"""Add needs_backfill queue column to items

Revision ID: 0004_backfill_queue
Revises: 0003_stripe_subscription
Create Date: 2026-04-07
"""

from alembic import op
import sqlalchemy as sa

revision = '0004_backfill_queue'
down_revision = '0003_stripe_subscription'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('items', sa.Column(
        'needs_backfill', sa.Boolean(), nullable=False, server_default='false'
    ))
    op.add_column('items', sa.Column(
        'backfill_attempts', sa.Integer(), nullable=False, server_default='0'
    ))
    op.add_column('items', sa.Column(
        'backfill_queued_at', sa.TIMESTAMP(), nullable=True
    ))
    # Index so the queue job can efficiently find work
    op.create_index('idx_items_needs_backfill', 'items', ['needs_backfill'])


def downgrade() -> None:
    op.drop_index('idx_items_needs_backfill', table_name='items')
    op.drop_column('items', 'backfill_queued_at')
    op.drop_column('items', 'backfill_attempts')
    op.drop_column('items', 'needs_backfill')

