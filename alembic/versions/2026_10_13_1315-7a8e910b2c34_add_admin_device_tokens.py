"""add_admin_device_tokens

Revision ID: 7a8e910b2c34
Revises: 099c6e9bf97a
Create Date: 2026-10-13 13:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '7a8e910b2c34'
down_revision: Union[str, None] = '099c6e9bf97a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'admin_device_tokens' not in existing_tables:
        op.create_table(
            'admin_device_tokens',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('device_token', sa.String(length=500), nullable=False),
            sa.Column('platform', sa.String(length=20), server_default='android', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_admin_device_tokens_id'), 'admin_device_tokens', ['id'], unique=False)
        op.create_index(op.f('ix_admin_device_tokens_user_id'), 'admin_device_tokens', ['user_id'], unique=False)
        op.create_index(op.f('ix_admin_device_tokens_device_token'), 'admin_device_tokens', ['device_token'], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'admin_device_tokens' in existing_tables:
        op.drop_index(op.f('ix_admin_device_tokens_device_token'), table_name='admin_device_tokens')
        op.drop_index(op.f('ix_admin_device_tokens_user_id'), table_name='admin_device_tokens')
        op.drop_index(op.f('ix_admin_device_tokens_id'), table_name='admin_device_tokens')
        op.drop_table('admin_device_tokens')
