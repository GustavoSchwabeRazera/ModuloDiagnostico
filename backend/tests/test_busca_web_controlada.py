import pytest
from diagnostico.inteligencia.busca.fabrica import criar_provedor_busca
from diagnostico.inteligencia.busca.extrator_html import extrair_html
from diagnostico.inteligencia.busca.seguranca import ErroURL,validar_url
def test_desativado(): assert criar_provedor_busca().buscar({'consulta':'site:europa.eu requisito produto','dominio_permitido':'europa.eu'}).status=='INDISPONIVEL'
def test_https():
    with pytest.raises(ErroURL): validar_url('http://europa.eu/x',['europa.eu'])
def test_subdominio(): assert validar_url('https://trade.ec.europa.eu/x',['europa.eu'])
def test_dominio_falso():
    with pytest.raises(ErroURL): validar_url('https://europa.eu.exemplo.com/x',['europa.eu'])
def test_local():
    with pytest.raises(ErroURL): validar_url('https://localhost/x',['localhost'])
def test_ip_privado():
    with pytest.raises(ErroURL): validar_url('https://127.0.0.1/x',['127.0.0.1'])
def test_html():
    t,x=extrair_html(b'<html><head><title>Regra</title><style>x</style></head><body><nav>menu</nav><main>Requisito oficial aplicavel ao produto.</main><script>x</script></body></html>')
    assert t=='Regra' and 'Requisito oficial' in x and 'menu' not in x
