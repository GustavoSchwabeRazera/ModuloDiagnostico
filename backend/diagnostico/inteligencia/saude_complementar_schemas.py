from datetime import datetime
from typing import Literal
from pydantic import BaseModel,ConfigDict
class S(BaseModel): model_config=ConfigDict(extra="forbid")
class ComponenteSaude(S):
    nome:str; status:Literal["OK","DESATIVADO","ERRO","NAO_CONFIGURADO"]; detalhe:str
class SaudeComplementar(S):
    status:Literal["OK","PARCIAL","INDISPONIVEL"]; componentes:list[ComponenteSaude]; verificado_em:datetime
