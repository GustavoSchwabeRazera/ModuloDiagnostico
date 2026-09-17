"""Corrige a chave primária criada com nome legado em produção.

Revision ID: 20260917_04
Revises: 20260911_03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260917_04"
down_revision: Union[str, None] = "20260911_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Renomeia `id` para `diagnostico_id` sem perder sessões existentes."""
    inspector = sa.inspect(op.get_bind())
    if "diagnosticos" not in inspector.get_table_names():
        return

    colunas = {coluna["name"] for coluna in inspector.get_columns("diagnosticos")}
    if "id" in colunas and "diagnostico_id" not in colunas:
        op.alter_column(
            "diagnosticos",
            "id",
            new_column_name="diagnostico_id",
            existing_type=sa.String(length=36),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "diagnosticos" not in inspector.get_table_names():
        return

    colunas = {coluna["name"] for coluna in inspector.get_columns("diagnosticos")}
    if "diagnostico_id" in colunas and "id" not in colunas:
        op.alter_column(
            "diagnosticos",
            "diagnostico_id",
            new_column_name="id",
            existing_type=sa.String(length=36),
        )
