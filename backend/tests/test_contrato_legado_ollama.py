from diagnostico.inteligencia.fabrica import criar_provedor_inteligencia


def test_ollama_explicito_exige_configuracao_legada(monkeypatch):
    monkeypatch.delenv("EXPORTAI_DIAGNOSTICO_IA_MODELO", raising=False)
    try:
        criar_provedor_inteligencia("OLLAMA")
        assert False, "Era esperado erro de configuração do adaptador legado."
    except Exception as error:
        assert "EXPORTAI_DIAGNOSTICO_IA_MODELO" in str(error)


def test_ollama_explicito_funciona_com_modelo_legado(monkeypatch):
    monkeypatch.setenv("EXPORTAI_DIAGNOSTICO_IA_MODELO", "modelo-teste")
    provider = criar_provedor_inteligencia("OLLAMA")
    assert provider.nome == "OLLAMA"
