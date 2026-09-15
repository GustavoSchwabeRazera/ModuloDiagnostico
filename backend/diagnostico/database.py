from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_PATH = (BACKEND_DIR / "data" / "exportai_diagnostico.db").resolve()
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


def obter_database_url() -> str:
    """Usa PostgreSQL quando configurado e SQLite como fallback local."""
    raw = (
        os.getenv("EXPORTAI_DATABASE_URL")
        or os.getenv("EXPORTAI_DIAGNOSTICO_DATABASE_URL")
        or DEFAULT_DATABASE_URL
    ).strip()
    # Alguns provedores ainda entregam postgres://; SQLAlchemy espera postgresql://.
    if raw.startswith("postgres://"):
        raw = "postgresql+psycopg://" + raw[len("postgres://"):]
    elif raw.startswith("postgresql://"):
        raw = "postgresql+psycopg://" + raw[len("postgresql://"):]
    return raw


def criar_engine(database_url: str | None = None) -> Engine:
    url = database_url or obter_database_url()
    backend = make_url(url).get_backend_name()
    kwargs: dict = {"pool_pre_ping": True}
    if backend == "sqlite":
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update({"pool_size": 5, "max_overflow": 10, "pool_recycle": 1800})
    return create_engine(url, **kwargs)


def criar_fabrica_sessoes(engine_alvo: Engine | None = None):
    """Cria uma fábrica de sessões compatível com o repositório existente.

    O parâmetro permite que testes usem engines SQLite temporárias sem alterar
    a engine global. Em produção, sem parâmetro, usa a engine configurada por
    EXPORTAI_DATABASE_URL.
    """
    alvo = engine_alvo or engine
    return sessionmaker(
        bind=alvo,
        autoflush=False,
        expire_on_commit=False,
    )


class Base(DeclarativeBase):
    pass


DATABASE_URL = obter_database_url()
engine = criar_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def criar_tabelas() -> None:
    # Compatibilidade local. Em produção, use: alembic upgrade head.
    from diagnostico import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
