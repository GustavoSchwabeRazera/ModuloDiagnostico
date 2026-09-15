from diagnostico.inteligencia.saude_complementar import verificar_saude_complementar
class Resp:
    def raise_for_status(self): pass
    def json(self): return {'models':[{'name':'modelo-teste'}]}
class Cliente:
    def get(self,*a,**k): return Resp()
def test_desativado_e_saudavel(monkeypatch):
    monkeypatch.setenv('EXPORTAI_DIAGNOSTICO_BUSCA_PROVEDOR','DESATIVADO'); monkeypatch.setenv('EXPORTAI_DIAGNOSTICO_IA_PROVEDOR','DESATIVADO')
    s=verificar_saude_complementar(); assert s.status=='OK'; assert any(x.status=='DESATIVADO' for x in s.componentes)
def test_ollama_configurado(monkeypatch):
    monkeypatch.setenv('EXPORTAI_DIAGNOSTICO_BUSCA_PROVEDOR','DESATIVADO'); monkeypatch.setenv('EXPORTAI_DIAGNOSTICO_IA_PROVEDOR','OLLAMA'); monkeypatch.setenv('EXPORTAI_DIAGNOSTICO_IA_MODELO','modelo-teste')
    s=verificar_saude_complementar(Cliente()); assert any(x.nome=='inteligencia' and x.status=='OK' for x in s.componentes)
def test_ollama_sem_modelo(monkeypatch):
    monkeypatch.setenv('EXPORTAI_DIAGNOSTICO_IA_PROVEDOR','OLLAMA'); monkeypatch.delenv('EXPORTAI_DIAGNOSTICO_IA_MODELO',raising=False)
    s=verificar_saude_complementar(); assert any(x.nome=='inteligencia' and x.status=='NAO_CONFIGURADO' for x in s.componentes)
def test_openapi_saude():
    from app.main import app
    assert '/api/v1/diagnosticos/complementar/saude' in app.openapi()['paths']
