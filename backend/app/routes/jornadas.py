from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from diagnostico.jornada_schemas import (
    AssociarDiagnosticoRequest,
    CriarJornadaRequest,
    CriarJornadaResponse,
    JornadaPublica,
    PrepararDiagnosticoResponse,
    SelecionarMercadosRequest,
)
from diagnostico.jornada_service import (
    JornadaExpirada,
    JornadaNaoEncontrada,
    RegraJornadaInvalida,
    ServicoJornadas,
    TokenJornadaInvalido,
)

router = APIRouter(prefix="/api/v1/jornadas", tags=["Jornadas anônimas"])
security = HTTPBearer(auto_error=False)
service = ServicoJornadas()


def bearer(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"erro": {"codigo": "TOKEN_AUSENTE", "mensagem": "Informe o token de retomada."}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def auth(journey_id: str, token: str) -> dict:
    try:
        return service.autenticar(journey_id, token)
    except JornadaNaoEncontrada as exc:
        raise HTTPException(status_code=404, detail={"erro": {"codigo": "JORNADA_NAO_ENCONTRADA", "mensagem": str(exc)}}) from exc
    except TokenJornadaInvalido as exc:
        raise HTTPException(status_code=401, detail={"erro": {"codigo": "TOKEN_INVALIDO", "mensagem": str(exc)}}, headers={"WWW-Authenticate": "Bearer"}) from exc
    except JornadaExpirada as exc:
        raise HTTPException(status_code=410, detail={"erro": {"codigo": "JORNADA_EXPIRADA", "mensagem": str(exc)}}) from exc


@router.post("", response_model=CriarJornadaResponse, status_code=201)
def criar_jornada(payload: CriarJornadaRequest):
    data, token = service.criar(payload.produto.model_dump(), [m.model_dump() for m in payload.mercados_basico])
    return {"journey_id": data["journey_id"], "resume_token": token, "status": data["status"], "expira_em": data["expira_em"]}


@router.get("/{journey_id}", response_model=JornadaPublica)
def obter_jornada(journey_id: str, token: str = Depends(bearer)):
    return service.public(auth(journey_id, token))


@router.put("/{journey_id}/mercados", response_model=JornadaPublica)
def selecionar_mercados(journey_id: str, payload: SelecionarMercadosRequest, token: str = Depends(bearer)):
    data = auth(journey_id, token)
    try:
        return service.public(service.selecionar_mercados(data, payload.mercados_escolhidos))
    except RegraJornadaInvalida as exc:
        raise HTTPException(status_code=400, detail={"erro": {"codigo": "MERCADOS_INVALIDOS", "mensagem": str(exc)}}) from exc


@router.get("/{journey_id}/diagnostico-payload", response_model=PrepararDiagnosticoResponse)
def preparar_diagnostico(journey_id: str, token: str = Depends(bearer)):
    data = auth(journey_id, token)
    try:
        return {"journey_id": journey_id, "diagnostico_payload": service.diagnostic_payload(data), "status": "PRONTA_PARA_DIAGNOSTICO"}
    except RegraJornadaInvalida as exc:
        raise HTTPException(status_code=409, detail={"erro": {"codigo": "JORNADA_INCOMPLETA", "mensagem": str(exc)}}) from exc


@router.put("/{journey_id}/diagnostico", response_model=JornadaPublica)
def associar_diagnostico(journey_id: str, payload: AssociarDiagnosticoRequest, token: str = Depends(bearer)):
    data = auth(journey_id, token)
    return service.public(service.associar_diagnostico(data, payload.diagnostico_id))


from pydantic import BaseModel, ConfigDict
from diagnostico.handoff_service import ServicoHandoff, HandoffInvalido, HandoffExpirado, HandoffConsumido
handoff_service = ServicoHandoff()

class CriarHandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destino: str
class TrocarHandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    handoff_code: str

@router.post("/{journey_id}/handoff", status_code=201)
def criar_handoff(journey_id: str, payload: CriarHandoffRequest, token: str = Depends(bearer)):
    auth(journey_id, token)
    try: return handoff_service.criar(journey_id, token, payload.destino)
    except HandoffInvalido as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/handoff/trocar")
def trocar_handoff(payload: TrocarHandoffRequest):
    try: return handoff_service.trocar(payload.handoff_code)
    except HandoffInvalido as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HandoffExpirado as exc: raise HTTPException(status_code=410, detail=str(exc)) from exc
    except HandoffConsumido as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
