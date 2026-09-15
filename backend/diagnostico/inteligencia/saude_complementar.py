from datetime import datetime,timezone
import os
from pathlib import Path
import httpx
from diagnostico.inteligencia.fontes import carregar_catalogo
from diagnostico.inteligencia.saude_complementar_schemas import ComponenteSaude,SaudeComplementar

def _componente(nome,status,detalhe): return ComponenteSaude(nome=nome,status=status,detalhe=detalhe)
def verificar_saude_complementar(cliente=None):
    itens=[]
    try:
        c=carregar_catalogo(); itens.append(_componente('catalogo_fontes','OK',f'Catálogo {c.versao} carregado com {len(c.fontes)} fontes.'))
    except Exception as e: itens.append(_componente('catalogo_fontes','ERRO',str(e)))
    busca=os.getenv('EXPORTAI_DIAGNOSTICO_BUSCA_PROVEDOR','DESATIVADO').strip().upper()
    if busca=='DESATIVADO': itens.append(_componente('busca_web','DESATIVADO','Busca externa desativada; diagnóstico principal permanece operacional.'))
    elif busca=='SEARXNG':
        url=os.getenv('EXPORTAI_DIAGNOSTICO_SEARXNG_URL','').strip()
        if not url: itens.append(_componente('busca_web','NAO_CONFIGURADO','URL do SearXNG não definida.'))
        else:
            try:
                cli=cliente or httpx.Client(timeout=5); r=cli.get(url.rstrip('/')+'/search',params={'q':'ExportAI health','format':'json'}); r.raise_for_status(); r.json(); itens.append(_componente('busca_web','OK','SearXNG respondeu em JSON.'))
            except Exception as e: itens.append(_componente('busca_web','ERRO',str(e)))
    else: itens.append(_componente('busca_web','NAO_CONFIGURADO',f'Provedor {busca} desconhecido.'))
    ia=os.getenv('EXPORTAI_DIAGNOSTICO_IA_PROVEDOR','DESATIVADO').strip().upper()
    if ia=='DESATIVADO': itens.append(_componente('inteligencia','DESATIVADO','IA desativada; cálculo determinístico permanece operacional.'))
    elif ia=='OLLAMA':
        host=os.getenv('EXPORTAI_DIAGNOSTICO_OLLAMA_HOST','http://127.0.0.1:11434').rstrip('/'); modelo=os.getenv('EXPORTAI_DIAGNOSTICO_IA_MODELO','').strip()
        if not modelo: itens.append(_componente('inteligencia','NAO_CONFIGURADO','Modelo Ollama não definido.'))
        else:
            try:
                cli=cliente or httpx.Client(timeout=5); r=cli.get(host+'/api/tags'); r.raise_for_status(); nomes={m.get('name') for m in r.json().get('models',[])}
                status='OK' if modelo in nomes else 'NAO_CONFIGURADO'; detalhe='Ollama disponível e modelo instalado.' if status=='OK' else f'Modelo {modelo} não encontrado no Ollama.'; itens.append(_componente('inteligencia',status,detalhe))
            except Exception as e: itens.append(_componente('inteligencia','ERRO',str(e)))
    else: itens.append(_componente('inteligencia','NAO_CONFIGURADO',f'Provedor {ia} desconhecido.'))
    ruins=[x for x in itens if x.status in {'ERRO','NAO_CONFIGURADO'}]
    ativos=[x for x in itens if x.status=='OK']
    status='INDISPONIVEL' if ruins and not ativos else ('PARCIAL' if ruins else 'OK')
    return SaudeComplementar(status=status,componentes=itens,verificado_em=datetime.now(timezone.utc))
