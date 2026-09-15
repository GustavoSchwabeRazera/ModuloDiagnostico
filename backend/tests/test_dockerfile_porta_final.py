from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def test_dockerfile_documenta_host_e_porta_do_runtime():
    content = (BACKEND / "Dockerfile").read_text(encoding="utf-8")
    assert "USER exportai" in content
    assert "HEALTHCHECK" in content
    assert "--host 0.0.0.0" in content
    assert "--port ${PORT}" in content
    assert 'CMD ["/app/start.sh"]' in content


def test_start_sh_aplica_porta_configuravel():
    content = (BACKEND / "start.sh").read_text(encoding="utf-8")
    assert '--port "${PORT:-8000}"' in content
