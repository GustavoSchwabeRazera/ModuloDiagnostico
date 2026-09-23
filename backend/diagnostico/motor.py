from __future__ import annotations

import json
from pathlib import Path

from diagnostico.schemas import (
    AcaoPlano,
    BloqueadorDiagnostico,
    CatalogoChecklist,
    PesquisaMercadoResumo,
    RegistrarRespostasRequest,
    ResultadoDiagnostico,
    ScoreDimensao,
)

DIRETORIO_DATA = Path(__file__).resolve().parent / "data"
CATALOGO_PADRAO = DIRETORIO_DATA / "catalogo_checklist_v1.json"
REGRAS_PADRAO = DIRETORIO_DATA / "regras_pontuacao_v1.json"


class ErroDiagnostico(ValueError):
    """Erro de domínio do motor determinístico."""


class CatalogoIncompativelError(ErroDiagnostico):
    pass


class RespostasIncompletasError(ErroDiagnostico):
    pass


def carregar_json(caminho: Path) -> dict:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except FileNotFoundError as erro:
        raise CatalogoIncompativelError(f"Arquivo não encontrado: {caminho}") from erro
    except json.JSONDecodeError as erro:
        raise CatalogoIncompativelError(f"JSON inválido: {caminho}") from erro


def arredondar(valor: float) -> float:
    return round(valor + 1e-12, 2)


def nivel_prontidao(score: float, faixas: list[dict]) -> str:
    for faixa in faixas:
        minimo = float(faixa["minimo"])
        if "maximo_exclusivo" in faixa:
            if minimo <= score < float(faixa["maximo_exclusivo"]):
                return faixa["nivel"]
        elif minimo <= score <= float(faixa["maximo_inclusivo"]):
            return faixa["nivel"]
    raise CatalogoIncompativelError(f"Nenhuma faixa cobre o score {score}.")


def chave_plano(item: dict, status: str) -> tuple:
    criticidade = item["criticidade"]
    if criticidade == "BLOQUEADOR":
        grupo = 0 if status in {"NAO_INICIADO", "NAO_SEI"} else 1
    elif criticidade == "ESSENCIAL":
        grupo = 2 if status in {"NAO_INICIADO", "NAO_SEI"} else 3
    else:
        grupo = 4
    prioridade = {"ALTA": 0, "MEDIA": 1, "BAIXA": 2}
    acao = item["acao_quando_pendente"]
    return (
        grupo,
        prioridade[acao["prioridade"]],
        item["dimensao"],
        int(item["ordem"]),
        item["codigo"],
    )


class MotorDiagnostico:
    def __init__(
        self,
        caminho_catalogo: Path = CATALOGO_PADRAO,
        caminho_regras: Path = REGRAS_PADRAO,
    ) -> None:
        self.catalogo = CatalogoChecklist.model_validate(carregar_json(caminho_catalogo))
        self.regras = carregar_json(caminho_regras)
        self._validar_configuracao()
        self.itens = {item.codigo: item.model_dump() for item in self.catalogo.itens}

    def _validar_configuracao(self) -> None:
        if self.catalogo.versao != self.regras.get("versao"):
            raise CatalogoIncompativelError("Catálogo e regras possuem versões diferentes.")
        fatores = self.regras.get("status_resposta", {})
        esperados = {"CONCLUIDO", "EM_ANDAMENTO", "NAO_INICIADO", "NAO_SEI"}
        if set(fatores) != esperados:
            raise CatalogoIncompativelError("As regras não cobrem todos os status de resposta.")
        pesos = self.regras.get("pesos_criticidade", {})
        for item in self.catalogo.itens:
            if item.peso != pesos.get(item.criticidade):
                raise CatalogoIncompativelError(f"Peso incompatível no item {item.codigo}.")

    def calcular(
        self,
        entrada: RegistrarRespostasRequest | dict,
        mercados_escolhidos: list[str] | None = None,
        exigir_todas_respostas: bool = True,
    ) -> ResultadoDiagnostico:
        respostas = (
            entrada
            if isinstance(entrada, RegistrarRespostasRequest)
            else RegistrarRespostasRequest.model_validate(entrada)
        )
        if respostas.catalogo_versao != self.catalogo.versao:
            raise CatalogoIncompativelError(
                f"Versão recebida {respostas.catalogo_versao} difere do catálogo {self.catalogo.versao}."
            )

        por_codigo = {resposta.item_codigo: resposta for resposta in respostas.respostas}
        desconhecidos = sorted(set(por_codigo) - set(self.itens))
        if desconhecidos:
            raise CatalogoIncompativelError(
                "Itens não encontrados no catálogo: " + ", ".join(desconhecidos)
            )

        ativos = [item for item in self.catalogo.itens if item.ativo]
        ausentes = sorted(item.codigo for item in ativos if item.codigo not in por_codigo)
        if exigir_todas_respostas and ausentes:
            raise RespostasIncompletasError(
                "Faltam respostas para: " + ", ".join(ausentes)
            )

        fatores = self.regras["status_resposta"]
        numerador_geral = 0.0
        denominador_geral = 0.0
        acumulado_dimensoes = {
            dimensao: {"numerador": 0.0, "denominador": 0.0, "aplicaveis": 0, "concluidos": 0}
            for dimensao in self.catalogo.dimensoes
        }
        bloqueadores = []
        pendencias = []

        for item_model in ativos:
            resposta = por_codigo.get(item_model.codigo)
            if resposta is None:
                continue
            item = item_model.model_dump()
            fator = fatores[resposta.status]
            if fator is None:
                continue

            peso = float(item["peso"])
            numerador_geral += peso * float(fator)
            denominador_geral += peso
            dim = acumulado_dimensoes[item["dimensao"]]
            dim["numerador"] += peso * float(fator)
            dim["denominador"] += peso
            dim["aplicaveis"] += 1
            if resposta.status == "CONCLUIDO":
                dim["concluidos"] += 1

            if item["criticidade"] == "BLOQUEADOR" and resposta.status != "CONCLUIDO":
                bloqueadores.append(
                    BloqueadorDiagnostico(
                        codigo=item["codigo"],
                        status=resposta.status,
                        mensagem=(
                            f"{item['pergunta']} Situação informada: {resposta.status}."
                        ),
                    )
                )

            if resposta.status != "CONCLUIDO":
                pendencias.append((item, resposta.status))

        score_geral = 0.0 if denominador_geral == 0 else arredondar(
            100 * numerador_geral / denominador_geral
        )

        scores_dimensoes = []
        for dimensao in self.catalogo.dimensoes:
            dados = acumulado_dimensoes[dimensao]
            score = 0.0 if dados["denominador"] == 0 else arredondar(
                100 * dados["numerador"] / dados["denominador"]
            )
            scores_dimensoes.append(
                ScoreDimensao(
                    dimensao=dimensao,
                    score=score,
                    itens_aplicaveis=dados["aplicaveis"],
                    itens_concluidos=dados["concluidos"],
                )
            )

        pendencias.sort(key=lambda par: chave_plano(par[0], par[1]))
        plano_acao = []
        for ordem, (item, status) in enumerate(pendencias, start=1):
            acao = item["acao_quando_pendente"]
            plano_acao.append(
                AcaoPlano(
                    ordem=ordem,
                    item_codigo=item["codigo"],
                    dimensao=item["dimensao"],
                    criticidade=item["criticidade"],
                    status=status,
                    titulo=acao["titulo"],
                    descricao=acao["descricao"],
                    prioridade=acao["prioridade"],
                )
            )

        mercados = mercados_escolhidos or []
        if len(mercados) > int(self.regras["mercados_diagnostico_maximo"]):
            raise ErroDiagnostico("O Diagnóstico permite no máximo três países.")
        if len(mercados) != len(set(mercados)):
            raise ErroDiagnostico("Os países selecionados não podem se repetir.")
        pesquisas = [
            PesquisaMercadoResumo(pais_iso3=iso3, status="NAO_EXECUTADA")
            for iso3 in mercados
        ]

        possui_bloqueadores = bool(bloqueadores)
        alerta = None
        if possui_bloqueadores:
            alerta = (
                "Há pendências impeditivas no diagnóstico. Elas não bloqueiam o acesso "
                "ao Módulo Vendas, mas devem ser avaliadas antes de concluir uma exportação."
            )

        return ResultadoDiagnostico(
            catalogo_versao=self.catalogo.versao,
            score_geral=score_geral,
            nivel=nivel_prontidao(score_geral, self.regras["faixas_prontidao"]),
            scores_dimensoes=scores_dimensoes,
            possui_bloqueadores=possui_bloqueadores,
            bloqueadores=bloqueadores,
            plano_acao=plano_acao,
            pesquisas_mercado=pesquisas,
            alerta_vendas=alerta,
            bloqueia_modulo_vendas=False,
        )
