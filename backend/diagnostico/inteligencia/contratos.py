from __future__ import annotations

from abc import ABC, abstractmethod

from diagnostico.inteligencia.schemas import EntradaInteligenciaMercado, SaidaInteligenciaMercado


class ProvedorInteligenciaDiagnostico(ABC):
    """Interface única para Ollama e futuros provedores de IA."""

    nome: str

    @abstractmethod
    def analisar(self, entrada: EntradaInteligenciaMercado) -> SaidaInteligenciaMercado:
        raise NotImplementedError
