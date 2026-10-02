"""add language code indexes

Revision ID: b1bacb78de0f
Revises: 6ed1dfd2923a
Create Date: 2026-10-02 11:46:53.966798

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1bacb78de0f'
down_revision: Union[str, Sequence[str], None] = '6ed1dfd2923a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Уникальный код среди системных языков
    op.create_index(
        "uq_system_language_code",
        "languages",
        ["code"],
        unique=True,
        postgresql_where=sa.text("user_id IS NULL"),
    )

    # Уникальный код для каждого пользователя
    op.create_index(
        "uq_user_language_code",
        "languages",
        ["user_id", "code"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )


def downgrade() -> None:
    # Удаляем индекс пользовательских языков
    op.drop_index(
        "uq_user_language_code",
        table_name="languages",
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )

    # Удаляем индекс системных языков
    op.drop_index(
        "uq_system_language_code",
        table_name="languages",
        postgresql_where=sa.text("user_id IS NULL"),
    )
