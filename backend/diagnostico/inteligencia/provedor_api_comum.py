from __future__ import annotations

import json
from typing import Any

from diagnostico.inteligencia.schemas import EntradaInteligenciaMercado, SaidaInteligenciaMercado


class ErroProvedorInteligencia(RuntimeError):
    pass


def serializar_entrada(entrada: EntradaInteligenciaMercado) -> str:
    if hasattr(entrada, "model_dump"):
        data = entrada.model_dump(mode="json")
    elif isinstance(entrada, dict):
        data = entrada
    else:
        raise TypeError("Entrada de inteligência inválida.")
    return json.dumps(data, ensure_ascii=False, indent=2)


def schema_saida() -> dict[str, Any]:
    return SaidaInteligenciaMercado.model_json_schema()


def validar_saida(raw: str | dict | SaidaInteligenciaMercado, entrada: EntradaInteligenciaMercado) -> SaidaInteligenciaMercado:
    if isinstance(raw, SaidaInteligenciaMercado):
        result = raw
    elif isinstance(raw, dict):
        result = SaidaInteligenciaMercado.model_validate(raw)
    elif isinstance(raw, str) and raw.strip():
        result = SaidaInteligenciaMercado.model_validate_json(raw)
    else:
        raise ErroProvedorInteligencia("O provedor retornou conteúdo vazio.")

    entrada_data = entrada.model_dump(mode="json") if hasattr(entrada, "model_dump") else entrada
    requested_country = entrada_data.get("pais", {}).get("iso3") or entrada_data.get("pais_iso3")
    returned_country = getattr(result, "pais_iso3", None)
    if requested_country and returned_country and requested_country != returned_country:
        raise ErroProvedorInteligencia("O provedor devolveu país diferente do solicitado.")

    evidence_ids = {
        item.get("evidencia_id")
        for item in entrada_data.get("evidencias", [])
        if isinstance(item, dict) and item.get("evidencia_id")
    }
    for requirement in getattr(result, "requisitos", []) or []:
        refs = getattr(requirement, "fontes_ids", []) or []
        unknown = set(refs) - evidence_ids
        if unknown:
            raise ErroProvedorInteligencia(
                "O provedor citou evidências inexistentes: " + ", ".join(sorted(unknown))
            )
    return result


def system_instruction() -> str:
    return (
        "Use exclusivamente as evidências fornecidas. Não use memória geral para afirmar obrigações. "
        "Não invente fontes, regras, certificações ou autoridades. Não declare conformidade. "
        "Associe cada requisito aos IDs das evidências recebidas. Quando a evidência for insuficiente, "
        "registre a lacuna em nao_confirmados. Não calcule nem altere score, peso, criticidade, "
        "nível de prontidão ou acesso ao Módulo Vendas. Responda somente no schema solicitado."
    )
