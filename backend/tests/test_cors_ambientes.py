from app.production import cors_origins


def test_defaults_incluem_frontend_local(monkeypatch):
    monkeypatch.delenv("EXPORTAI_CORS_ORIGINS", raising=False)
    origins = cors_origins()
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins


def test_producao_pode_restringir_origens_por_variavel(monkeypatch):
    monkeypatch.setenv(
        "EXPORTAI_CORS_ORIGINS",
        "https://exportai-brazil.netlify.app,https://export-recommend-wiz.lovable.app",
    )
    origins = cors_origins()
    assert "http://localhost:5173" not in origins
    assert origins == [
        "https://exportai-brazil.netlify.app",
        "https://export-recommend-wiz.lovable.app",
    ]
