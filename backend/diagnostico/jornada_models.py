from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from diagnostico.database import Base


class JornadaModel(Base):
    __tablename__ = "jornadas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    resume_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    produto_json: Mapped[str] = mapped_column(Text, nullable=False)
    mercados_basico_json: Mapped[str] = mapped_column(Text, nullable=False)
    mercados_escolhidos_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    diagnostico_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ultimo_acesso_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
