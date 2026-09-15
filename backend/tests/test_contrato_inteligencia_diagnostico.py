from datetime import date

import pytest
from pydantic import ValidationError

from diagnostico.inteligencia.fabrica import criar_provedor
from diagnostico.inteligencia.provedor_desativado import ProvedorInteligenciaDesativado
from diagnostico.inteligencia.schemas import EntradaInteligenciaMercado, SaidaInteligenciaMercado


def entrada(evidencias=None):
    return EntradaInteligenciaMercado(
        produto={"ncm": "09011110", "hs6": "090111", "descricao": "Café não torrado"},
        pais={"iso3": "DEU", "nome": "Alemanha"},
        evidencias=evidencias or [],
    )


def evidencia(identificador="fonte-001"):
    return {
        "evidencia_id": identificador,
        "fonte_titulo": "Portal oficial",
        "fonte_url": "https://example.gov/requisitos",
        "tipo_fonte": "OFICIAL",
        "consultado_em": date(2026, 9, 8),
        "trecho": "Trecho oficial suficientemente longo para validação.",
        "idioma": "pt-BR",
    }


def test_entrada_valida_um_pais():
    modelo = entrada([evidencia()])
    assert modelo.pais.iso3 == "DEU"
    assert len(modelo.evidencias) == 1


def test_entrada_sem_evidencias_e_valida():
    assert entrada().evidencias == []


def test_iso3_invalido_e_rejeitado():
    with pytest.raises(ValidationError):
        EntradaInteligenciaMercado(
            produto={"ncm": "09011110", "hs6": "090111", "descricao": "Café"},
            pais={"iso3": "DE", "nome": "Alemanha"},
            evidencias=[],
        )


def test_evidencia_sem_url_e_rejeitada():
    dados = evidencia()
    dados.pop("fonte_url")
    with pytest.raises(ValidationError):
        entrada([dados])


def test_evidencias_duplicadas_sao_rejeitadas():
    with pytest.raises(ValidationError, match="não podem se repetir"):
        entrada([evidencia(), evidencia()])


def test_requisito_precisa_referenciar_evidencia_existente():
    with pytest.raises(ValidationError, match="evidências inexistentes"):
        SaidaInteligenciaMercado(
            pais_iso3="DEU",
            status="CONCLUIDA",
            resumo="Análise concluída com evidências.",
            requisitos=[{
                "categoria": "ROTULAGEM",
                "titulo": "Regra de rotulagem",
                "descricao": "Descrição suficientemente longa da regra encontrada.",
                "obrigatoriedade": "NAO_DETERMINADO",
                "status_evidencia": "NAO_CONFIRMADO",
                "aplicabilidade": "NAO_DETERMINADA",
                "fontes_ids": ["inexistente"],
            }],
            evidencias_disponiveis=["fonte-001"],
        )


def test_provedor_desativado_retorna_indisponivel():
    saida = ProvedorInteligenciaDesativado().analisar(entrada([evidencia()]))
    assert saida.status == "INDISPONIVEL"
    assert saida.requisitos == []
    assert saida.pais_iso3 == "DEU"
    assert saida.evidencias_disponiveis == ["fonte-001"]


def test_fabrica_usa_desativado_por_padrao(monkeypatch):
    monkeypatch.delenv("EXPORTAI_DIAGNOSTICO_IA_PROVEDOR", raising=False)
    assert criar_provedor().nome == "DESATIVADO"


def test_provedor_desconhecido_falha_de_forma_segura():
    with pytest.warns(RuntimeWarning, match="usando DESATIVADO"):
        provedor = criar_provedor("OUTRA_IA")
    assert provedor.nome == "DESATIVADO"


def test_saida_nao_possui_campos_de_pontuacao():
    campos = SaidaInteligenciaMercado.model_fields
    proibidos = {"score_geral", "nivel", "peso", "bloqueia_modulo_vendas"}
    assert proibidos.isdisjoint(campos)


def test_indisponivel_nao_pode_conter_requisitos():
    with pytest.raises(ValidationError, match="não pode conter requisitos"):
        SaidaInteligenciaMercado(
            pais_iso3="DEU",
            status="INDISPONIVEL",
            resumo="Pesquisa indisponível.",
            requisitos=[{
                "categoria": "OUTROS",
                "titulo": "Requisito inválido",
                "descricao": "Este requisito não poderia estar nesta saída.",
                "obrigatoriedade": "NAO_DETERMINADO",
                "status_evidencia": "NAO_CONFIRMADO",
                "aplicabilidade": "NAO_DETERMINADA",
                "fontes_ids": ["fonte-001"],
            }],
            evidencias_disponiveis=["fonte-001"],
        )
