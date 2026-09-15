import os
import httpx
from diagnostico.inteligencia.busca.extrator_html import extrair_html
from diagnostico.inteligencia.busca.extrator_pdf import extrair_pdf
from diagnostico.inteligencia.busca.seguranca import validar_url
class ErroDownload(RuntimeError): pass
class DownloaderSeguro:
    def __init__(self,cliente=None):
        self.timeout=float(os.getenv('EXPORTAI_DIAGNOSTICO_DOWNLOAD_TIMEOUT','15')); self.max_bytes=int(os.getenv('EXPORTAI_DIAGNOSTICO_DOWNLOAD_MAX_BYTES','3000000')); self.cliente=cliente
    def baixar(self,url,dominios):
        validar_url(url,dominios,resolver_dns=self.cliente is None)
        c=self.cliente or httpx.Client(timeout=self.timeout,follow_redirects=False,headers={'User-Agent':'ExportAI-Diagnostico/1.0'})
        fechar=self.cliente is None
        try:
            r=c.get(str(url));
            if 300<=r.status_code<400: raise ErroDownload('Redirecionamento não permitido.')
            r.raise_for_status(); data=r.content
            if len(data)>self.max_bytes: raise ErroDownload('Resposta acima do limite.')
            tipo=r.headers.get('content-type','').split(';')[0].lower()
            if tipo not in {'text/html','text/plain','application/pdf'}: raise ErroDownload('Tipo de conteúdo não permitido.')
            if tipo=='text/html': titulo,texto=extrair_html(data)
            elif tipo=='application/pdf': titulo,texto=extrair_pdf(data)
            else: titulo='Documento de texto'; texto=data.decode(r.encoding or 'utf-8',errors='replace').strip()
            if len(texto)<10: raise ErroDownload('Conteúdo textual insuficiente.')
            return {'url':str(url),'titulo':titulo,'texto':texto,'content_type':tipo}
        finally:
            if fechar: c.close()
