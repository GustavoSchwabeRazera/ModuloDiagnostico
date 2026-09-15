import os,pytest
from diagnostico.inteligencia.busca.fabrica import criar_provedor_busca
from diagnostico.inteligencia.provedor_ollama import ProvedorInteligenciaOllama
@pytest.mark.skipif(os.getenv('EXPORTAI_TESTE_INTEGRACAO_REAL')!='true',reason='Integração real desativada.')
def test_provedores_reais_inicializam():
    assert criar_provedor_busca().nome=='SEARXNG'
    assert ProvedorInteligenciaOllama().nome=='OLLAMA'
