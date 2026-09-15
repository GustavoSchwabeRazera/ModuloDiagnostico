from __future__ import annotations

from sqlalchemy import text

from diagnostico.database import criar_engine, obter_database_url


def test_sqlite_continua_disponivel_para_testes(monkeypatch):
    monkeypatch.setenv("EXPORTAI_DATABASE_URL", "sqlite:///:memory:")
    assert obter_database_url() == "sqlite:///:memory:"
    engine = criar_engine(obter_database_url())
    with engine.connect() as conn:
        assert conn.execute(text("select 1")).scalar_one() == 1


def test_url_postgres_antiga_e_normalizada(monkeypatch):
    monkeypatch.setenv("EXPORTAI_DATABASE_URL", "postgres://u:s@host:5432/db")
    assert obter_database_url() == "postgresql+psycopg://u:s@host:5432/db"


def test_url_postgresql_e_normalizada_para_psycopg(monkeypatch):
    monkeypatch.setenv("EXPORTAI_DATABASE_URL", "postgresql://u:s@host:5432/db")
    assert obter_database_url() == "postgresql+psycopg://u:s@host:5432/db"


def test_migracoes_e_configuracao_presentes():
    from pathlib import Path
    backend = Path(__file__).resolve().parents[1]
    assert (backend / "alembic.ini").exists()
    assert (backend / "migrations" / "env.py").exists()
    assert (backend / "migrations" / "versions" / "20260911_01_baseline_diagnosticos.py").exists()


def test_env_exemplo_nao_contem_senha_real():
    from pathlib import Path
    texto = (Path(__file__).resolve().parents[1] / ".env.example").read_text(encoding="utf-8")
    assert "EXPORTAI_DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/exportai" in texto
