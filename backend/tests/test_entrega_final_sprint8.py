import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def test_artefatos_finais_presentes():
    required = [
        "Dockerfile", "start.sh", ".dockerignore", "Procfile",
        "docs/openapi-exportai.json", "docs/DEPLOY_NUVEM.md",
        "docs/LOVABLE_DIAGNOSTICO_HANDOFF.md",
        "docs/TESTE_PONTA_A_PONTA.md",
        "docs/CHECKLIST_ENTREGA_COLEGA.md",
        "MANIFESTO_SPRINT8_FINAL.json",
    ]
    for name in required:
        assert (BACKEND / name).exists(), name


def test_openapi_e_json_e_contem_jornadas():
    data = json.loads((BACKEND / "docs/openapi-exportai.json").read_text(encoding="utf-8"))
    assert "/api/v1/jornadas" in data["paths"]
    assert "/api/v1/jornadas/{journey_id}" in data["paths"]


def test_manifesto_nao_contem_valores_de_segredos():
    text = (BACKEND / "MANIFESTO_SPRINT8_FINAL.json").read_text(encoding="utf-8")
    assert "GEMINI_API_KEY=" not in text
    assert "GROQ_API_KEY=" not in text
    assert "postgresql+psycopg://usuario:senha" not in text.lower()
