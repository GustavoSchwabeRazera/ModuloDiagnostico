from __future__ import annotations

from copy import deepcopy
from threading import RLock


class RepositorioDiagnosticosMemoria:
    """Armazenamento temporário. Os dados são perdidos ao reiniciar a API."""

    def __init__(self) -> None:
        self._sessoes: dict[str, dict] = {}
        self._lock = RLock()

    def criar(self, sessao: dict) -> dict:
        with self._lock:
            identificador = sessao["diagnostico_id"]
            self._sessoes[identificador] = deepcopy(sessao)
            return deepcopy(sessao)

    def obter(self, identificador: str) -> dict | None:
        with self._lock:
            sessao = self._sessoes.get(identificador)
            return deepcopy(sessao) if sessao is not None else None

    def salvar(self, identificador: str, sessao: dict) -> dict:
        with self._lock:
            if identificador not in self._sessoes:
                raise KeyError(identificador)
            self._sessoes[identificador] = deepcopy(sessao)
            return deepcopy(sessao)

    def limpar(self) -> None:
        with self._lock:
            self._sessoes.clear()


repositorio_diagnosticos = RepositorioDiagnosticosMemoria()
