from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from diagnostico.database import Base


class DiagnosticoModel(Base):
    __tablename__ = "diagnosticos"

    diagnostico_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    catalogo_versao: Mapped[str] = mapped_column(String(30), nullable=False)
    produto_json: Mapped[str] = mapped_column(Text, nullable=False)
    mercados_basico_json: Mapped[str] = mapped_column(Text, nullable=False)
    mercados_escolhidos_json: Mapped[str] = mapped_column(Text, nullable=False)
    respostas_json: Mapped[str] = mapped_column(Text, nullable=False)
    resultado_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    pesquisa_assistida_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
