import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from diagnostico.repositorio_memoria import repositorio_diagnosticos

client = TestClient(app)
BASE = Path(__file__).resolve().parents[1] / "diagnostico"


@pytest.fixture(autouse=True)
def limpar_repositorio():
    repositorio_diagnosticos.limpar()
    yield
    repositorio_diagnosticos.limpar()


def entrada():
    return json.loads((BASE / "exemplos" / "entrada_modulo_basico.json").read_text(encoding="utf-8"))


def respostas(status="CONCLUIDO"):
    catalogo = client.get("/api/v1/diagnosticos/checklist").json()
    return {
        "catalogo_versao": catalogo["versao"],
        "respostas": [
            {"item_codigo": item["codigo"], "status": status}
            for item in catalogo["itens"]
        ],
    }


def criar():
    resposta = client.post("/api/v1/diagnosticos", json=entrada())
    assert resposta.status_code == 201
    return resposta.json()["diagnostico_id"]


def test_checklist_retorna_26_itens():
    resposta = client.get("/api/v1/diagnosticos/checklist")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["versao"] == "1.0.0"
    assert len(corpo["dimensoes"]) == 6
    assert len(corpo["itens"]) == 26


def test_cria_e_consulta_sessao():
    identificador = criar()
    resposta = client.get(f"/api/v1/diagnosticos/{identificador}")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "CRIADO"
    assert corpo["mercados_escolhidos"] == ["CHN", "DEU", "ITA"]
    assert corpo["resultado"] is None


def test_sessao_inexistente_retorna_404():
    resposta = client.get("/api/v1/diagnosticos/00000000-0000-0000-0000-000000000000")
    assert resposta.status_code == 404


def test_atualiza_mercados():
    identificador = criar()
    resposta = client.put(
        f"/api/v1/diagnosticos/{identificador}/mercados",
        json={"mercados_escolhidos": ["DEU"]},
    )
    assert resposta.status_code == 200
    assert resposta.json()["mercados_escolhidos"] == ["DEU"]


def test_rejeita_mercado_fora_do_basico():
    identificador = criar()
    resposta = client.put(
        f"/api/v1/diagnosticos/{identificador}/mercados",
        json={"mercados_escolhidos": ["USA"]},
    )
    assert resposta.status_code == 400


def test_registra_respostas_parciais_e_atualiza_item():
    identificador = criar()
    parcial = {
        "catalogo_versao": "1.0.0",
        "respostas": [{"item_codigo": "PROD_CAPACIDADE_01", "status": "NAO_INICIADO"}],
    }
    resposta = client.put(f"/api/v1/diagnosticos/{identificador}/respostas", json=parcial)
    assert resposta.status_code == 200
    assert resposta.json()["respostas_registradas"] == 1
    assert resposta.json()["status"] == "EM_PREENCHIMENTO"

    parcial["respostas"][0]["status"] = "CONCLUIDO"
    client.put(f"/api/v1/diagnosticos/{identificador}/respostas", json=parcial)
    sessao = client.get(f"/api/v1/diagnosticos/{identificador}").json()
    assert len(sessao["respostas"]) == 1
    assert sessao["respostas"][0]["status"] == "CONCLUIDO"


def test_calculo_incompleto_retorna_409():
    identificador = criar()
    client.put(
        f"/api/v1/diagnosticos/{identificador}/respostas",
        json={
            "catalogo_versao": "1.0.0",
            "respostas": [{"item_codigo": "PROD_CAPACIDADE_01", "status": "CONCLUIDO"}],
        },
    )
    resposta = client.post(f"/api/v1/diagnosticos/{identificador}/calcular")
    assert resposta.status_code == 409


def test_fluxo_completo_calcula_e_consulta_resultado():
    identificador = criar()
    registro = client.put(
        f"/api/v1/diagnosticos/{identificador}/respostas",
        json=respostas("CONCLUIDO"),
    )
    assert registro.status_code == 200
    assert registro.json()["status"] == "PRONTO_PARA_CALCULAR"

    calculo = client.post(f"/api/v1/diagnosticos/{identificador}/calcular")
    assert calculo.status_code == 200
    corpo = calculo.json()
    assert corpo["score_geral"] == 100
    assert corpo["nivel"] == "PRONTA_PARA_PROSPECTAR"
    assert corpo["bloqueia_modulo_vendas"] is False
    assert len(corpo["pesquisas_mercado"]) == 3

    consulta = client.get(f"/api/v1/diagnosticos/{identificador}/resultado")
    assert consulta.status_code == 200
    assert consulta.json() == corpo


def test_resultado_antes_do_calculo_retorna_409():
    identificador = criar()
    resposta = client.get(f"/api/v1/diagnosticos/{identificador}/resultado")
    assert resposta.status_code == 409


def test_alterar_resposta_invalida_resultado():
    identificador = criar()
    client.put(f"/api/v1/diagnosticos/{identificador}/respostas", json=respostas())
    client.post(f"/api/v1/diagnosticos/{identificador}/calcular")

    atualizacao = client.put(
        f"/api/v1/diagnosticos/{identificador}/respostas",
        json={
            "catalogo_versao": "1.0.0",
            "respostas": [{"item_codigo": "CONF_DESTINO_04", "status": "NAO_SEI"}],
        },
    )
    assert atualizacao.status_code == 200
    assert atualizacao.json()["resultado_invalidado"] is True
    assert client.get(f"/api/v1/diagnosticos/{identificador}/resultado").status_code == 409


def test_alterar_mercado_invalida_resultado():
    identificador = criar()
    client.put(f"/api/v1/diagnosticos/{identificador}/respostas", json=respostas())
    client.post(f"/api/v1/diagnosticos/{identificador}/calcular")

    atualizacao = client.put(
        f"/api/v1/diagnosticos/{identificador}/mercados",
        json={"mercados_escolhidos": ["CHN"]},
    )
    assert atualizacao.status_code == 200
    assert atualizacao.json()["resultado_invalidado"] is True
    assert client.get(f"/api/v1/diagnosticos/{identificador}/resultado").status_code == 409


def test_openapi_documenta_rotas_diagnostico():
    esquema = client.get("/openapi.json").json()
    caminhos = esquema["paths"]
    assert "/api/v1/diagnosticos/checklist" in caminhos
    assert "/api/v1/diagnosticos" in caminhos
    assert "/api/v1/diagnosticos/{diagnostico_id}/calcular" in caminhos
