import json
from pathlib import Path

from app.main import app

BACKEND = Path(__file__).resolve().parents[1]


def test_manifesto_sprint8_valido():
    dados = json.loads((BACKEND / "MANIFESTO_SPRINT8.json").read_text(encoding="utf-8"))
    assert dados["sprint"] == 8
    assert dados["status"] == "CONCLUIDA"
    assert dados["arquitetura"]["diagnostico_principal"] == "DETERMINISTICO"
    assert dados["arquitetura"]["pesquisa_regulatoria"] == "COMPLEMENTAR_E_OPCIONAL"


def test_arquivos_fundamentais_presentes():
    dados = json.loads((BACKEND / "MANIFESTO_SPRINT8.json").read_text(encoding="utf-8"))
    ausentes = [nome for nome in dados["arquivos_fundamentais"] if not (BACKEND / nome).exists()]
    assert ausentes == []


def test_documentacao_foi_gerada():
    esperados = [
        "SPRINT8_MODULO_DIAGNOSTICO.md",
        "API_DIAGNOSTICO.md",
        "CONFIGURACAO_COMPLEMENTAR.md",
        "CHECKLIST_DEMONSTRACAO.md",
    ]
    assert all((BACKEND / "docs" / nome).exists() for nome in esperados)


def test_requirements_contem_dependencias_sprint8():
    texto = (BACKEND / "requirements.txt").read_text(encoding="utf-8").lower()
    for pacote in ("sqlalchemy", "ollama", "beautifulsoup4", "pypdf"):
        assert pacote in texto


def test_env_exemplo_seguro_por_padrao():
    texto = (BACKEND / ".env.example").read_text(encoding="utf-8")
    assert "EXPORTAI_DIAGNOSTICO_IA_PROVEDOR=DESATIVADO" in texto
    assert "EXPORTAI_DIAGNOSTICO_BUSCA_PROVEDOR=DESATIVADO" in texto
    assert "EXPORTAI_TESTE_INTEGRACAO_REAL=false" in texto


def test_openapi_contem_endpoints_complementares():
    caminhos = app.openapi()["paths"]
    assert "/api/v1/diagnosticos/{diagnostico_id}/pesquisa-assistida" in caminhos
    assert "/api/v1/diagnosticos/{diagnostico_id}/pesquisa-assistida/automatica" in caminhos
    assert "/api/v1/diagnosticos/complementar/saude" in caminhos


def test_manifesto_registra_independencia_da_pontuacao():
    dados = json.loads((BACKEND / "MANIFESTO_SPRINT8.json").read_text(encoding="utf-8"))
    garantias = " ".join(dados["garantias"]).lower()
    assert "ausência de evidências não reduz o score" in garantias
    assert "ia não calcula pontuação" in garantias
