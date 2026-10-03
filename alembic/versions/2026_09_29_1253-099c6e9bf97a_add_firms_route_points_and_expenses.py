"""add_firms_route_points_and_expenses

Revision ID: 099c6e9bf97a
Revises: 93b6962cb4aa
Create Date: 2026-09-29 12:53:56.253104

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '099c6e9bf97a'
down_revision: Union[str, None] = '93b6962cb4aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create firms table
    if 'firms' not in existing_tables:
        op.create_table(
            'firms',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=150), nullable=False),
            sa.Column('registration_number', sa.String(length=100), nullable=True),
            sa.Column('contact_person', sa.String(length=100), nullable=True),
            sa.Column('phone', sa.String(length=20), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_firms_id'), 'firms', ['id'], unique=False)
        op.create_index(op.f('ix_firms_name'), 'firms', ['name'], unique=True)

    # 2. Add firm_id to vehicles if not present
    vehicle_cols = [c['name'] for c in inspector.get_columns('vehicles')]
    if 'firm_id' not in vehicle_cols:
        op.add_column('vehicles', sa.Column('firm_id', sa.Integer(), nullable=True))
        try:
            op.create_foreign_key('fk_vehicles_firm_id_firms', 'vehicles', 'firms', ['firm_id'], ['id'], ondelete='SET NULL')
        except Exception:
            pass
        try:
            op.create_index(op.f('ix_vehicles_firm_id'), 'vehicles', ['firm_id'], unique=False)
        except Exception:
            pass

    # 3. Create route_points table
    if 'route_points' not in existing_tables:
        op.create_table(
            'route_points',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=150), nullable=False),
            sa.Column('point_type', sa.String(length=50), nullable=False, server_default='UNLOADING'),
            sa.Column('default_rtkm', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('default_rate', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('pump_station', sa.String(length=150), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_route_points_id'), 'route_points', ['id'], unique=False)
        op.create_index(op.f('ix_route_points_name'), 'route_points', ['name'], unique=True)

    # 4. Create vehicle_expenses table
    if 'vehicle_expenses' not in existing_tables:
        op.create_table(
            'vehicle_expenses',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('vehicle_id', sa.Integer(), nullable=False),
            sa.Column('trip_id', sa.Integer(), nullable=True),
            sa.Column('expense_date', sa.Date(), nullable=False),
            sa.Column('category', sa.Enum('tyre', 'battery', 'maintenance', 'salary', 'khuraki', 'toll', 'road_tax', 'others', name='expensecategory', native_enum=False), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('vendor', sa.String(length=150), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['trip_id'], ['tanker_daily_reports.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_vehicle_expenses_id'), 'vehicle_expenses', ['id'], unique=False)
        op.create_index(op.f('ix_vehicle_expenses_vehicle_id'), 'vehicle_expenses', ['vehicle_id'], unique=False)
        op.create_index(op.f('ix_vehicle_expenses_category'), 'vehicle_expenses', ['category'], unique=False)
        op.create_index(op.f('ix_vehicle_expenses_expense_date'), 'vehicle_expenses', ['expense_date'], unique=False)

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'vehicle_expenses' in existing_tables:
        op.drop_table('vehicle_expenses')
    if 'route_points' in existing_tables:
        op.drop_table('route_points')
    vehicle_cols = [c['name'] for c in inspector.get_columns('vehicles')]
    if 'firm_id' in vehicle_cols:
        op.drop_column('vehicles', 'firm_id')
    if 'firms' in existing_tables:
        op.drop_table('firms')
