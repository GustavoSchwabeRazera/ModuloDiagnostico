import os
from urllib.parse import urljoin
import httpx
from diagnostico.inteligencia.busca.contratos import ProvedorBuscaWeb
from diagnostico.inteligencia.busca.schemas import ConsultaBusca,ItemBusca,SaidaBusca
from diagnostico.inteligencia.busca.seguranca import validar_url
class ProvedorBuscaSearXNG(ProvedorBuscaWeb):
    nome='SEARXNG'
    def __init__(self,cliente=None,url=None):
        self.url=(url or os.getenv('EXPORTAI_DIAGNOSTICO_SEARXNG_URL','')).strip()
        if not self.url: raise ValueError('Defina EXPORTAI_DIAGNOSTICO_SEARXNG_URL.')
        self.cliente=cliente or httpx.Client(timeout=20)
    def buscar(self,entrada):
        e=entrada if isinstance(entrada,ConsultaBusca) else ConsultaBusca.model_validate(entrada)
        r=self.cliente.get(urljoin(self.url.rstrip('/')+'/', 'search'),params={'q':e.consulta,'format':'json','safesearch':1}); r.raise_for_status()
        itens=[]
        for x in r.json().get('results',[]):
            try: validar_url(x.get('url',''),[e.dominio_permitido])
            except ValueError: continue
            itens.append(ItemBusca(titulo=x.get('title') or 'Resultado sem título',url=x['url'],resumo=x.get('content') or ''))
            if len(itens)>=e.limite: break
        return SaidaBusca(status='CONCLUIDA',resultados=itens,mensagem=None)
