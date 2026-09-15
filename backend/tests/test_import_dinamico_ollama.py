from diagnostico.inteligencia.fabrica import criar_provedor


def test_fabrica_descobre_classe_real_do_modulo_ollama(monkeypatch):
    monkeypatch.setenv("EXPORTAI_DIAGNOSTICO_IA_MODELO", "modelo-teste")
    provider = criar_provedor("OLLAMA")
    assert provider.nome == "OLLAMA"
    assert "ollama" in provider.__class__.__module__.lower()
