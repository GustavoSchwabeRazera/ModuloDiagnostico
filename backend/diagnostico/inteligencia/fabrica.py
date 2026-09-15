from __future__ import annotations

import os
import warnings

from diagnostico.inteligencia.provedor_desativado import ProvedorInteligenciaDesativado
from diagnostico.inteligencia.provedor_fallback import ProvedorComFallback


def _instanciar(nome: str):
    normalized = (nome or "DESATIVADO").strip().upper()
    if normalized == "GEMINI":
        from diagnostico.inteligencia.provedor_gemini import ProvedorGemini
        return ProvedorGemini()
    if normalized == "GROQ":
        from diagnostico.inteligencia.provedor_groq import ProvedorGroq
        return ProvedorGroq()
    if normalized in {"", "DESATIVADO", "NONE", "OFF"}:
        return ProvedorInteligenciaDesativado()
    if normalized == "OLLAMA":
        # Compatibilidade temporária, sem assumir o nome concreto da classe legada.
        # A implementação original usa um nome diferente conforme a versão do código 33.
        import inspect
        from diagnostico.inteligencia import provedor_ollama as modulo_ollama

        candidatos = []
        for _, objeto in vars(modulo_ollama).items():
            if not inspect.isclass(objeto):
                continue
            if objeto.__module__ != modulo_ollama.__name__:
                continue
            nome_declarado = getattr(objeto, "nome", None)
            if nome_declarado == "OLLAMA" or "ollama" in objeto.__name__.lower():
                candidatos.append(objeto)

        for classe in candidatos:
            try:
                instancia = classe()
            except TypeError:
                continue
            if getattr(instancia, "nome", None) == "OLLAMA":
                return instancia

        raise RuntimeError(
            "Implementação legada do OLLAMA não foi localizada no módulo provedor_ollama."
        )
    warnings.warn(
        f"Provedor desconhecido: {normalized}; usando DESATIVADO.",
        RuntimeWarning,
    )
    return ProvedorInteligenciaDesativado()


def criar_provedor_inteligencia(provedor: str | None = None, fallback: str | None = None):
    primary_name = provedor or os.getenv("EXPORTAI_DIAGNOSTICO_IA_PROVEDOR", "DESATIVADO")
    fallback_name = fallback if fallback is not None else os.getenv("EXPORTAI_DIAGNOSTICO_IA_FALLBACK", "")
    primary = _instanciar(primary_name)
    if not fallback_name or fallback_name.strip().upper() in {"", "DESATIVADO", primary_name.strip().upper()}:
        return primary
    try:
        secondary = _instanciar(fallback_name)
    except (ValueError, RuntimeError) as exc:
        warnings.warn(f"Fallback não pôde ser inicializado: {type(exc).__name__}", RuntimeWarning)
        return primary
    return ProvedorComFallback(primary, secondary)


# Aliases de compatibilidade com scripts e testes anteriores.
def criar_provedor(provedor: str | None = None, fallback: str | None = None):
    return criar_provedor_inteligencia(provedor, fallback)


def obter_provedor(provedor: str | None = None, fallback: str | None = None):
    return criar_provedor_inteligencia(provedor, fallback)
