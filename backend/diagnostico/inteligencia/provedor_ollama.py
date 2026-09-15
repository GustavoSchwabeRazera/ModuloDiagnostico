from __future__ import annotations

import json
import os
from typing import Any

from pydantic import ValidationError

from diagnostico.inteligencia.contratos import ProvedorInteligenciaDiagnostico
from diagnostico.inteligencia.prompts import PROMPT_SISTEMA_DIAGNOSTICO
from diagnostico.inteligencia.schemas import EntradaInteligenciaMercado, SaidaInteligenciaMercado


class ErroProvedorOllama(RuntimeError):
    pass


class ProvedorInteligenciaOllama(ProvedorInteligenciaDiagnostico):
    nome = "OLLAMA"

    def __init__(self, cliente: Any | None = None, modelo: str | None = None) -> None:
        self.modelo = (modelo or os.getenv("EXPORTAI_DIAGNOSTICO_IA_MODELO", "")).strip()
        if not self.modelo:
            raise ErroProvedorOllama(
                "Defina EXPORTAI_DIAGNOSTICO_IA_MODELO antes de habilitar o Ollama."
            )
        self.host = os.getenv(
            "EXPORTAI_DIAGNOSTICO_OLLAMA_HOST", "http://127.0.0.1:11434"
        ).strip()
        self.timeout = float(os.getenv("EXPORTAI_DIAGNOSTICO_OLLAMA_TIMEOUT", "90"))
        self.temperature = float(
            os.getenv("EXPORTAI_DIAGNOSTICO_OLLAMA_TEMPERATURE", "0")
        )
        self.cliente = cliente or self._criar_cliente()

    def _criar_cliente(self):
        try:
            from ollama import Client
        except ImportError as exc:
            raise ErroProvedorOllama(
                "A biblioteca ollama não está instalada no ambiente Python."
            ) from exc
        return Client(host=self.host, timeout=self.timeout)

    @staticmethod
    def _evidencias_para_prompt(entrada: EntradaInteligenciaMercado) -> list[dict]:
        return [
            {
                "evidencia_id": e.evidencia_id,
                "fonte_titulo": e.fonte_titulo,
                "fonte_url": str(e.fonte_url),
                "tipo_fonte": e.tipo_fonte,
                "consultado_em": e.consultado_em.isoformat(),
                "trecho": e.trecho,
                "idioma": e.idioma,
            }
            for e in entrada.evidencias
        ]

    def _prompt_usuario(self, entrada: EntradaInteligenciaMercado) -> str:
        carga = {
            "produto": entrada.produto.model_dump(),
            "pais": entrada.pais.model_dump(),
            "evidencias": self._evidencias_para_prompt(entrada),
            "instrucoes": {
                "pais_iso3_obrigatorio": entrada.pais.iso3,
                "evidencias_permitidas": [e.evidencia_id for e in entrada.evidencias],
                "sem_evidencia": "Não afirme requisito; registre como não confirmado.",
            },
        }
        return (
            "Analise a carga abaixo usando exclusivamente as evidências nela contidas. "
            "Retorne somente JSON aderente ao schema fornecido.\n\n"
            + json.dumps(carga, ensure_ascii=False, indent=2)
        )

    @staticmethod
    def _conteudo_resposta(resposta: Any) -> str:
        if hasattr(resposta, "message"):
            message = resposta.message
            if hasattr(message, "content"):
                return message.content
            if isinstance(message, dict):
                return message.get("content", "")
        if isinstance(resposta, dict):
            message = resposta.get("message", {})
            return message.get("content", "") if isinstance(message, dict) else ""
        return ""

    def analisar(self, entrada: EntradaInteligenciaMercado) -> SaidaInteligenciaMercado:
        if not entrada.evidencias:
            return SaidaInteligenciaMercado(
                pais_iso3=entrada.pais.iso3,
                status="CONCLUIDA_COM_RESSALVAS",
                resumo="Nenhuma evidência controlada foi fornecida para interpretação.",
                requisitos=[],
                nao_confirmados=[
                    "Não foi possível confirmar requisitos sem evidências recuperadas."
                ],
                alertas=["Execute a recuperação direcionada de fontes antes da análise."],
                evidencias_disponiveis=[],
            )

        schema = SaidaInteligenciaMercado.model_json_schema()
        try:
            resposta = self.cliente.chat(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": PROMPT_SISTEMA_DIAGNOSTICO},
                    {"role": "user", "content": self._prompt_usuario(entrada)},
                ],
                format=schema,
                options={"temperature": self.temperature},
                stream=False,
            )
            conteudo = self._conteudo_resposta(resposta)
            if not conteudo:
                raise ErroProvedorOllama("O Ollama retornou conteúdo vazio.")
            saida = SaidaInteligenciaMercado.model_validate_json(conteudo)
        except ErroProvedorOllama:
            raise
        except (ValidationError, json.JSONDecodeError) as exc:
            raise ErroProvedorOllama(
                "A saída do Ollama não respeitou o contrato estruturado."
            ) from exc
        except Exception as exc:
            raise ErroProvedorOllama(f"Falha ao consultar o Ollama: {exc}") from exc

        if saida.pais_iso3 != entrada.pais.iso3:
            raise ErroProvedorOllama("O Ollama retornou um país diferente do solicitado.")

        permitidas = {e.evidencia_id for e in entrada.evidencias}
        if set(saida.evidencias_disponiveis) != permitidas:
            raise ErroProvedorOllama(
                "A saída alterou a lista de evidências disponibilizadas."
            )
        return saida
