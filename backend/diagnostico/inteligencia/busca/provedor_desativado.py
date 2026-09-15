from diagnostico.inteligencia.busca.contratos import ProvedorBuscaWeb
from diagnostico.inteligencia.busca.schemas import ConsultaBusca,SaidaBusca
class ProvedorBuscaDesativado(ProvedorBuscaWeb):
    nome="DESATIVADO"
    def buscar(self,entrada): return SaidaBusca(status="INDISPONIVEL",resultados=[],mensagem="O provedor de busca externa não está configurado.")
