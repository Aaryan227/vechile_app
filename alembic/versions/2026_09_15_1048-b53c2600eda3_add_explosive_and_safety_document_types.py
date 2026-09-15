"""add_explosive_and_safety_document_types

Revision ID: b53c2600eda3
Revises: 55f49671ceb6
Create Date: 2026-09-15 10:48:51.088544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b53c2600eda3'
down_revision: Union[str, None] = '55f49671ceb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # 1. Add all new values to PostgreSQL documenttype enum if it exists
        new_values = [
            "EXPLOSIVE_LICENSE",
            "EXPLOSIVE_VEHICLE_CERTIFICATE",
            "PESO_CERTIFICATE",
            "SAFETY_CERTIFICATE",
            "OTHER_CERTIFICATE",
            "NATIONAL_PERMIT"
        ]
        for val in new_values:
            try:
                with op.get_context().autocommit_block():
                    op.execute(f"ALTER TYPE documenttype ADD VALUE IF NOT EXISTS '{val}'")
            except Exception:
                pass

        # 2. Convert document_type column to VARCHAR(50) so role is resilient against strict DB enums
        try:
            op.execute("ALTER TABLE documents ALTER COLUMN document_type TYPE VARCHAR(50) USING document_type::text")
        except Exception:
            pass
    elif bind.dialect.name == "sqlite":
        pass


def downgrade() -> None:
    pass
