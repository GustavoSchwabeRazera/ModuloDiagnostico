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


class ProvedorGemini:
    nome = "GEMINI"

    def __init__(self, api_key: str | None = None, modelo: str | None = None, cliente=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.modelo = modelo or os.getenv("EXPORTAI_GEMINI_MODELO", "")
        if not self.modelo:
            raise ValueError("EXPORTAI_GEMINI_MODELO não foi configurado.")
        if cliente is not None:
            self.cliente = cliente
        else:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY não foi configurada.")
            try:
                from google import genai
            except ImportError as exc:
                raise RuntimeError("Instale google-genai para usar Gemini.") from exc
            self.cliente = genai.Client(api_key=self.api_key)

    def analisar(self, entrada: EntradaInteligenciaMercado) -> SaidaInteligenciaMercado:
        prompt = system_instruction() + "\n\nENTRADA CONTROLADA:\n" + serializar_entrada(entrada)
        try:
            response = self.cliente.models.generate_content(
                model=self.modelo,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": schema_saida(),
                    "temperature": 0,
                },
            )
            raw = getattr(response, "text", None)
            if raw is None and getattr(response, "parsed", None) is not None:
                raw = response.parsed
            return validar_saida(raw, entrada)
        except ErroProvedorInteligencia:
            raise
        except Exception as exc:
            raise ErroProvedorInteligencia(f"Falha controlada no Gemini: {type(exc).__name__}") from exc
