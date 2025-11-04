"""create_price_history_table

Revision ID: 919842792ba3
Revises: b1c693bdd42f
Create Date: 2025-11-03 02:33:12.641268

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '919842792ba3'
down_revision = 'b1c693bdd42f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('investment_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('source', sa.String(), nullable=False, server_default='steam_market'),
        sa.Column('volume', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['investment_id'], ['investments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_history_id'), 'price_history', ['id'], unique=False)
    op.create_index(op.f('ix_price_history_investment_id'), 'price_history', ['investment_id'], unique=False)
    op.create_index(op.f('ix_price_history_timestamp'), 'price_history', ['timestamp'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_price_history_timestamp'), table_name='price_history')
    op.drop_index(op.f('ix_price_history_investment_id'), table_name='price_history')
    op.drop_index(op.f('ix_price_history_id'), table_name='price_history')
    op.drop_table('price_history')
