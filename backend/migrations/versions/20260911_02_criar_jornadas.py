"""Cria jornadas anônimas.

Revision ID: 20260911_02
Revises: 20260911_01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260911_02"
down_revision: Union[str, None] = "20260911_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "jornadas" in inspector.get_table_names():
        return
    op.create_table(
        "jornadas",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("resume_token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("produto_json", sa.Text(), nullable=False),
        sa.Column("mercados_basico_json", sa.Text(), nullable=False),
        sa.Column("mercados_escolhidos_json", sa.Text(), nullable=False),
        sa.Column("diagnostico_id", sa.String(length=36), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultimo_acesso_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_jornadas_status", "jornadas", ["status"])
    op.create_index("ix_jornadas_diagnostico_id", "jornadas", ["diagnostico_id"])
    op.create_index("ix_jornadas_expira_em", "jornadas", ["expira_em"])


def downgrade() -> None:
    op.drop_index("ix_jornadas_expira_em", table_name="jornadas")
    op.drop_index("ix_jornadas_diagnostico_id", table_name="jornadas")
    op.drop_index("ix_jornadas_status", table_name="jornadas")
    op.drop_table("jornadas")
