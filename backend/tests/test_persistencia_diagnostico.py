from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from diagnostico.repositorio_sqlite import RepositorioDiagnosticosSQLite


def engine_memoria():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )


def sessao_exemplo(identificador="11111111-1111-4111-8111-111111111111"):
    instante = datetime.now(timezone.utc)
    return {
        "diagnostico_id": identificador,
        "status": "CRIADO",
        "catalogo_versao": "1.0.0",
        "produto": {"ncm": "09011110", "hs6": "090111", "descricao": "Café"},
        "mercados_basico": [{"iso3": "DEU", "nome": "Alemanha"}],
        "mercados_escolhidos": ["DEU"],
        "respostas": [],
        "resultado": None,
        "criado_em": instante,
        "atualizado_em": instante,
    }


def test_cria_banco_e_persiste_sessao():
    repo = RepositorioDiagnosticosSQLite(engine_memoria())
    original = sessao_exemplo()
    repo.criar(original)
    recuperada = repo.obter(original["diagnostico_id"])
    assert recuperada["produto"] == original["produto"]
    assert recuperada["mercados_escolhidos"] == ["DEU"]
    assert repo.contar() == 1


def test_duas_instancias_acessam_mesma_sessao():
    engine = engine_memoria()
    repo_a = RepositorioDiagnosticosSQLite(engine)
    repo_b = RepositorioDiagnosticosSQLite(engine)
    original = sessao_exemplo()
    repo_a.criar(original)
    assert repo_b.obter(original["diagnostico_id"])["status"] == "CRIADO"


def test_salvar_atualiza_respostas_e_resultado():
    repo = RepositorioDiagnosticosSQLite(engine_memoria())
    original = sessao_exemplo()
    repo.criar(original)
    original["status"] = "CALCULADO"
    original["respostas"] = [{"item_codigo": "PROD_CAPACIDADE_01", "status": "CONCLUIDO", "observacao": None}]
    original["resultado"] = {"score_geral": 100, "bloqueia_modulo_vendas": False}
    original["atualizado_em"] = datetime.now(timezone.utc)
    repo.salvar(original["diagnostico_id"], original)
    recuperada = repo.obter(original["diagnostico_id"])
    assert recuperada["status"] == "CALCULADO"
    assert recuperada["respostas"][0]["status"] == "CONCLUIDO"
    assert recuperada["resultado"]["score_geral"] == 100


def test_obter_inexistente_retorna_none():
    repo = RepositorioDiagnosticosSQLite(engine_memoria())
    assert repo.obter("inexistente") is None


def test_salvar_inexistente_gera_keyerror():
    repo = RepositorioDiagnosticosSQLite(engine_memoria())
    try:
        repo.salvar("inexistente", sessao_exemplo())
    except KeyError as erro:
        assert erro.args[0] == "inexistente"
    else:
        raise AssertionError("KeyError esperado")


def test_limpar_remove_registros():
    repo = RepositorioDiagnosticosSQLite(engine_memoria())
    repo.criar(sessao_exemplo())
    repo.limpar()
    assert repo.contar() == 0
