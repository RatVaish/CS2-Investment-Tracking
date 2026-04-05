"""price_history - replace date with candle_timestamp, add resolution and weekly support

Revision ID: 0002_price_history_candles
Revises: 0001_v4_schema
Create Date: 2026-04-05

What this migration does:
1. Drops old indexes and unique constraints on price_history
2. Migrates existing data:
   - All existing rows have date (DATE) and no resolution
   - Converts date -> candle_timestamp (TIMESTAMP at midnight)
   - Sets resolution = 'daily' for all existing rows (they were daily candles)
3. Drops old date column
4. Adds resolution column
5. Adds updated_at column
6. Recreates indexes and unique constraint on new structure
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_price_history_candles'
down_revision: Union[str, Sequence[str], None] = '0001_v4_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # Step 1 — Drop existing constraints and indexes
    op.drop_constraint('uq_item_market_date', 'price_history', type_='unique')
    op.drop_index('idx_price_history_item_date', table_name='price_history')
    op.drop_index('idx_price_history_market_date', table_name='price_history')

    # Step 2 — Add candle_timestamp as nullable first (so we can populate it)
    op.add_column('price_history',
        sa.Column('candle_timestamp', sa.TIMESTAMP(), nullable=True)
    )

    # Step 3 — Populate candle_timestamp from existing date column
    # Convert DATE to TIMESTAMP at midnight UTC
    op.execute("""
        UPDATE price_history
        SET candle_timestamp = date::timestamp
        WHERE candle_timestamp IS NULL
    """)

    # Step 4 — Make candle_timestamp non-nullable now that it's populated
    op.alter_column('price_history', 'candle_timestamp', nullable=False)

    # Step 5 — Drop old date column
    op.drop_column('price_history', 'date')

    # Step 6 — Drop listing_count (not needed for Steam-sourced candles)
    op.drop_column('price_history', 'listing_count')

    # Step 7 — Add resolution column
    # All existing rows are daily candles (from old CSFloat daily job)
    op.add_column('price_history',
        sa.Column('resolution', sa.String(10), nullable=False, server_default='daily')
    )

    # Step 8 — Add updated_at column
    op.add_column('price_history',
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, server_default='NOW()')
    )

    # Step 9 — Recreate unique constraint on new structure
    op.create_unique_constraint(
        'uq_item_market_timestamp_resolution',
        'price_history',
        ['item_id', 'market', 'candle_timestamp', 'resolution']
    )

    # Step 10 — Recreate indexes for new query patterns
    op.create_index(
        'idx_ph_item_market_resolution_ts',
        'price_history',
        ['item_id', 'market', 'resolution', 'candle_timestamp']
    )
    op.create_index(
        'idx_ph_item_ts',
        'price_history',
        ['item_id', 'candle_timestamp']
    )


def downgrade() -> None:
    # Drop new indexes and constraints
    op.drop_index('idx_ph_item_ts', table_name='price_history')
    op.drop_index('idx_ph_item_market_resolution_ts', table_name='price_history')
    op.drop_constraint('uq_item_market_timestamp_resolution', 'price_history', type_='unique')

    # Remove new columns
    op.drop_column('price_history', 'updated_at')
    op.drop_column('price_history', 'resolution')

    # Add date column back
    op.add_column('price_history',
        sa.Column('date', sa.Date(), nullable=True)
    )

    # Restore listing_count
    op.add_column('price_history',
        sa.Column('listing_count', sa.Integer(), nullable=True)
    )

    # Populate date from candle_timestamp
    op.execute("""
        UPDATE price_history
        SET date = candle_timestamp::date
    """)

    # Make date non-nullable
    op.alter_column('price_history', 'date', nullable=False)

    # Drop candle_timestamp
    op.drop_column('price_history', 'candle_timestamp')

    # Restore old indexes and constraint
    op.create_unique_constraint(
        'uq_item_market_date',
        'price_history',
        ['item_id', 'market', 'date']
    )
    op.create_index('idx_price_history_item_date', 'price_history', ['item_id', 'date'])
    op.create_index('idx_price_history_market_date', 'price_history', ['item_id', 'market', 'date'])
