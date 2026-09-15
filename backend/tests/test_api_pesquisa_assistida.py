from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from diagnostico.repositorio_sqlite import RepositorioDiagnosticosSQLite


def engine_memoria():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )


def sessao():
    agora = datetime.now(timezone.utc)
    return {
        "diagnostico_id": "11111111-1111-4111-8111-111111111111",
        "status": "CALCULADO",
        "catalogo_versao": "1.0.0",
        "produto": {"ncm": "09011110", "hs6": "090111", "descricao": "Café"},
        "mercados_basico": [{"iso3": "DEU", "nome": "Alemanha"}],
        "mercados_escolhidos": ["DEU"],
        "respostas": [],
        "resultado": {"score_geral": 72.5, "nivel": "QUASE_PRONTA"},
        "pesquisa_assistida": None,
        "criado_em": agora,
        "atualizado_em": agora,
    }


def test_coluna_pesquisa_e_criada():
    engine = engine_memoria()
    RepositorioDiagnosticosSQLite(engine)
    colunas = {c["name"] for c in inspect(engine).get_columns("diagnosticos")}
    assert "pesquisa_assistida_json" in colunas


def test_pesquisa_assistida_e_persistida_sem_alterar_score():
    repo = RepositorioDiagnosticosSQLite(engine_memoria())
    dados = sessao()
    repo.criar(dados)
    dados["pesquisa_assistida"] = {
        "diagnostico_id": dados["diagnostico_id"],
        "provedor": "DESATIVADO",
        "paises_solicitados": 1,
        "paises_concluidos": 0,
        "paises_com_erro": 0,
        "resultados": [],
        "pontuacao_preservada": True,
    }
    repo.salvar(dados["diagnostico_id"], dados)
    recuperada = repo.obter(dados["diagnostico_id"])
    assert recuperada["pesquisa_assistida"]["provedor"] == "DESATIVADO"
    assert recuperada["resultado"]["score_geral"] == 72.5


def test_ausencia_de_pesquisa_nao_altera_diagnostico():
    repo = RepositorioDiagnosticosSQLite(engine_memoria())
    dados = sessao()
    repo.criar(dados)
    recuperada = repo.obter(dados["diagnostico_id"])
    assert recuperada["pesquisa_assistida"] is None
    assert recuperada["resultado"]["score_geral"] == 72.5
    assert recuperada["resultado"]["nivel"] == "QUASE_PRONTA"


def test_openapi_contem_endpoints_pesquisa():
    from app.main import app
    caminhos = app.openapi()["paths"]
    caminho = "/api/v1/diagnosticos/{diagnostico_id}/pesquisa-assistida"
    assert caminho in caminhos
    assert "post" in caminhos[caminho]
    assert "get" in caminhos[caminho]
