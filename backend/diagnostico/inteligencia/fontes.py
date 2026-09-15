from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from diagnostico.inteligencia.fontes_schemas import (
    CatalogoFontes,
    ConsultaDirecionada,
    DocumentoRecuperado,
    ResultadoRecuperacao,
)
from diagnostico.inteligencia.schemas import EvidenciaMercado

CATALOGO_PADRAO = Path(__file__).resolve().parents[1] / "data" / "catalogo_fontes_regulatorias_v1.json"


class ErroFonte(ValueError):
    pass


def carregar_catalogo(caminho: Path = CATALOGO_PADRAO) -> CatalogoFontes:
    return CatalogoFontes.model_validate_json(caminho.read_text(encoding="utf-8"))


def dominio_permitido(url: str, dominios: list[str], seguir_subdominios: bool = True) -> bool:
    host = (urlparse(url).hostname or "").lower().rstrip(".")
    for dominio in dominios:
        base = dominio.lower().rstrip(".")
        if host == base or (seguir_subdominios and host.endswith("." + base)):
            return True
    return False


def normalizar_texto(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def selecionar_fontes(catalogo: CatalogoFontes, pais_iso3: str):
    pais = pais_iso3.upper()
    candidatas = [
        fonte for fonte in catalogo.fontes
        if fonte.ativo and (fonte.escopo == "GLOBAL" or pais in fonte.paises_iso3)
    ]
    return sorted(candidatas, key=lambda f: (f.prioridade, f.codigo))[
        : catalogo.politica.maximo_fontes_por_pais
    ]


def montar_consultas(catalogo: CatalogoFontes, pais_iso3: str, hs6: str, descricao: str):
    consultas = []
    for fonte in selecionar_fontes(catalogo, pais_iso3):
        for dominio in fonte.dominios_permitidos:
            categorias = " ".join(c.lower() for c in fonte.categorias)
            texto = f"site:{dominio} {pais_iso3.upper()} HS {hs6} {descricao} {categorias}"
            consultas.append(ConsultaDirecionada(
                fonte_codigo=fonte.codigo,
                pais_iso3=pais_iso3,
                hs6=hs6,
                descricao_produto=descricao,
                categorias=fonte.categorias,
                consulta_textual=texto,
                dominio_restrito=dominio,
                url_inicial=fonte.url_inicial,
            ))
    return consultas


def transformar_documentos(
    catalogo: CatalogoFontes,
    pais_iso3: str,
    hs6: str,
    descricao: str,
    documentos: list[DocumentoRecuperado | dict],
) -> ResultadoRecuperacao:
    fontes = {fonte.codigo: fonte for fonte in catalogo.fontes}
    evidencias = []
    descartes = []
    hashes = set()

    for bruto in documentos:
        doc = bruto if isinstance(bruto, DocumentoRecuperado) else DocumentoRecuperado.model_validate(bruto)
        fonte = fontes.get(doc.fonte_codigo)
        if fonte is None or not fonte.ativo:
            descartes.append(f"Fonte não autorizada: {doc.fonte_codigo}")
            continue
        if catalogo.politica.somente_https and urlparse(str(doc.url)).scheme != "https":
            descartes.append(f"URL não HTTPS: {doc.url}")
            continue
        if not dominio_permitido(str(doc.url), fonte.dominios_permitidos, catalogo.politica.seguir_subdominios):
            descartes.append(f"Domínio não autorizado: {doc.url}")
            continue
        trecho = normalizar_texto(doc.texto)[:catalogo.politica.maximo_caracteres_por_evidencia]
        digest = hashlib.sha256(trecho.casefold().encode("utf-8")).hexdigest()
        if digest in hashes:
            descartes.append(f"Conteúdo duplicado: {doc.url}")
            continue
        hashes.add(digest)
        evidencia_id = f"{doc.fonte_codigo.lower()}-{digest[:12]}"
        evidencias.append(EvidenciaMercado(
            evidencia_id=evidencia_id,
            fonte_titulo=doc.titulo,
            fonte_url=doc.url,
            tipo_fonte=fonte.tipo_fonte,
            consultado_em=doc.consultado_em,
            trecho=trecho,
            idioma=doc.idioma,
        ))
        if len(evidencias) >= catalogo.politica.maximo_evidencias_por_pais:
            break

    chave_material = json.dumps({
        "v": catalogo.versao,
        "pais": pais_iso3.upper(),
        "hs6": hs6,
        "descricao": normalizar_texto(descricao).casefold(),
    }, ensure_ascii=False, sort_keys=True)
    chave = hashlib.sha256(chave_material.encode("utf-8")).hexdigest()
    return ResultadoRecuperacao(
        consultas=montar_consultas(catalogo, pais_iso3, hs6, descricao),
        evidencias=evidencias,
        descartes=descartes,
        cache_chave=chave,
        criado_em=datetime.now(timezone.utc),
    )
