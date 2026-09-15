import os
from app.production import cors_origins, validate_production

def test_cors_sem_wildcard(monkeypatch):
    monkeypatch.setenv("EXPORTAI_CORS_ORIGINS", "https://exportai-brazil.netlify.app")
    assert cors_origins() == ["https://exportai-brazil.netlify.app"]

def test_cors_rejeita_wildcard(monkeypatch):
    monkeypatch.setenv("EXPORTAI_CORS_ORIGINS", "*")
    try: cors_origins(); assert False
    except RuntimeError: pass

def test_producao_exige_postgres(monkeypatch):
    monkeypatch.setenv("EXPORTAI_AMBIENTE", "PRODUCAO")
    monkeypatch.setenv("EXPORTAI_DATABASE_URL", "sqlite:///x.db")
    try: validate_production(); assert False
    except RuntimeError as e: assert "PostgreSQL" in str(e)

def test_producao_rejeita_ollama(monkeypatch):
    monkeypatch.setenv("EXPORTAI_AMBIENTE", "PRODUCAO")
    monkeypatch.setenv("EXPORTAI_DATABASE_URL", "postgresql+psycopg://u:p@h/db")
    monkeypatch.setenv("EXPORTAI_HANDOFF_SECRET", "x" * 32)
    monkeypatch.setenv("EXPORTAI_DIAGNOSTICO_IA_PROVEDOR", "OLLAMA")
    try: validate_production(); assert False
    except RuntimeError as e: assert "OLLAMA" in str(e)
