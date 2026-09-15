from __future__ import annotations

from types import SimpleNamespace

from diagnostico.inteligencia.fabrica import criar_provedor_inteligencia
from diagnostico.inteligencia.provedor_fallback import ProvedorComFallback


def test_fabrica_desativada_por_padrao(monkeypatch):
    monkeypatch.delenv("EXPORTAI_DIAGNOSTICO_IA_PROVEDOR", raising=False)
    provider = criar_provedor_inteligencia()
    assert "Desativado" in provider.__class__.__name__


def test_ollama_e_tratado_como_legado(monkeypatch):
    # Compatibilidade histórica: o adaptador continua instanciável quando
    # solicitado explicitamente e com o modelo exigido pelo contrato antigo.
    monkeypatch.setenv("EXPORTAI_DIAGNOSTICO_IA_MODELO", "modelo-teste")
    provider = criar_provedor_inteligencia("OLLAMA")
    assert provider.nome == "OLLAMA"


def test_gemini_exige_modelo_sem_instanciar_cliente(monkeypatch):
    from diagnostico.inteligencia.provedor_gemini import ProvedorGemini
    monkeypatch.delenv("EXPORTAI_GEMINI_MODELO", raising=False)
    try:
        ProvedorGemini(api_key="x")
        assert False, "Era esperado ValueError"
    except ValueError:
        pass


def test_groq_exige_modelo_sem_instanciar_cliente(monkeypatch):
    from diagnostico.inteligencia.provedor_groq import ProvedorGroq
    monkeypatch.delenv("EXPORTAI_GROQ_MODELO", raising=False)
    try:
        ProvedorGroq(api_key="x")
        assert False, "Era esperado ValueError"
    except ValueError:
        pass


def test_fallback_e_usado_quando_primario_falha():
    class Falha:
        nome = "FALHA"
        def analisar(self, entrada):
            raise RuntimeError("não disponível")
    class Sucesso:
        nome = "SUCESSO"
        def analisar(self, entrada):
            return {"ok": True}
    provider = ProvedorComFallback(Falha(), Sucesso())
    assert provider.analisar({}) == {"ok": True}


def test_gemini_configura_json_schema(monkeypatch):
    from diagnostico.inteligencia import provedor_gemini as module
    captured = {}
    class Models:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(text='{}', parsed=None)
    client = SimpleNamespace(models=Models())
    provider = module.ProvedorGemini(modelo="modelo-teste", cliente=client)
    monkeypatch.setattr(module, "validar_saida", lambda raw, entrada: {"raw": raw})
    monkeypatch.setattr(module, "schema_saida", lambda: {"type": "object"})
    result = provider.analisar({"pais": {"iso3": "DEU"}, "evidencias": []})
    assert result == {"raw": "{}"}
    assert captured["config"]["response_mime_type"] == "application/json"
    assert captured["config"]["response_json_schema"] == {"type": "object"}


def test_groq_configura_json_schema(monkeypatch):
    from diagnostico.inteligencia import provedor_groq as module
    captured = {}
    class Completions:
        def create(self, **kwargs):
            captured.update(kwargs)
            message = SimpleNamespace(content='{}')
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])
    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    provider = module.ProvedorGroq(modelo="modelo-teste", cliente=client, strict=False)
    monkeypatch.setattr(module, "validar_saida", lambda raw, entrada: {"raw": raw})
    monkeypatch.setattr(module, "schema_saida", lambda: {"type": "object"})
    result = provider.analisar({"pais": {"iso3": "DEU"}, "evidencias": []})
    assert result == {"raw": "{}"}
    assert captured["response_format"]["type"] == "json_schema"
    assert captured["response_format"]["json_schema"]["schema"] == {"type": "object"}
