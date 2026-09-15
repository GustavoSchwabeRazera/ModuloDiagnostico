from __future__ import annotations

import os

from diagnostico.inteligencia.provedor_api_comum import (
    ErroProvedorInteligencia,
    schema_saida,
    serializar_entrada,
    system_instruction,
    validar_saida,
)
from diagnostico.inteligencia.schemas import EntradaInteligenciaMercado, SaidaInteligenciaMercado


class ProvedorGroq:
    nome = "GROQ"

    def __init__(self, api_key: str | None = None, modelo: str | None = None, cliente=None, strict: bool | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.modelo = modelo or os.getenv("EXPORTAI_GROQ_MODELO", "")
        env_strict = os.getenv("EXPORTAI_GROQ_STRUCTURED_STRICT", "false").lower() == "true"
        self.strict = env_strict if strict is None else strict
        if not self.modelo:
            raise ValueError("EXPORTAI_GROQ_MODELO não foi configurado.")
        if cliente is not None:
            self.cliente = cliente
        else:
            if not self.api_key:
                raise ValueError("GROQ_API_KEY não foi configurada.")
            try:
                from groq import Groq
            except ImportError as exc:
                raise RuntimeError("Instale groq para usar Groq.") from exc
            self.cliente = Groq(api_key=self.api_key)

    def analisar(self, entrada: EntradaInteligenciaMercado) -> SaidaInteligenciaMercado:
        messages = [
            {"role": "system", "content": system_instruction()},
            {"role": "user", "content": serializar_entrada(entrada)},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "saida_inteligencia_mercado",
                "strict": self.strict,
                "schema": schema_saida(),
            },
        }
        try:
            response = self.cliente.chat.completions.create(
                model=self.modelo,
                messages=messages,
                response_format=response_format,
                temperature=0,
                stream=False,
            )
            raw = response.choices[0].message.content
            return validar_saida(raw, entrada)
        except ErroProvedorInteligencia:
            raise
        except Exception as exc:
            raise ErroProvedorInteligencia(f"Falha controlada no Groq: {type(exc).__name__}") from exc
