"""add_danda_and_green_tax_types

Revision ID: 93b6962cb4aa
Revises: b53c2600eda3
Create Date: 2026-09-15 11:28:43.108508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93b6962cb4aa'
down_revision: Union[str, None] = 'b53c2600eda3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        new_values = [
            "DANDA_TAX",
            "GREEN_TAX"
        ]
        for val in new_values:
            try:
                with op.get_context().autocommit_block():
                    op.execute(f"ALTER TYPE taxtype ADD VALUE IF NOT EXISTS '{val}'")
            except Exception:
                pass

        try:
            op.execute("ALTER TABLE vehicle_tax_records ALTER COLUMN tax_type TYPE VARCHAR(50) USING tax_type::text")
        except Exception:
            pass
    elif bind.dialect.name == "sqlite":
        pass


def downgrade() -> None:
    pass
