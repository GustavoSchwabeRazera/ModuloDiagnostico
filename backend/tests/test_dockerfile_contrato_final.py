from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def test_dockerfile_declara_host_e_usuario():
    content = (BACKEND / "Dockerfile").read_text(encoding="utf-8")
    assert "USER exportai" in content
    assert "HEALTHCHECK" in content
    assert "--host 0.0.0.0" in content
    assert 'CMD ["/app/start.sh"]' in content


def test_start_sh_executa_uvicorn_no_host_publico():
    content = (BACKEND / "start.sh").read_text(encoding="utf-8")
    assert "python -m alembic upgrade head" in content
    assert "python -m uvicorn app.main:app" in content
    assert "--host 0.0.0.0" in content
