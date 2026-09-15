from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
class S(BaseModel): model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
class ConsultaBusca(S):
    consulta:str=Field(min_length=10,max_length=2000); dominio_permitido:str; limite:int=Field(default=5,ge=1,le=10)
class ItemBusca(S):
    titulo:str=Field(min_length=1,max_length=500); url:HttpUrl; resumo:str=Field(default="",max_length=3000)
class SaidaBusca(S):
    status:Literal["CONCLUIDA","INDISPONIVEL","ERRO"]; resultados:list[ItemBusca]=Field(default_factory=list); mensagem:str|None=None
