"""Add Stripe subscription fields to users

Revision ID: 0003_stripe_subscription
Revises: 0002_price_history_candles
Create Date: 2026-04-07
"""

from alembic import op
import sqlalchemy as sa

revision = '0003_stripe_subscription'
down_revision = '0002_price_history_candles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column(
        'stripe_customer_id', sa.String(255), nullable=True,
    ))
    op.add_column('users', sa.Column(
        'stripe_subscription_id', sa.String(255), nullable=True,
    ))
    op.add_column('users', sa.Column(
        'subscription_status', sa.String(50), nullable=True,
    ))
    op.create_index(
        'ix_users_stripe_customer_id', 'users', ['stripe_customer_id'], unique=True,
    )


def downgrade() -> None:
    op.drop_index('ix_users_stripe_customer_id', table_name='users')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_customer_id')
