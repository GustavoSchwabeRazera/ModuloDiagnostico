from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from diagnostico.inteligencia.schemas import CategoriaRequisito, EvidenciaMercado, ISO3, TipoFonte


class FonteSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FonteRegulatoria(FonteSchema):
    codigo: str = Field(pattern=r"^[A-Z0-9_]+$")
    nome: str = Field(min_length=3, max_length=300)
    tipo_fonte: TipoFonte
    escopo: Literal["GLOBAL", "UNIAO_EUROPEIA", "PAIS"]
    paises_iso3: list[ISO3]
    dominios_permitidos: list[str] = Field(min_length=1)
    url_inicial: HttpUrl
    categorias: list[CategoriaRequisito] = Field(min_length=1)
    prioridade: int = Field(ge=1, le=100)
    ativo: bool = True


class PoliticaFontes(FonteSchema):
    origem_exportacao: ISO3
    maximo_fontes_por_pais: int = Field(ge=1, le=20)
    maximo_evidencias_por_pais: int = Field(ge=1, le=100)
    maximo_caracteres_por_evidencia: int = Field(ge=100, le=50000)
    somente_https: bool
    seguir_subdominios: bool
    busca_livre_habilitada: Literal[False] = False
    observacao: str


class CatalogoFontes(FonteSchema):
    versao: str
    politica: PoliticaFontes
    fontes: list[FonteRegulatoria] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_unicidade(self):
        codigos = [f.codigo for f in self.fontes]
        if len(codigos) != len(set(codigos)):
            raise ValueError("Há códigos de fontes duplicados.")
        return self


class ConsultaDirecionada(FonteSchema):
    fonte_codigo: str
    pais_iso3: ISO3
    hs6: str = Field(pattern=r"^\d{6}$")
    descricao_produto: str = Field(min_length=3, max_length=1000)
    categorias: list[CategoriaRequisito] = Field(min_length=1)
    consulta_textual: str = Field(min_length=10, max_length=2000)
    dominio_restrito: str
    url_inicial: HttpUrl


class DocumentoRecuperado(FonteSchema):
    fonte_codigo: str
    url: HttpUrl
    titulo: str = Field(min_length=3, max_length=500)
    texto: str = Field(min_length=10, max_length=100000)
    consultado_em: date
    idioma: str | None = None


class ResultadoRecuperacao(FonteSchema):
    consultas: list[ConsultaDirecionada]
    evidencias: list[EvidenciaMercado]
    descartes: list[str]
    cache_chave: str
    criado_em: datetime
