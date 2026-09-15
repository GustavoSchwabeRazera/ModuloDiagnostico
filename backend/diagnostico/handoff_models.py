from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from diagnostico.database import Base

class JornadaHandoffModel(Base):
    __tablename__ = "jornada_handoffs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    journey_id: Mapped[str] = mapped_column(String(36), ForeignKey("jornadas.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_token_cifrado: Mapped[str] = mapped_column(String(1000), nullable=False)
    destino: Mapped[str] = mapped_column(String(500), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    consumido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
