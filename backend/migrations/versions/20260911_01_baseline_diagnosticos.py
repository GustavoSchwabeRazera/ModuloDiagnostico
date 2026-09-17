"""Baseline da tabela de diagnósticos.

Revision ID: 20260911_01
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260911_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "diagnosticos" in inspector.get_table_names():
        return
    op.create_table(
        "diagnosticos",
        sa.Column("diagnostico_id", sa.String(length=36), primary_key=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("catalogo_versao", sa.String(length=30), nullable=False),
        sa.Column("produto_json", sa.Text(), nullable=False),
        sa.Column("mercados_basico_json", sa.Text(), nullable=False),
        sa.Column("mercados_escolhidos_json", sa.Text(), nullable=False),
        sa.Column("respostas_json", sa.Text(), nullable=False),
        sa.Column("resultado_json", sa.Text(), nullable=True),
        sa.Column("pesquisa_assistida_json", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diagnosticos_status", "diagnosticos", ["status"])
    op.create_index("ix_diagnosticos_atualizado_em", "diagnosticos", ["atualizado_em"])


def downgrade() -> None:
    op.drop_index("ix_diagnosticos_atualizado_em", table_name="diagnosticos")
    op.drop_index("ix_diagnosticos_status", table_name="diagnosticos")
    op.drop_table("diagnosticos")
