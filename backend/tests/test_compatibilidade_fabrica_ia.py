import pytest

from diagnostico.inteligencia.fabrica import criar_provedor


def test_provedor_desconhecido_mantem_mensagem_legada():
    with pytest.warns(RuntimeWarning, match="usando DESATIVADO"):
        provider = criar_provedor("OUTRA_IA")
    assert provider.nome == "DESATIVADO"


def test_ollama_continua_instanciavel_por_compatibilidade(monkeypatch):
    monkeypatch.setenv("EXPORTAI_DIAGNOSTICO_IA_MODELO", "modelo-teste")
    provider = criar_provedor("OLLAMA")
    assert provider.nome == "OLLAMA"
