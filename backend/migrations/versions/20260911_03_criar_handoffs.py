"""Cria handoffs descartáveis. Revision ID: 20260911_03 Revises: 20260911_02"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision="20260911_03"; down_revision="20260911_02"
branch_labels=None; depends_on=None

def upgrade():
    if "jornada_handoffs" in sa.inspect(op.get_bind()).get_table_names(): return
    op.create_table("jornada_handoffs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("journey_id", sa.String(36), sa.ForeignKey("jornadas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_token_cifrado", sa.String(1000), nullable=False),
        sa.Column("destino", sa.String(500), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumido_em", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_handoffs_code_hash", "jornada_handoffs", ["code_hash"], unique=True)
    op.create_index("ix_handoffs_journey_id", "jornada_handoffs", ["journey_id"])
    op.create_index("ix_handoffs_expira_em", "jornada_handoffs", ["expira_em"])

def downgrade():
    op.drop_table("jornada_handoffs")
