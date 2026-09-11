"""add_master_to_userrole_enum

Revision ID: 55f49671ceb6
Revises: ac4798419be6
Create Date: 2026-09-11 14:34:05.233205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55f49671ceb6'
down_revision: Union[str, None] = 'ac4798419be6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # 1. Add values to PostgreSQL enum if userrole enum type exists
        try:
            with op.get_context().autocommit_block():
                op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'MASTER'")
                op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'master'")
        except Exception:
            pass

        # 2. Convert role column to VARCHAR(20) so role is resilient against strict DB enums
        try:
            op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20) USING role::text")
        except Exception:
            pass
    elif bind.dialect.name == "sqlite":
        pass


def downgrade() -> None:
    pass
