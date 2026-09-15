from pydantic import BaseModel,ConfigDict,Field
from diagnostico.inteligencia.orquestrador_schemas import ResultadoPesquisaAssistida

class Schema(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)

class ExecutarPesquisaAutomaticaRequest(Schema):
    incluir_documentos_manuais: bool=True
    maximo_resultados_por_consulta: int=Field(default=3,ge=1,le=5)

class EstatisticaBuscaPais(Schema):
    pais_iso3:str=Field(pattern=r"^[A-Z]{3}$")
    consultas_executadas:int=Field(ge=0)
    urls_encontradas:int=Field(ge=0)
    documentos_baixados:int=Field(ge=0)
    falhas:list[str]=Field(default_factory=list)

class ResultadoPesquisaAutomatica(Schema):
    busca_provedor:str
    estatisticas:list[EstatisticaBuscaPais]
    pesquisa:ResultadoPesquisaAssistida
