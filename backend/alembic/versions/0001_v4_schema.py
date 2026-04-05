"""V4 schema - complete database overhaul

Revision ID: 0001_v4_schema
Revises:
Create Date: 2026-04-05

What this migration does:
1.  Stamps Alembic version (DB was created outside Alembic, no version row exists)
2.  Adds new columns to `items` (phase, tournament, min_float, max_float, is_commodity, last_synced_at)
3.  Adds new columns to `users` (display_name, google_id, tier, tier_expires_at, preferences,
        steam_data_consent, steam_data_consent_at, terms_accepted_at,
        privacy_policy_accepted_at, data_export_requested_at,
        deletion_requested_at, deletion_scheduled_at)
4.  Transforms `item_prices` from V3 (column-per-market) to V4 (row-per-market)
        - Creates new V4 table as `item_prices_v4`
        - Migrates existing CSFloat data across as market='csfloat' rows
        - Drops old `item_prices` table
        - Renames `item_prices_v4` → `item_prices`
        - Recreates indexes and constraints
5.  Transforms `price_history`
        - Renames column `source` → `market`
        - Adds `currency` and `listing_count` columns
        - Drops `resolution` column (deprecated - daily only)
        - Recreates unique constraint to match new schema
6.  Creates 11 new tables:
        user_consents, investment_stickers, investment_tags,
        investment_audit, portfolio_snapshots, price_alerts,
        notifications, user_watchlist, import_batches,
        exchange_rates, item_sync_log, price_update_log, market_benchmarks
7.  Adds new columns to `investments`
        (purchase_fee, wear_value, status, sold_price, sold_at,
         sold_fee, target_price, import_source, import_batch_id, steam_asset_id)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_v4_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # =========================================================================
    # STEP 1 — Items: add new columns
    # =========================================================================
    op.add_column('items', sa.Column('phase', sa.String(50), nullable=True))
    op.add_column('items', sa.Column('tournament', sa.String(100), nullable=True))
    op.add_column('items', sa.Column('min_float', sa.Float(), nullable=True))
    op.add_column('items', sa.Column('max_float', sa.Float(), nullable=True))
    op.add_column('items', sa.Column('is_commodity', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('items', sa.Column('last_synced_at', sa.TIMESTAMP(), nullable=True))

    # =========================================================================
    # STEP 2 — Users: add new columns
    # =========================================================================
    op.add_column('users', sa.Column('display_name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)

    op.add_column('users', sa.Column('tier', sa.String(10), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('tier_expires_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('users', sa.Column('preferences', postgresql.JSONB(), nullable=True))

    op.add_column('users', sa.Column('steam_data_consent', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('steam_data_consent_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('users', sa.Column('terms_accepted_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('users', sa.Column('privacy_policy_accepted_at', sa.TIMESTAMP(), nullable=True))

    op.add_column('users', sa.Column('data_export_requested_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('users', sa.Column('deletion_requested_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('users', sa.Column('deletion_scheduled_at', sa.TIMESTAMP(), nullable=True))

    # =========================================================================
    # STEP 3 — item_prices: V3 → V4 transformation
    #
    # V3: one row per item, columns per market
    # V4: one row per item per market
    #
    # We create a new table, migrate data, drop old, rename new.
    # Done inside the migration transaction so it's atomic.
    # =========================================================================

    # Create V4 item_prices table under a temporary name
    op.create_table(
        'item_prices_v4',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('market', sa.String(20), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('lowest_listing', sa.Float(), nullable=True),
        sa.Column('highest_bid', sa.Float(), nullable=True),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.Column('listing_count', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_item_prices_v4_item_id', 'item_prices_v4', ['item_id'], unique=False)
    op.create_index('ix_item_prices_v4_market', 'item_prices_v4', ['market'], unique=False)

    # Migrate existing CSFloat data from V3 → V4
    # Only migrate rows that actually have a csfloat_price value
    op.execute("""
        INSERT INTO item_prices_v4 (item_id, market, price, lowest_listing, volume, currency, updated_at)
        SELECT
            item_id,
            'csfloat'                   AS market,
            csfloat_price               AS price,
            csfloat_lowest_listing      AS lowest_listing,
            csfloat_volume              AS volume,
            'USD'                       AS currency,
            csfloat_updated_at          AS updated_at
        FROM item_prices
        WHERE csfloat_price IS NOT NULL
    """)

    # Migrate existing Buff data (if any exists)
    op.execute("""
        INSERT INTO item_prices_v4 (item_id, market, price, volume, currency, updated_at)
        SELECT
            item_id,
            'buff163'       AS market,
            buff_price      AS price,
            buff_volume     AS volume,
            'CNY'           AS currency,
            buff_updated_at AS updated_at
        FROM item_prices
        WHERE buff_price IS NOT NULL
    """)

    # Migrate existing Steam data (if any exists)
    op.execute("""
        INSERT INTO item_prices_v4 (item_id, market, price, volume, currency, updated_at)
        SELECT
            item_id,
            'steam'          AS market,
            steam_price      AS price,
            steam_volume     AS volume,
            'USD'            AS currency,
            steam_updated_at AS updated_at
        FROM item_prices
        WHERE steam_price IS NOT NULL
    """)

    # Drop old V3 table
    op.drop_index('ix_item_prices_item_id', table_name='item_prices')
    op.drop_index('ix_item_prices_id', table_name='item_prices')
    op.drop_table('item_prices')

    # Rename V4 table to final name
    op.rename_table('item_prices_v4', 'item_prices')

    # Rename indexes to match final table name
    op.execute('ALTER INDEX ix_item_prices_v4_item_id RENAME TO ix_item_prices_item_id')
    op.execute('ALTER INDEX ix_item_prices_v4_market RENAME TO ix_item_prices_market')

    # Add sequence-backed primary key properly and unique constraint
    op.execute('CREATE SEQUENCE IF NOT EXISTS item_prices_id_seq OWNED BY item_prices.id')
    op.execute("SELECT setval('item_prices_id_seq', (SELECT MAX(id) FROM item_prices) + 1)")
    op.execute("ALTER TABLE item_prices ALTER COLUMN id SET DEFAULT nextval('item_prices_id_seq')")

    op.create_unique_constraint('uq_item_market', 'item_prices', ['item_id', 'market'])

    # =========================================================================
    # STEP 4 — price_history transformation
    #
    # - Rename source → market
    # - Add currency and listing_count columns
    # - Drop resolution column (deprecated, daily only going forward)
    # - Fix unique constraint
    # =========================================================================

    # Drop existing constraints before altering columns
    op.drop_constraint('uq_item_source_date_resolution', 'price_history', type_='unique')
    op.drop_index('idx_price_history_resolution', table_name='price_history')

    # Rename source → market
    op.alter_column('price_history', 'source', new_column_name='market')

    # Add new columns
    op.add_column('price_history', sa.Column('listing_count', sa.Integer(), nullable=True))
    op.add_column('price_history', sa.Column('currency', sa.String(3), nullable=False, server_default='USD'))

    # Drop resolution (deprecated)
    op.drop_column('price_history', 'resolution')

    # Recreate unique constraint without resolution
    op.create_unique_constraint('uq_item_market_date', 'price_history', ['item_id', 'market', 'date'])

    # Add index for market + date queries
    op.create_index('idx_price_history_market_date', 'price_history', ['item_id', 'market', 'date'])

    # =========================================================================
    # STEP 5 — investments: add new columns
    # =========================================================================

    # Create import_batches first since investments FKs to it
    op.create_table(
        'import_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('total_items', sa.Integer(), nullable=True),
        sa.Column('imported_items', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('skipped_items', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_items', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('error_msg', sa.String(1000), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default='NOW()'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_import_batches_user_id', 'import_batches', ['user_id'], unique=False)

    # Now add new investment columns
    op.add_column('investments', sa.Column('purchase_fee', sa.Float(), nullable=True))
    op.add_column('investments', sa.Column('wear_value', sa.Float(), nullable=True))
    op.add_column('investments', sa.Column('status', sa.String(10), nullable=False, server_default='active'))
    op.add_column('investments', sa.Column('sold_price', sa.Float(), nullable=True))
    op.add_column('investments', sa.Column('sold_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('investments', sa.Column('sold_fee', sa.Float(), nullable=True))
    op.add_column('investments', sa.Column('target_price', sa.Float(), nullable=True))
    op.add_column('investments', sa.Column('import_source', sa.String(20), nullable=True))
    op.add_column('investments', sa.Column('import_batch_id', sa.Integer(), nullable=True))
    op.add_column('investments', sa.Column('steam_asset_id', sa.String(20), nullable=True))

    op.create_foreign_key(
        'fk_investments_import_batch',
        'investments', 'import_batches',
        ['import_batch_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_investments_steam_asset_id', 'investments', ['steam_asset_id'], unique=False)

    # =========================================================================
    # STEP 6 — Create all new tables
    # =========================================================================

    # user_consents
    op.create_table(
        'user_consents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('consent_type', sa.String(50), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False),
        sa.Column('granted_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('revoked_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('consent_version', sa.String(20), nullable=False, server_default='v1.0'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_consents_user_id', 'user_consents', ['user_id'], unique=False)

    # investment_stickers
    op.create_table(
        'investment_stickers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('investment_id', sa.Integer(), nullable=False),
        sa.Column('slot', sa.Integer(), nullable=False),
        sa.Column('sticker_name', sa.String(255), nullable=False),
        sa.Column('sticker_wear', sa.Float(), nullable=True),
        sa.Column('applied_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('purchase_value', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['investment_id'], ['investments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('investment_id', 'slot', name='uq_investment_sticker_slot'),
    )
    op.create_index('ix_investment_stickers_investment_id', 'investment_stickers', ['investment_id'], unique=False)

    # investment_tags
    op.create_table(
        'investment_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('investment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tag', sa.String(50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default='NOW()'),
        sa.ForeignKeyConstraint(['investment_id'], ['investments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('investment_id', 'tag', name='uq_investment_tag'),
    )
    op.create_index('ix_investment_tags_investment_id', 'investment_tags', ['investment_id'], unique=False)
    op.create_index('ix_investment_tags_user_id', 'investment_tags', ['user_id'], unique=False)
    op.create_index('idx_investment_tags_user_tag', 'investment_tags', ['user_id', 'tag'], unique=False)

    # investment_audit
    op.create_table(
        'investment_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('investment_id', sa.Integer(), nullable=True),   # nullable — survives deletion
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('old_values', postgresql.JSONB(), nullable=True),
        sa.Column('new_values', postgresql.JSONB(), nullable=True),
        sa.Column('changed_at', sa.TIMESTAMP(), server_default='NOW()', nullable=False),
        sa.ForeignKeyConstraint(['investment_id'], ['investments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_investment_audit_investment_id', 'investment_audit', ['investment_id'], unique=False)
    op.create_index('ix_investment_audit_user_id', 'investment_audit', ['user_id'], unique=False)

    # portfolio_snapshots
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_invested', sa.Float(), nullable=False),
        sa.Column('total_current_value', sa.Float(), nullable=False),
        sa.Column('total_profit_loss', sa.Float(), nullable=False),
        sa.Column('overall_roi', sa.Float(), nullable=False),
        sa.Column('csfloat_value', sa.Float(), nullable=True),
        sa.Column('buff_value', sa.Float(), nullable=True),
        sa.Column('open_positions', sa.Integer(), nullable=True),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default='NOW()'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'snapshot_date', name='uq_user_snapshot_date'),
    )
    op.create_index('ix_portfolio_snapshots_user_id', 'portfolio_snapshots', ['user_id'], unique=False)

    # price_alerts
    op.create_table(
        'price_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('market', sa.String(20), nullable=False),
        sa.Column('target_price', sa.Float(), nullable=False),
        sa.Column('direction', sa.String(5), nullable=False),
        sa.Column('is_triggered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('triggered_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default='NOW()'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_price_alerts_user_id', 'price_alerts', ['user_id'], unique=False)
    op.create_index('ix_price_alerts_item_id', 'price_alerts', ['item_id'], unique=False)

    # notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(30), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.String(1000), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default='NOW()'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)

    # user_watchlist
    op.create_table(
        'user_watchlist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('added_at', sa.TIMESTAMP(), server_default='NOW()'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'item_id', name='uq_user_watchlist_item'),
    )
    op.create_index('ix_user_watchlist_user_id', 'user_watchlist', ['user_id'], unique=False)
    op.create_index('ix_user_watchlist_item_id', 'user_watchlist', ['item_id'], unique=False)

    # exchange_rates
    op.create_table(
        'exchange_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_currency', sa.String(3), nullable=False),
        sa.Column('to_currency', sa.String(3), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default='NOW()'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('from_currency', 'to_currency', 'date', name='uq_exchange_rate_date'),
    )

    # item_sync_log
    op.create_table(
        'item_sync_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False, server_default='byMykel_github'),
        sa.Column('commit_sha', sa.String(40), nullable=True),
        sa.Column('previous_sha', sa.String(40), nullable=True),
        sa.Column('items_added', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('items_updated', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('items_deactivated', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('synced_at', sa.TIMESTAMP(), server_default='NOW()'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_msg', sa.String(1000), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # price_update_log
    op.create_table(
        'price_update_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('market', sa.String(20), nullable=False),
        sa.Column('items_updated', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('items_failed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('items_skipped', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('ran_at', sa.TIMESTAMP(), server_default='NOW()'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_msg', sa.String(1000), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # market_benchmarks
    op.create_table(
        'market_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('metric', sa.String(30), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='internal'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default='NOW()'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'metric', name='uq_benchmark_date_metric'),
    )


def downgrade() -> None:
    """
    Reverses the migration. Converts V4 item_prices back to V3 column-per-market.
    NOTE: Any Buff or Steam price data added after the upgrade will be lost on downgrade
    since V3 has no mechanism to store multiple markets cleanly.
    """

    # Drop all new tables (reverse order of creation)
    op.drop_table('market_benchmarks')
    op.drop_table('price_update_log')
    op.drop_table('item_sync_log')
    op.drop_table('exchange_rates')
    op.drop_index('ix_user_watchlist_item_id', table_name='user_watchlist')
    op.drop_index('ix_user_watchlist_user_id', table_name='user_watchlist')
    op.drop_table('user_watchlist')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
    op.drop_index('ix_price_alerts_item_id', table_name='price_alerts')
    op.drop_index('ix_price_alerts_user_id', table_name='price_alerts')
    op.drop_table('price_alerts')
    op.drop_index('ix_portfolio_snapshots_user_id', table_name='portfolio_snapshots')
    op.drop_table('portfolio_snapshots')
    op.drop_index('ix_investment_audit_user_id', table_name='investment_audit')
    op.drop_index('ix_investment_audit_investment_id', table_name='investment_audit')
    op.drop_table('investment_audit')
    op.drop_index('idx_investment_tags_user_tag', table_name='investment_tags')
    op.drop_index('ix_investment_tags_user_id', table_name='investment_tags')
    op.drop_index('ix_investment_tags_investment_id', table_name='investment_tags')
    op.drop_table('investment_tags')
    op.drop_index('ix_investment_stickers_investment_id', table_name='investment_stickers')
    op.drop_table('investment_stickers')
    op.drop_index('ix_user_consents_user_id', table_name='user_consents')
    op.drop_table('user_consents')

    # Remove investment new columns
    op.drop_constraint('fk_investments_import_batch', 'investments', type_='foreignkey')
    op.drop_index('ix_investments_steam_asset_id', table_name='investments')
    op.drop_column('investments', 'steam_asset_id')
    op.drop_column('investments', 'import_batch_id')
    op.drop_column('investments', 'import_source')
    op.drop_column('investments', 'target_price')
    op.drop_column('investments', 'sold_fee')
    op.drop_column('investments', 'sold_at')
    op.drop_column('investments', 'sold_price')
    op.drop_column('investments', 'status')
    op.drop_column('investments', 'wear_value')
    op.drop_column('investments', 'purchase_fee')
    op.drop_table('import_batches')

    # Restore price_history to V3 shape
    op.drop_constraint('uq_item_market_date', 'price_history', type_='unique')
    op.drop_index('idx_price_history_market_date', table_name='price_history')
    op.alter_column('price_history', 'market', new_column_name='source')
    op.drop_column('price_history', 'currency')
    op.drop_column('price_history', 'listing_count')
    op.add_column('price_history', sa.Column('resolution', sa.String(20), server_default='daily', nullable=False))
    op.create_unique_constraint(
        'uq_item_source_date_resolution', 'price_history',
        ['item_id', 'source', 'date', 'resolution']
    )
    op.create_index('idx_price_history_resolution', 'price_history', ['item_id', 'resolution', 'date'])

    # Restore item_prices to V3 (column-per-market)
    op.drop_constraint('uq_item_market', 'item_prices', type_='unique')
    op.drop_index('ix_item_prices_market', table_name='item_prices')
    op.drop_index('ix_item_prices_item_id', table_name='item_prices')

    op.create_table(
        'item_prices_v3',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('csfloat_price', sa.Float(), nullable=True),
        sa.Column('csfloat_volume', sa.Integer(), nullable=True),
        sa.Column('csfloat_lowest_listing', sa.Float(), nullable=True),
        sa.Column('csfloat_updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('buff_price', sa.Float(), nullable=True),
        sa.Column('buff_volume', sa.Integer(), nullable=True),
        sa.Column('buff_updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('steam_price', sa.Float(), nullable=True),
        sa.Column('steam_volume', sa.Integer(), nullable=True),
        sa.Column('steam_updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('last_updated', sa.TIMESTAMP(), server_default='NOW()'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Migrate CSFloat data back to V3
    op.execute("""
        INSERT INTO item_prices_v3 (item_id, csfloat_price, csfloat_volume, csfloat_updated_at, last_updated)
        SELECT item_id, price, volume, updated_at, NOW()
        FROM item_prices
        WHERE market = 'csfloat'
    """)

    op.drop_table('item_prices')
    op.rename_table('item_prices_v3', 'item_prices')
    op.execute('CREATE SEQUENCE IF NOT EXISTS item_prices_id_seq OWNED BY item_prices.id')
    op.execute("SELECT setval('item_prices_id_seq', (SELECT MAX(id) FROM item_prices) + 1)")
    op.execute("ALTER TABLE item_prices ALTER COLUMN id SET DEFAULT nextval('item_prices_id_seq')")
    op.create_index('ix_item_prices_item_id', 'item_prices', ['item_id'], unique=True)
    op.create_index('ix_item_prices_id', 'item_prices', ['id'], unique=False)

    # Remove user new columns
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_column('users', 'deletion_scheduled_at')
    op.drop_column('users', 'deletion_requested_at')
    op.drop_column('users', 'data_export_requested_at')
    op.drop_column('users', 'privacy_policy_accepted_at')
    op.drop_column('users', 'terms_accepted_at')
    op.drop_column('users', 'steam_data_consent_at')
    op.drop_column('users', 'steam_data_consent')
    op.drop_column('users', 'preferences')
    op.drop_column('users', 'tier_expires_at')
    op.drop_column('users', 'tier')
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'display_name')

    # Remove items new columns
    op.drop_column('items', 'last_synced_at')
    op.drop_column('items', 'is_commodity')
    op.drop_column('items', 'max_float')
    op.drop_column('items', 'min_float')
    op.drop_column('items', 'tournament')
    op.drop_column('items', 'phase')
