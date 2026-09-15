from datetime import date

from diagnostico.inteligencia.fontes import (
    carregar_catalogo,
    dominio_permitido,
    montar_consultas,
    selecionar_fontes,
    transformar_documentos,
)


def test_catalogo_valido_e_busca_livre_desativada():
    catalogo = carregar_catalogo()
    assert catalogo.versao == "1.0.0"
    assert catalogo.politica.busca_livre_habilitada is False
    assert len(catalogo.fontes) == 3


def test_europa_recebe_access2markets_primeiro():
    fontes = selecionar_fontes(carregar_catalogo(), "DEU")
    assert fontes[0].codigo == "EU_ACCESS2MARKETS"


def test_pais_fora_ue_recebe_fontes_globais():
    codigos = {f.codigo for f in selecionar_fontes(carregar_catalogo(), "CHN")}
    assert codigos == {"ITC_MARKET_ACCESS_MAP", "EPING_SPS_TBT"}


def test_consulta_e_ultradirecionada():
    consultas = montar_consultas(carregar_catalogo(), "DEU", "090111", "café não torrado")
    assert consultas
    assert all("site:" in c.consulta_textual for c in consultas)
    assert all("DEU" in c.consulta_textual for c in consultas)
    assert all("090111" in c.consulta_textual for c in consultas)


def test_dominio_exato_e_subdominio_sao_permitidos():
    assert dominio_permitido("https://trade.ec.europa.eu/x", ["europa.eu"])
    assert dominio_permitido("https://europa.eu/x", ["europa.eu"])
    assert not dominio_permitido("https://europa.eu.exemplo.com/x", ["europa.eu"])


def test_documento_autorizado_vira_evidencia():
    resultado = transformar_documentos(
        carregar_catalogo(), "DEU", "090111", "café não torrado", [{
            "fonte_codigo": "EU_ACCESS2MARKETS",
            "url": "https://trade.ec.europa.eu/access-to-markets/en/content/product-requirements-0",
            "titulo": "Product requirements",
            "texto": "Requisito regulatório oficial suficientemente detalhado para o produto consultado.",
            "consultado_em": date(2026, 9, 8),
            "idioma": "en",
        }]
    )
    assert len(resultado.evidencias) == 1
    assert resultado.evidencias[0].tipo_fonte == "OFICIAL"


def test_dominio_nao_autorizado_e_descartado():
    resultado = transformar_documentos(
        carregar_catalogo(), "DEU", "090111", "café", [{
            "fonte_codigo": "EU_ACCESS2MARKETS",
            "url": "https://example.com/regras",
            "titulo": "Página externa",
            "texto": "Texto longo que não deve ser aceito como evidência controlada.",
            "consultado_em": date(2026, 9, 8),
        }]
    )
    assert resultado.evidencias == []
    assert any("Domínio não autorizado" in x for x in resultado.descartes)


def test_conteudo_duplicado_e_removido():
    doc = {
        "fonte_codigo": "ITC_MARKET_ACCESS_MAP",
        "url": "https://www.intracen.org/resources/tools/market-access-map",
        "titulo": "Market Access Map",
        "texto": "Mesmo texto regulatório suficientemente longo para representar uma evidência.",
        "consultado_em": date(2026, 9, 8),
    }
    outro = dict(doc, url="https://www.intracen.org/resources/tools/market-access-map?x=1")
    resultado = transformar_documentos(carregar_catalogo(), "CHN", "090111", "café", [doc, outro])
    assert len(resultado.evidencias) == 1
    assert any("Conteúdo duplicado" in x for x in resultado.descartes)


def test_cache_chave_e_deterministica():
    catalogo = carregar_catalogo()
    a = transformar_documentos(catalogo, "DEU", "090111", "Café não torrado", [])
    b = transformar_documentos(catalogo, "DEU", "090111", "  café   não torrado ", [])
    assert a.cache_chave == b.cache_chave
