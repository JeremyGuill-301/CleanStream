"""Add inventory constraints and audit logging

Revision ID: 1779163092
Revises: 76ec99861b87
Create Date: 2026-05-18 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '1779163092'
down_revision = '76ec99861b87'
branch_labels = None
depends_on = None


def upgrade():
    # Add inventory_audit table for tracking all corrections
    op.create_table(
        'inventory_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supply_id', sa.Integer(), nullable=False),
        sa.Column('audit_type', sa.Enum('Discrepancy Found', 'Manual Correction', 'Reconciliation', 'Validation Failed'), nullable=False),
        sa.Column('previous_count', sa.Integer(), nullable=False),
        sa.Column('new_count', sa.Integer(), nullable=False),
        sa.Column('calculated_count', sa.Integer(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('corrected_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(['supply_id'], ['supplies.id'], ),
        sa.ForeignKeyConstraint(['corrected_by_user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add new columns to supply_inventory for better tracking
    op.add_column('supply_inventory', sa.Column('reconciliation_note', sa.Text(), nullable=True))
    
    # Add CHECK constraint to prevent negative current_count
    # Note: SQLite doesn't support CHECK constraints modification after table creation,
    # so we'll handle this at the application level but document it here
    
    # Create an index for faster inventory lookups
    op.create_index('ix_supply_inventory_supply_id', 'supply_inventory', ['supply_id'])
    op.create_index('ix_supply_inventory_status', 'supply_inventory', ['status'])
    op.create_index('ix_inventory_audit_supply_id', 'inventory_audit', ['supply_id'])


def downgrade():
    op.drop_index('ix_inventory_audit_supply_id', table_name='inventory_audit')
    op.drop_index('ix_supply_inventory_status', table_name='supply_inventory')
    op.drop_index('ix_supply_inventory_supply_id', table_name='supply_inventory')
    op.drop_column('supply_inventory', 'reconciliation_note')
    op.drop_table('inventory_audit')
