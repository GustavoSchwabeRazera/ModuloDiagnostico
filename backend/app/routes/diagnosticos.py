from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from diagnostico.motor import (
    CatalogoIncompativelError,
    ErroDiagnostico,
    MotorDiagnostico,
    RespostasIncompletasError,
)
from diagnostico.inteligencia.fabrica import criar_provedor
from diagnostico.inteligencia.orquestrador import ErroOrquestracao, OrquestradorPesquisaAssistida
from diagnostico.inteligencia.orquestrador_schemas import (
    ExecutarPesquisaAssistidaRequest,
    ResultadoPesquisaAssistida,
)
from diagnostico.inteligencia.busca.fabrica import criar_provedor_busca
from diagnostico.inteligencia.pesquisa_automatica import ErroPesquisaAutomatica, ServicoPesquisaAutomatica
from diagnostico.inteligencia.pesquisa_automatica_schemas import ExecutarPesquisaAutomaticaRequest, ResultadoPesquisaAutomatica
from diagnostico.inteligencia.saude_complementar import verificar_saude_complementar
from diagnostico.inteligencia.saude_complementar_schemas import SaudeComplementar
from diagnostico.repositorio_sqlite import repositorio_diagnosticos
from diagnostico.schemas import (
    AtualizarMercadosRequest,
    CatalogoChecklist,
    CriarDiagnosticoRequest,
    MercadoBasico,
    ProdutoDiagnostico,
    RegistrarRespostasRequest,
    RespostaChecklist,
    ResultadoDiagnostico,
)

router = APIRouter(prefix="/api/v1/diagnosticos", tags=["Diagnóstico"])
DIRETORIO_DATA = Path(__file__).resolve().parents[2] / "diagnostico" / "data"
CATALOGO = CatalogoChecklist.model_validate(
    json.loads((DIRETORIO_DATA / "catalogo_checklist_v1.json").read_text(encoding="utf-8"))
)
MOTOR = MotorDiagnostico()

StatusSessao = Literal["CRIADO", "EM_PREENCHIMENTO", "PRONTO_PARA_CALCULAR", "CALCULADO"]


class ApiSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SessaoCriadaResponse(ApiSchema):
    diagnostico_id: UUID
    status: StatusSessao
    catalogo_versao: str
    criado_em: datetime


class SessaoDiagnosticoResponse(ApiSchema):
    diagnostico_id: UUID
    status: StatusSessao
    catalogo_versao: str
    produto: ProdutoDiagnostico
    mercados_basico: list[MercadoBasico]
    mercados_escolhidos: list[str] = Field(min_length=1, max_length=3)
    respostas: list[RespostaChecklist]
    resultado: ResultadoDiagnostico | None
    pesquisa_assistida: dict[str, Any] | None = None
    criado_em: datetime
    atualizado_em: datetime


class RespostasRegistradasResponse(ApiSchema):
    diagnostico_id: UUID
    status: StatusSessao
    respostas_registradas: int
    total_itens_ativos: int
    faltam_responder: int
    resultado_invalidado: bool


class MercadosAtualizadosResponse(ApiSchema):
    diagnostico_id: UUID
    mercados_escolhidos: list[str]
    resultado_invalidado: bool


def agora() -> datetime:
    return datetime.now(timezone.utc)


def erro(status_code: int, codigo: str, mensagem: str):
    raise HTTPException(
        status_code=status_code,
        detail={"erro": {"codigo": codigo, "mensagem": mensagem}},
    )


def obter_sessao(diagnostico_id: UUID) -> dict:
    sessao = repositorio_diagnosticos.obter(str(diagnostico_id))
    if sessao is None:
        erro(404, "DIAGNOSTICO_NAO_ENCONTRADO", "Sessão de diagnóstico não encontrada.")
    return sessao


def status_respostas(respostas: list[dict]) -> StatusSessao:
    total = sum(1 for item in CATALOGO.itens if item.ativo)
    if not respostas:
        return "CRIADO"
    if len(respostas) < total:
        return "EM_PREENCHIMENTO"
    return "PRONTO_PARA_CALCULAR"


def validar_mercados_da_sessao(sessao: dict, escolhidos: list[str]) -> None:
    disponiveis = {mercado["iso3"] for mercado in sessao["mercados_basico"]}
    ausentes = [iso3 for iso3 in escolhidos if iso3 not in disponiveis]
    if ausentes:
        erro(
            400,
            "MERCADO_FORA_DO_RESULTADO_BASICO",
            "Países não recebidos do Módulo Básico: " + ", ".join(ausentes),
        )



@router.get(
    "/complementar/saude",
    response_model=SaudeComplementar,
    summary="Verifica a saúde da camada complementar",
)
def saude_camadas_complementares() -> SaudeComplementar:
    return verificar_saude_complementar()


@router.get(
    "/checklist",
    response_model=CatalogoChecklist,
    summary="Consulta o checklist do Módulo Diagnóstico",
)
def consultar_checklist() -> CatalogoChecklist:
    return CATALOGO


@router.post(
    "",
    response_model=SessaoCriadaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma sessão de diagnóstico",
)
def criar_diagnostico(entrada: CriarDiagnosticoRequest) -> SessaoCriadaResponse:
    instante = agora()
    identificador = uuid4()
    sessao = {
        "diagnostico_id": str(identificador),
        "status": "CRIADO",
        "catalogo_versao": CATALOGO.versao,
        "produto": entrada.produto.model_dump(),
        "mercados_basico": [mercado.model_dump() for mercado in entrada.mercados_basico],
        "mercados_escolhidos": list(entrada.mercados_escolhidos),
        "respostas": [],
        "resultado": None,
        "pesquisa_assistida": None,
        "criado_em": instante,
        "atualizado_em": instante,
    }
    repositorio_diagnosticos.criar(sessao)
    return SessaoCriadaResponse(
        diagnostico_id=identificador,
        status="CRIADO",
        catalogo_versao=CATALOGO.versao,
        criado_em=instante,
    )


@router.get(
    "/{diagnostico_id}",
    response_model=SessaoDiagnosticoResponse,
    summary="Consulta uma sessão de diagnóstico",
)
def consultar_diagnostico(diagnostico_id: UUID) -> SessaoDiagnosticoResponse:
    return SessaoDiagnosticoResponse.model_validate(obter_sessao(diagnostico_id))


@router.put(
    "/{diagnostico_id}/mercados",
    response_model=MercadosAtualizadosResponse,
    summary="Atualiza os países escolhidos",
)
def atualizar_mercados(
    diagnostico_id: UUID,
    entrada: AtualizarMercadosRequest,
) -> MercadosAtualizadosResponse:
    sessao = obter_sessao(diagnostico_id)
    validar_mercados_da_sessao(sessao, entrada.mercados_escolhidos)
    invalidado = sessao["resultado"] is not None
    sessao["mercados_escolhidos"] = list(entrada.mercados_escolhidos)
    sessao["resultado"] = None
    sessao["status"] = status_respostas(sessao["respostas"])
    sessao["atualizado_em"] = agora()
    repositorio_diagnosticos.salvar(str(diagnostico_id), sessao)
    return MercadosAtualizadosResponse(
        diagnostico_id=diagnostico_id,
        mercados_escolhidos=entrada.mercados_escolhidos,
        resultado_invalidado=invalidado,
    )


@router.put(
    "/{diagnostico_id}/respostas",
    response_model=RespostasRegistradasResponse,
    summary="Registra respostas parciais ou completas",
)
def registrar_respostas(
    diagnostico_id: UUID,
    entrada: RegistrarRespostasRequest,
) -> RespostasRegistradasResponse:
    sessao = obter_sessao(diagnostico_id)
    if entrada.catalogo_versao != CATALOGO.versao:
        erro(409, "VERSAO_CATALOGO_INCOMPATIVEL", "A versão do checklist não é a versão ativa.")

    itens_ativos = {item.codigo for item in CATALOGO.itens if item.ativo}
    desconhecidos = sorted({r.item_codigo for r in entrada.respostas} - itens_ativos)
    if desconhecidos:
        erro(400, "ITEM_CHECKLIST_INVALIDO", "Itens desconhecidos: " + ", ".join(desconhecidos))

    por_codigo = {resposta["item_codigo"]: resposta for resposta in sessao["respostas"]}
    for resposta in entrada.respostas:
        por_codigo[resposta.item_codigo] = resposta.model_dump()

    invalidado = sessao["resultado"] is not None
    sessao["respostas"] = [
        por_codigo[item.codigo]
        for item in CATALOGO.itens
        if item.ativo and item.codigo in por_codigo
    ]
    sessao["resultado"] = None
    sessao["status"] = status_respostas(sessao["respostas"])
    sessao["atualizado_em"] = agora()
    repositorio_diagnosticos.salvar(str(diagnostico_id), sessao)

    total = len(itens_ativos)
    registrados = len(sessao["respostas"])
    return RespostasRegistradasResponse(
        diagnostico_id=diagnostico_id,
        status=sessao["status"],
        respostas_registradas=registrados,
        total_itens_ativos=total,
        faltam_responder=total - registrados,
        resultado_invalidado=invalidado,
    )


@router.post(
    "/{diagnostico_id}/calcular",
    response_model=ResultadoDiagnostico,
    summary="Calcula o resultado do diagnóstico",
)
def calcular_diagnostico(diagnostico_id: UUID) -> ResultadoDiagnostico:
    sessao = obter_sessao(diagnostico_id)
    try:
        resultado = MOTOR.calcular(
            {
                "catalogo_versao": sessao["catalogo_versao"],
                "respostas": sessao["respostas"],
            },
            mercados_escolhidos=sessao["mercados_escolhidos"],
            exigir_todas_respostas=True,
        )
    except RespostasIncompletasError as exc:
        erro(409, "RESPOSTAS_INCOMPLETAS", str(exc))
    except CatalogoIncompativelError as exc:
        erro(409, "CATALOGO_INCOMPATIVEL", str(exc))
    except ErroDiagnostico as exc:
        erro(400, "DIAGNOSTICO_INVALIDO", str(exc))

    sessao["resultado"] = resultado.model_dump()
    sessao["status"] = "CALCULADO"
    sessao["atualizado_em"] = agora()
    repositorio_diagnosticos.salvar(str(diagnostico_id), sessao)
    return resultado


@router.get(
    "/{diagnostico_id}/resultado",
    response_model=ResultadoDiagnostico,
    summary="Consulta o último resultado calculado",
)
def consultar_resultado(diagnostico_id: UUID) -> ResultadoDiagnostico:
    sessao = obter_sessao(diagnostico_id)
    if sessao["resultado"] is None:
        erro(409, "RESULTADO_NAO_CALCULADO", "O diagnóstico ainda não possui resultado calculado.")
    return ResultadoDiagnostico.model_validate(sessao["resultado"])

@router.post(
    "/{diagnostico_id}/pesquisa-assistida",
    response_model=ResultadoPesquisaAssistida,
    summary="Executa a interpretação complementar por país",
)
def executar_pesquisa_assistida(
    diagnostico_id: UUID,
    entrada: ExecutarPesquisaAssistidaRequest,
) -> ResultadoPesquisaAssistida:
    sessao = obter_sessao(diagnostico_id)
    if sessao.get("resultado") is None:
        erro(
            409,
            "DIAGNOSTICO_NAO_CALCULADO",
            "Calcule o diagnóstico determinístico antes da pesquisa assistida.",
        )
    try:
        provedor = criar_provedor()
        orquestrador = OrquestradorPesquisaAssistida(
            repositorio_diagnosticos,
            provedor,
        )
        return orquestrador.executar(str(diagnostico_id), entrada)
    except ErroOrquestracao as exc:
        erro(400, "PESQUISA_ASSISTIDA_INVALIDA", str(exc))
    except Exception as exc:
        erro(
            503,
            "PESQUISA_ASSISTIDA_INDISPONIVEL",
            f"A pesquisa complementar não pôde ser executada: {exc}",
        )



@router.post(
    "/{diagnostico_id}/pesquisa-assistida/automatica",
    response_model=ResultadoPesquisaAutomatica,
    summary="Busca fontes autorizadas e executa interpretação complementar",
)
def executar_pesquisa_assistida_automatica(
    diagnostico_id: UUID,
    entrada: ExecutarPesquisaAutomaticaRequest,
) -> ResultadoPesquisaAutomatica:
    obter_sessao(diagnostico_id)
    try:
        servico=ServicoPesquisaAutomatica(
            repositorio_diagnosticos,
            criar_provedor(),
            criar_provedor_busca(),
        )
        return servico.executar(str(diagnostico_id),entrada)
    except ErroPesquisaAutomatica as exc:
        erro(409,"PESQUISA_AUTOMATICA_INVALIDA",str(exc))
    except Exception as exc:
        erro(503,"PESQUISA_AUTOMATICA_INDISPONIVEL",f"A busca complementar não pôde ser concluída: {exc}")


@router.get(
    "/{diagnostico_id}/pesquisa-assistida",
    response_model=ResultadoPesquisaAssistida,
    summary="Consulta a última pesquisa assistida",
)
def consultar_pesquisa_assistida(
    diagnostico_id: UUID,
) -> ResultadoPesquisaAssistida:
    sessao = obter_sessao(diagnostico_id)
    pesquisa = sessao.get("pesquisa_assistida")
    if pesquisa is None:
        erro(
            404,
            "PESQUISA_ASSISTIDA_NAO_ENCONTRADA",
            "A sessão ainda não possui pesquisa assistida.",
        )
    return ResultadoPesquisaAssistida.model_validate(pesquisa)

