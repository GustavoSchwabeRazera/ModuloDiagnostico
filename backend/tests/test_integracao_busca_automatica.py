from copy import deepcopy
from datetime import datetime,timezone
from diagnostico.inteligencia.pesquisa_automatica import ServicoPesquisaAutomatica
from diagnostico.inteligencia.schemas import SaidaInteligenciaMercado
from diagnostico.inteligencia.busca.schemas import SaidaBusca,ItemBusca

class Repo:
    def __init__(self):
        agora=datetime.now(timezone.utc); self.s={
            'diagnostico_id':'diag-1','status':'CALCULADO','catalogo_versao':'1.0.0',
            'produto':{'ncm':'09011110','hs6':'090111','descricao':'Café'},
            'mercados_basico':[{'iso3':'DEU','nome':'Alemanha'}],'mercados_escolhidos':['DEU'],
            'respostas':[],'resultado':{'score_geral':80.0,'nivel':'PRONTA'},
            'pesquisa_assistida':None,'criado_em':agora,'atualizado_em':agora}
    def obter(self,i): return deepcopy(self.s) if i=='diag-1' else None
    def salvar(self,i,s): self.s=deepcopy(s); return deepcopy(s)
class Busca:
    nome='FAKE_BUSCA'
    def buscar(self,e):
        if e.dominio_permitido=='trade.ec.europa.eu':
            return SaidaBusca(status='CONCLUIDA',resultados=[ItemBusca(titulo='Regra',url='https://trade.ec.europa.eu/regra',resumo='x')])
        return SaidaBusca(status='CONCLUIDA',resultados=[])
class Download:
    def baixar(self,url,dominios): return {'url':url,'titulo':'Regra oficial','texto':'Conteúdo oficial suficientemente longo para evidência.','content_type':'text/html'}
class IA:
    nome='FAKE_IA'
    def analisar(self,e): return SaidaInteligenciaMercado(
        pais_iso3=e.pais.iso3,status='CONCLUIDA_COM_RESSALVAS',resumo='Análise concluída.',
        requisitos=[],nao_confirmados=[],alertas=[],evidencias_disponiveis=[x.evidencia_id for x in e.evidencias])
class BuscaFalha:
    nome='FALHA'
    def buscar(self,e): raise RuntimeError('offline')

def test_fluxo_automatico_baixa_e_analisa():
    r=Repo(); out=ServicoPesquisaAutomatica(r,IA(),Busca(),Download()).executar('diag-1',{})
    assert out.busca_provedor=='FAKE_BUSCA'
    assert out.estatisticas[0].documentos_baixados>=1
    assert out.pesquisa.pontuacao_preservada is True
    assert r.s['resultado']['score_geral']==80.0

def test_falha_busca_nao_impede_diagnostico():
    r=Repo(); out=ServicoPesquisaAutomatica(r,IA(),BuscaFalha(),Download()).executar('diag-1',{})
    assert out.estatisticas[0].documentos_baixados==0
    assert out.estatisticas[0].falhas
    assert out.pesquisa.score_geral_antes==80.0
    assert out.pesquisa.score_geral_depois==80.0

def test_openapi_expoe_endpoint_automatico():
    from app.main import app
    assert '/api/v1/diagnosticos/{diagnostico_id}/pesquisa-assistida/automatica' in app.openapi()['paths']
