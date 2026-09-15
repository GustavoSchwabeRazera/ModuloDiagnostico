from __future__ import annotations
import base64, hashlib, hmac, os, secrets, uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from sqlalchemy import delete, select, update
from diagnostico.database import criar_fabrica_sessoes
from diagnostico.handoff_models import JornadaHandoffModel

class HandoffInvalido(Exception): pass
class HandoffExpirado(Exception): pass
class HandoffConsumido(Exception): pass


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _allowed_destinations() -> set[str]:
    raw = os.getenv("EXPORTAI_HANDOFF_DESTINOS", "")
    return {item.strip().rstrip("/") for item in raw.split(",") if item.strip()}


def _validate_destination(destination: str) -> str:
    clean = destination.strip().rstrip("/")
    parsed = urlparse(clean)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
        raise HandoffInvalido("Destino deve ser uma origem HTTPS, sem caminho.")
    if clean not in _allowed_destinations():
        raise HandoffInvalido("Destino de handoff não autorizado.")
    return clean


def _secret() -> bytes:
    value = os.getenv("EXPORTAI_HANDOFF_SECRET", "")
    if len(value) < 32:
        raise RuntimeError("EXPORTAI_HANDOFF_SECRET deve ter ao menos 32 caracteres.")
    return hashlib.sha256(value.encode()).digest()


def _seal(text: str) -> str:
    raw = text.encode()
    nonce = secrets.token_bytes(16)
    key = _secret()
    stream = hashlib.sha256(key + nonce).digest()
    encrypted = bytes(b ^ stream[i % len(stream)] for i, b in enumerate(raw))
    tag = hmac.new(key, nonce + encrypted, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(nonce + tag + encrypted).decode()


def _open(value: str) -> str:
    blob = base64.urlsafe_b64decode(value.encode())
    nonce, tag, encrypted = blob[:16], blob[16:48], blob[48:]
    key = _secret()
    expected = hmac.new(key, nonce + encrypted, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise HandoffInvalido("Conteúdo de handoff inválido.")
    stream = hashlib.sha256(key + nonce).digest()
    return bytes(b ^ stream[i % len(stream)] for i, b in enumerate(encrypted)).decode()


class ServicoHandoff:
    def __init__(self, fabrica=None):
        self.fabrica = fabrica or criar_fabrica_sessoes()

    def criar(self, journey_id: str, resume_token: str, destino: str) -> dict:
        destino = _validate_destination(destino)
        code = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        ttl = min(max(int(os.getenv("EXPORTAI_HANDOFF_TTL_SEGUNDOS", "120")), 30), 600)
        row = JornadaHandoffModel(
            id=str(uuid.uuid4()), code_hash=_hash(code), journey_id=journey_id,
            resume_token_cifrado=_seal(resume_token), destino=destino,
            criado_em=now, expira_em=now + timedelta(seconds=ttl), consumido_em=None,
        )
        with self.fabrica() as session:
            session.add(row); session.commit()
        return {"handoff_code": code, "destino": destino, "expira_em": row.expira_em}

    def trocar(self, code: str) -> dict:
        now = datetime.now(timezone.utc)
        digest = _hash(code)
        with self.fabrica() as session:
            row = session.scalar(select(JornadaHandoffModel).where(JornadaHandoffModel.code_hash == digest))
            if not row: raise HandoffInvalido("Código de handoff inválido.")
            expires = row.expira_em if row.expira_em.tzinfo else row.expira_em.replace(tzinfo=timezone.utc)
            if expires <= now: raise HandoffExpirado("Código de handoff expirado.")
            result = session.execute(
                update(JornadaHandoffModel)
                .where(JornadaHandoffModel.id == row.id, JornadaHandoffModel.consumido_em.is_(None))
                .values(consumido_em=now)
            )
            if result.rowcount != 1:
                session.rollback(); raise HandoffConsumido("Código de handoff já utilizado.")
            token = _open(row.resume_token_cifrado)
            session.commit()
            return {"journey_id": row.journey_id, "resume_token": token, "destino": row.destino}

    def limpar(self) -> int:
        now = datetime.now(timezone.utc)
        with self.fabrica() as session:
            result = session.execute(delete(JornadaHandoffModel).where(JornadaHandoffModel.expira_em < now))
            session.commit(); return int(result.rowcount or 0)
