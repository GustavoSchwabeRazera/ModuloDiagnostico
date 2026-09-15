from abc import ABC,abstractmethod
from diagnostico.inteligencia.busca.schemas import ConsultaBusca,SaidaBusca
class ProvedorBuscaWeb(ABC):
    nome:str
    @abstractmethod
    def buscar(self,entrada:ConsultaBusca)->SaidaBusca: raise NotImplementedError
