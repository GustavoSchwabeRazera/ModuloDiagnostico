from __future__ import annotations
import os, uuid
from urllib.parse import urlparse
from fastapi import Request

DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://exportai-brazil.netlify.app",
    "https://export-recommend-wiz.lovable.app",
]

def cors_origins() -> list[str]:
    raw = os.getenv("EXPORTAI_CORS_ORIGINS", ",".join(DEFAULT_ORIGINS))
    origins = [x.strip().rstrip("/") for x in raw.split(",") if x.strip()]
    if "*" in origins: raise RuntimeError("CORS wildcard não é permitido.")
    return origins


def validate_production() -> None:
    if os.getenv("EXPORTAI_AMBIENTE", "DESENVOLVIMENTO").upper() != "PRODUCAO": return
    db = os.getenv("EXPORTAI_DATABASE_URL", "")
    if not db.startswith(("postgresql://", "postgresql+psycopg://", "postgres://")):
        raise RuntimeError("Produção exige PostgreSQL.")
    if os.getenv("EXPORTAI_DIAGNOSTICO_IA_PROVEDOR", "DESATIVADO").upper() == "OLLAMA":
        raise RuntimeError("OLLAMA não é permitido em produção.")
    if len(os.getenv("EXPORTAI_HANDOFF_SECRET", "")) < 32:
        raise RuntimeError("Produção exige EXPORTAI_HANDOFF_SECRET forte.")

async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return response
