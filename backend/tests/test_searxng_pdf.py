from io import BytesIO
from pypdf import PdfWriter
from diagnostico.inteligencia.busca.provedor_searxng import ProvedorBuscaSearXNG
class R:
    def raise_for_status(self): pass
    def json(self): return {'results':[{'title':'OK','url':'https://trade.ec.europa.eu/x','content':'resumo'},{'title':'X','url':'https://evil.test/x'}]}
class C:
    def get(self,*a,**k): return R()
def test_searxng_filtra_dominio():
    p=ProvedorBuscaSearXNG(C(),'https://searx.local'); s=p.buscar({'consulta':'site:trade.ec.europa.eu regra produto','dominio_permitido':'trade.ec.europa.eu','limite':5}); assert len(s.resultados)==1
def test_pdf_vazio_rejeitado():
    from diagnostico.inteligencia.busca.extrator_pdf import ErroPDF,extrair_pdf
    import pytest
    b=BytesIO(); w=PdfWriter(); w.add_blank_page(width=100,height=100); w.write(b)
    with pytest.raises(ErroPDF): extrair_pdf(b.getvalue())
