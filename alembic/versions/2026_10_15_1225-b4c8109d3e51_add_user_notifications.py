"""add_user_notifications

Revision ID: b4c8109d3e51
Revises: 7a8e910b2c34
Create Date: 2026-10-15 12:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = 'b4c8109d3e51'
down_revision: Union[str, None] = '7a8e910b2c34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'user_notifications' not in existing_tables:
        op.create_table(
            'user_notifications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('notification_type', sa.String(length=50), nullable=True),
            sa.Column('data_payload', sa.JSON(), nullable=True),
            sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_notifications_id'), 'user_notifications', ['id'], unique=False)
        op.create_index(op.f('ix_user_notifications_user_id'), 'user_notifications', ['user_id'], unique=False)
        op.create_index(op.f('ix_user_notifications_notification_type'), 'user_notifications', ['notification_type'], unique=False)
        op.create_index(op.f('ix_user_notifications_is_read'), 'user_notifications', ['is_read'], unique=False)
        op.create_index(op.f('ix_user_notifications_created_at'), 'user_notifications', ['created_at'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'user_notifications' in existing_tables:
        op.drop_index(op.f('ix_user_notifications_created_at'), table_name='user_notifications')
        op.drop_index(op.f('ix_user_notifications_is_read'), table_name='user_notifications')
        op.drop_index(op.f('ix_user_notifications_notification_type'), table_name='user_notifications')
        op.drop_index(op.f('ix_user_notifications_user_id'), table_name='user_notifications')
        op.drop_index(op.f('ix_user_notifications_id'), table_name='user_notifications')
        op.drop_table('user_notifications')
