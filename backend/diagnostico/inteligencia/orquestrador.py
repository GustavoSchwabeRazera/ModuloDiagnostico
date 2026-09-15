from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from diagnostico.inteligencia.contratos import ProvedorInteligenciaDiagnostico
from diagnostico.inteligencia.fabrica import criar_provedor
from diagnostico.inteligencia.fontes import carregar_catalogo, transformar_documentos
from diagnostico.inteligencia.orquestrador_schemas import (
    ExecutarPesquisaAssistidaRequest,
    PesquisaPaisResultado,
    ResultadoPesquisaAssistida,
)
from diagnostico.inteligencia.schemas import (
    EntradaInteligenciaMercado,
    SaidaInteligenciaMercado,
)


class ErroOrquestracao(ValueError):
    pass


class OrquestradorPesquisaAssistida:
    def __init__(self, repositorio, provedor: ProvedorInteligenciaDiagnostico | None = None):
        self.repositorio = repositorio
        self.provedor = provedor or criar_provedor()
        self.catalogo = carregar_catalogo()

    @staticmethod
    def _mercado_por_iso3(sessao: dict) -> dict[str, dict]:
        return {mercado["iso3"]: mercado for mercado in sessao["mercados_basico"]}

    @staticmethod
    def _analise_erro(pais_iso3: str, mensagem: str) -> SaidaInteligenciaMercado:
        return SaidaInteligenciaMercado(
            pais_iso3=pais_iso3,
            status="ERRO",
            resumo="A interpretação das evidências não pôde ser concluída.",
            requisitos=[],
            nao_confirmados=[],
            alertas=[mensagem],
            evidencias_disponiveis=[],
        )

    def executar(
        self,
        diagnostico_id: str,
        entrada: ExecutarPesquisaAssistidaRequest | dict,
    ) -> ResultadoPesquisaAssistida:
        requisicao = (
            entrada
            if isinstance(entrada, ExecutarPesquisaAssistidaRequest)
            else ExecutarPesquisaAssistidaRequest.model_validate(entrada)
        )
        sessao = self.repositorio.obter(diagnostico_id)
        if sessao is None:
            raise ErroOrquestracao("Sessão de diagnóstico não encontrada.")

        escolhidos = list(sessao["mercados_escolhidos"])
        if not 1 <= len(escolhidos) <= 3:
            raise ErroOrquestracao("A sessão deve possuir de um a três países selecionados.")

        documentos = {item.pais_iso3: item.documentos for item in requisicao.documentos_por_pais}
        extras = sorted(set(documentos) - set(escolhidos))
        if extras:
            raise ErroOrquestracao(
                "Foram enviados documentos para países não selecionados: " + ", ".join(extras)
            )

        mercados = self._mercado_por_iso3(sessao)
        resultado_deterministico = deepcopy(sessao.get("resultado"))
        score_antes = (
            resultado_deterministico.get("score_geral")
            if resultado_deterministico is not None
            else None
        )
        resultados = []

        for iso3 in escolhidos:
            mercado = mercados.get(iso3)
            if mercado is None:
                raise ErroOrquestracao(f"Mercado {iso3} não existe nos dados do Módulo Básico.")

            recuperacao = transformar_documentos(
                self.catalogo,
                iso3,
                sessao["produto"]["hs6"],
                sessao["produto"]["descricao"],
                documentos.get(iso3, []),
            )
            entrada_ia = EntradaInteligenciaMercado(
                produto=sessao["produto"],
                pais={"iso3": iso3, "nome": mercado["nome"]},
                evidencias=recuperacao.evidencias,
            )
            try:
                analise = self.provedor.analisar(entrada_ia)
                erro = None
            except Exception as exc:
                erro = str(exc)
                analise = self._analise_erro(iso3, erro)

            resultados.append(
                PesquisaPaisResultado(
                    pais_iso3=iso3,
                    status=analise.status,
                    evidencias_encontradas=len(recuperacao.evidencias),
                    descartes=recuperacao.descartes,
                    analise=analise,
                    erro=erro,
                )
            )

        concluidos = sum(r.status in {"CONCLUIDA", "CONCLUIDA_COM_RESSALVAS"} for r in resultados)
        erros = sum(r.status == "ERRO" for r in resultados)
        executado_em = datetime.now(timezone.utc)
        payload = ResultadoPesquisaAssistida(
            diagnostico_id=diagnostico_id,
            provedor=self.provedor.nome,
            paises_solicitados=len(escolhidos),
            paises_concluidos=concluidos,
            paises_com_erro=erros,
            resultados=resultados,
            score_geral_antes=score_antes,
            score_geral_depois=score_antes,
            pontuacao_preservada=True,
            executado_em=executado_em,
        )

        sessao["pesquisa_assistida"] = payload.model_dump(mode="json")
        if resultado_deterministico is not None:
            resumo_por_pais = {r.pais_iso3: r for r in resultados}
            resultado_deterministico["pesquisas_mercado"] = [
                {
                    "pais_iso3": iso3,
                    "status": resumo_por_pais[iso3].status,
                    "requisitos_confirmados": sum(
                        req.status_evidencia == "CONFIRMADO_EM_FONTE_OFICIAL"
                        for req in resumo_por_pais[iso3].analise.requisitos
                    ),
                    "requisitos_com_ressalvas": sum(
                        req.status_evidencia == "ENCONTRADO_EM_FONTE_COMPLEMENTAR"
                        for req in resumo_por_pais[iso3].analise.requisitos
                    ),
                    "nao_confirmados": len(resumo_por_pais[iso3].analise.nao_confirmados),
                }
                for iso3 in escolhidos
            ]
            sessao["resultado"] = resultado_deterministico
        sessao["atualizado_em"] = executado_em
        self.repositorio.salvar(diagnostico_id, sessao)

        sessao_final = self.repositorio.obter(diagnostico_id)
        score_depois = (
            sessao_final.get("resultado", {}).get("score_geral")
            if sessao_final and sessao_final.get("resultado") is not None
            else None
        )
        if score_depois != score_antes:
            raise RuntimeError("A pesquisa assistida alterou a pontuação determinística.")
        return payload
