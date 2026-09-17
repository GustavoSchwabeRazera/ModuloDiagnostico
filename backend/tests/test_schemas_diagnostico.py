import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from diagnostico.schemas import (
    CatalogoChecklist,
    CriarDiagnosticoRequest,
    EntradaModuloBasico,
    RegistrarRespostasRequest,
    RespostaChecklist,
    ResultadoDiagnostico,
)

BASE = Path(__file__).resolve().parents[1] / "diagnostico"


def ler_json(caminho):
    return json.loads(caminho.read_text(encoding="utf-8"))


def entrada_exemplo():
    return ler_json(BASE / "exemplos" / "entrada_modulo_basico.json")


def test_catalogo_json_valida_no_schema():
    dados = ler_json(BASE / "data" / "catalogo_checklist_v1.json")
    catalogo = CatalogoChecklist.model_validate(dados)
    assert catalogo.versao == "1.0.0"
    assert len(catalogo.dimensoes) == 6
    assert len(catalogo.itens) == 26


def test_entrada_modulo_basico_valida():
    dados = entrada_exemplo()
    entrada = EntradaModuloBasico.model_validate({
        "produto": dados["produto"],
        "mercados_basico": dados["mercados_basico"],
    })
    assert entrada.produto.ncm == "09011110"
    assert entrada.produto.hs6 == "090111"
    assert len(entrada.mercados_basico) == 3


def test_ncm_pontuada_e_normalizada():
    dados = entrada_exemplo()
    dados["produto"]["ncm"] = "09.01.11.10"
    entrada = CriarDiagnosticoRequest.model_validate(dados)
    assert entrada.produto.ncm == "09011110"


def test_hs6_sem_ncm_e_aceito():
    dados = entrada_exemplo()
    dados["produto"].pop("ncm")
    entrada = CriarDiagnosticoRequest.model_validate(dados)
    assert entrada.produto.ncm is None
    assert entrada.produto.hs6 == "090111"


def test_hs6_incompativel_com_ncm_rejeitado():
    dados = entrada_exemplo()
    dados["produto"]["hs6"] = "850440"
    with pytest.raises(ValidationError, match="seis primeiros"):
        CriarDiagnosticoRequest.model_validate(dados)


def test_aceita_ate_tres_paises():
    entrada = CriarDiagnosticoRequest.model_validate(entrada_exemplo())
    assert entrada.mercados_escolhidos == ["CHN", "DEU", "ITA"]


def test_rejeita_quatro_paises():
    dados = entrada_exemplo()
    quarto = dict(dados["mercados_basico"][-1])
    quarto.update({
        "iso3": "JPN",
        "nome": "Japão",
        "ranking_personalizado": 4,
        "ranking_global_no_hs6": 7,
        "score_exportai": 53.86,
    })
    dados["mercados_basico"].append(quarto)
    dados["mercados_escolhidos"].append("JPN")
    with pytest.raises(ValidationError):
        CriarDiagnosticoRequest.model_validate(dados)


def test_rejeita_pais_que_nao_veio_do_basico():
    dados = entrada_exemplo()
    dados["mercados_escolhidos"] = ["USA"]
    with pytest.raises(ValidationError, match="resultado do Módulo Básico"):
        CriarDiagnosticoRequest.model_validate(dados)


def test_rejeita_iso3_duplicado_no_basico():
    dados = entrada_exemplo()
    dados["mercados_basico"][1]["iso3"] = "CHN"
    with pytest.raises(ValidationError, match="repetir ISO3"):
        CriarDiagnosticoRequest.model_validate(dados)


def test_rejeita_ranking_com_lacuna():
    dados = entrada_exemplo()
    dados["mercados_basico"][2]["ranking_personalizado"] = 4
    with pytest.raises(ValidationError, match="não possuir lacunas"):
        CriarDiagnosticoRequest.model_validate(dados)


def test_nao_se_aplica_exige_justificativa():
    with pytest.raises(ValidationError, match="justificativa"):
        RespostaChecklist(item_codigo="OPER_SEGURO_04", status="NAO_SE_APLICA")


def test_respostas_nao_podem_repetir_item():
    with pytest.raises(ValidationError, match="apenas uma resposta"):
        RegistrarRespostasRequest(
            catalogo_versao="1.0.0",
            respostas=[
                {"item_codigo": "PROD_CAPACIDADE_01", "status": "CONCLUIDO"},
                {"item_codigo": "PROD_CAPACIDADE_01", "status": "EM_ANDAMENTO"},
            ],
        )


def test_resultado_nunca_bloqueia_modulo_vendas():
    resultado = ResultadoDiagnostico(
        catalogo_versao="1.0.0",
        score_geral=80,
        nivel="QUASE_PRONTA",
        scores_dimensoes=[],
        possui_bloqueadores=True,
        bloqueadores=[{
            "codigo": "CONF_DESTINO_04",
            "status": "NAO_SEI",
            "mensagem": "Exigências ainda não confirmadas.",
        }],
        plano_acao=[],
        pesquisas_mercado=[],
        alerta_vendas="Há pendências importantes.",
        bloqueia_modulo_vendas=False,
    )
    assert resultado.bloqueia_modulo_vendas is False


def test_resultado_bloqueadores_precisa_ser_coerente():
    with pytest.raises(ValidationError, match="refletir"):
        ResultadoDiagnostico(
            catalogo_versao="1.0.0",
            score_geral=100,
            nivel="PRONTA_PARA_PROSPECTAR",
            scores_dimensoes=[],
            possui_bloqueadores=False,
            bloqueadores=[{
                "codigo": "CONF_DESTINO_04",
                "status": "NAO_SEI",
                "mensagem": "Pendente.",
            }],
            plano_acao=[],
            pesquisas_mercado=[],
        )
