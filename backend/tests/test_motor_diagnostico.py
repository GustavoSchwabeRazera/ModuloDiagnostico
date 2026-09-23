import json
from pathlib import Path

import pytest

from diagnostico.motor import (
    CatalogoIncompativelError,
    ErroDiagnostico,
    MotorDiagnostico,
    RespostasIncompletasError,
)

BASE = Path(__file__).resolve().parents[1] / "diagnostico"


def catalogo():
    return json.loads((BASE / "data" / "catalogo_checklist_v1.json").read_text(encoding="utf-8"))


def payload(status="CONCLUIDO"):
    itens = catalogo()["itens"]
    return {
        "catalogo_versao": "1.0.0",
        "respostas": [
            {"item_codigo": item["codigo"], "status": status}
            for item in itens
        ],
    }


def substituir_status(dados, codigo, status, observacao=None):
    for resposta in dados["respostas"]:
        if resposta["item_codigo"] == codigo:
            resposta["status"] = status
            if observacao is not None:
                resposta["observacao"] = observacao
            return
    raise AssertionError(codigo)


def test_tudo_concluido_resulta_em_cem():
    resultado = MotorDiagnostico().calcular(payload(), ["CHN", "DEU"])
    assert resultado.score_geral == 100
    assert resultado.nivel == "PRONTA_PARA_PROSPECTAR"
    assert resultado.possui_bloqueadores is False
    assert resultado.plano_acao == []
    assert resultado.bloqueia_modulo_vendas is False
    assert [x.pais_iso3 for x in resultado.pesquisas_mercado] == ["CHN", "DEU"]


def test_tudo_nao_iniciado_resulta_em_zero():
    resultado = MotorDiagnostico().calcular(payload("NAO_INICIADO"), ["ITA"])
    assert resultado.score_geral == 0
    assert resultado.nivel == "INICIAL"
    assert resultado.possui_bloqueadores is True
    assert resultado.plano_acao
    assert resultado.alerta_vendas
    assert resultado.bloqueia_modulo_vendas is False


def test_em_andamento_resulta_em_cinquenta():
    resultado = MotorDiagnostico().calcular(payload("EM_ANDAMENTO"))
    assert resultado.score_geral == 50
    assert resultado.nivel == "EM_PREPARACAO"


def test_nao_se_aplica_legado_e_normalizado_para_nao_sei():
    dados = payload()
    substituir_status(dados, "OPER_SEGURO_04", "NAO_SE_APLICA", "Seguro dispensado neste cenário.")
    resultado = MotorDiagnostico().calcular(dados)
    assert resultado.score_geral < 100
    assert any(x.item_codigo == "OPER_SEGURO_04" for x in resultado.plano_acao)


def test_bloqueador_pendente_gera_alerta_sem_bloquear_vendas():
    dados = payload()
    substituir_status(dados, "CONF_DESTINO_04", "NAO_SEI")
    resultado = MotorDiagnostico().calcular(dados)
    assert resultado.possui_bloqueadores is True
    assert resultado.bloqueadores[0].codigo == "CONF_DESTINO_04"
    assert resultado.alerta_vendas is not None
    assert resultado.bloqueia_modulo_vendas is False


def test_plano_prioriza_bloqueador_antes_de_essencial():
    dados = payload()
    substituir_status(dados, "MKT_CATALOGO_02", "NAO_INICIADO")
    substituir_status(dados, "CONF_DESTINO_04", "NAO_SEI")
    resultado = MotorDiagnostico().calcular(dados)
    assert resultado.plano_acao[0].item_codigo == "CONF_DESTINO_04"
    assert resultado.plano_acao[0].criticidade == "BLOQUEADOR"


def test_score_por_dimensao_e_calculado():
    dados = payload()
    substituir_status(dados, "PROD_CAPACIDADE_01", "NAO_INICIADO")
    resultado = MotorDiagnostico().calcular(dados)
    por_dimensao = {x.dimensao: x for x in resultado.scores_dimensoes}
    assert len(por_dimensao) == 6
    assert por_dimensao["PRODUCAO_GESTAO"].score < 100
    assert por_dimensao["MARKETING_COMERCIAL"].score == 100


def test_resposta_desconhecida_e_rejeitada():
    dados = payload()
    dados["respostas"][0]["item_codigo"] = "ITEM_INEXISTENTE"
    with pytest.raises(CatalogoIncompativelError, match="não encontrados"):
        MotorDiagnostico().calcular(dados)


def test_respostas_faltantes_sao_rejeitadas():
    dados = payload()
    dados["respostas"].pop()
    with pytest.raises(RespostasIncompletasError, match="Faltam respostas"):
        MotorDiagnostico().calcular(dados)


def test_versao_incorreta_e_rejeitada():
    dados = payload()
    dados["catalogo_versao"] = "9.9.9"
    with pytest.raises(CatalogoIncompativelError, match="Versão recebida"):
        MotorDiagnostico().calcular(dados)


def test_quatro_paises_sao_rejeitados():
    with pytest.raises(ErroDiagnostico, match="máximo três"):
        MotorDiagnostico().calcular(payload(), ["CHN", "DEU", "ITA", "JPN"])


def test_paises_repetidos_sao_rejeitados():
    with pytest.raises(ErroDiagnostico, match="não podem se repetir"):
        MotorDiagnostico().calcular(payload(), ["CHN", "CHN"])


def test_ordens_do_plano_sao_continuas():
    resultado = MotorDiagnostico().calcular(payload("NAO_INICIADO"))
    assert [x.ordem for x in resultado.plano_acao] == list(
        range(1, len(resultado.plano_acao) + 1)
    )
