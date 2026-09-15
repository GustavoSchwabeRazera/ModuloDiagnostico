from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from diagnostico.jornada_repository import RepositorioJornadas, repositorio_jornadas


class JornadaNaoEncontrada(Exception):
    pass


class TokenJornadaInvalido(Exception):
    pass


class JornadaExpirada(Exception):
    pass


class RegraJornadaInvalida(Exception):
    pass


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def retention_hours() -> int:
    raw = os.getenv("EXPORTAI_SESSAO_RETENCAO_HORAS", "24")
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("EXPORTAI_SESSAO_RETENCAO_HORAS deve ser inteiro.") from exc
    return min(max(value, 1), 168)


class ServicoJornadas:
    def __init__(self, repo: RepositorioJornadas | None = None):
        self.repo = repo or repositorio_jornadas

    def criar(self, produto: dict, mercados_basico: list[dict]) -> tuple[dict, str]:
        now = datetime.now(timezone.utc)
        token = secrets.token_urlsafe(32)
        data = {
            "journey_id": str(uuid.uuid4()),
            "resume_token_hash": token_hash(token),
            "status": "CRIADA",
            "produto": produto,
            "mercados_basico": mercados_basico,
            "mercados_escolhidos": [],
            "diagnostico_id": None,
            "criado_em": now,
            "atualizado_em": now,
            "ultimo_acesso_em": None,
            "expira_em": now + timedelta(hours=retention_hours()),
        }
        self.repo.criar(data)
        return data, token

    def autenticar(self, journey_id: str, token: str) -> dict:
        data = self.repo.obter(journey_id)
        if not data:
            raise JornadaNaoEncontrada("Jornada não encontrada.")
        now = datetime.now(timezone.utc)
        expires = data["expira_em"]
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= now:
            raise JornadaExpirada("A jornada expirou e não pode mais ser retomada.")
        candidate = token_hash(token)
        if not secrets.compare_digest(candidate, data["resume_token_hash"]):
            raise TokenJornadaInvalido("Token de retomada inválido.")
        data["ultimo_acesso_em"] = now
        data["atualizado_em"] = now
        self.repo.salvar(data)
        return data

    def selecionar_mercados(self, data: dict, mercados: list[str]) -> dict:
        available = {item["iso3"] for item in data["mercados_basico"]}
        outside = sorted(set(mercados) - available)
        if outside:
            raise RegraJornadaInvalida(
                "Mercados não recebidos do Módulo Básico: " + ", ".join(outside)
            )
        data["mercados_escolhidos"] = mercados
        data["status"] = "MERCADOS_SELECIONADOS"
        data["atualizado_em"] = datetime.now(timezone.utc)
        self.repo.salvar(data)
        return data

    def associar_diagnostico(self, data: dict, diagnostico_id: str) -> dict:
        data["diagnostico_id"] = diagnostico_id
        data["status"] = "DIAGNOSTICO_ASSOCIADO"
        data["atualizado_em"] = datetime.now(timezone.utc)
        self.repo.salvar(data)
        return data

    @staticmethod
    def public(data: dict) -> dict:
        return {k: v for k, v in data.items() if k != "resume_token_hash"}

    @staticmethod
    def diagnostic_payload(data: dict) -> dict:
        if not data["mercados_escolhidos"]:
            raise RegraJornadaInvalida("Selecione de 1 a 3 mercados antes de preparar o diagnóstico.")
        return {
            "produto": data["produto"],
            "mercados_basico": data["mercados_basico"],
            "mercados_escolhidos": data["mercados_escolhidos"],
        }
