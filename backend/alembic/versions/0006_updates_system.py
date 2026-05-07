"""Add updates and user_update_reads tables

Revision ID: 0006_updates_system
Revises: 0005_email_verification
Create Date: 2026-05-07
"""

from alembic import op
import sqlalchemy as sa

revision = '0006_updates_system'
down_revision = '0005_email_verification'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create updates table
    op.create_table(
        'updates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_updates_created_at', 'updates', ['created_at'])

    # Create user_update_reads junction table
    op.create_table(
        'user_update_reads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('update_id', sa.Integer(), nullable=False),
        sa.Column('read_at', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['update_id'], ['updates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_update_reads_user', 'user_update_reads', ['user_id'])
    op.create_index('idx_user_update_reads_unique', 'user_update_reads', ['user_id', 'update_id'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_user_update_reads_unique', table_name='user_update_reads')
    op.drop_index('idx_user_update_reads_user', table_name='user_update_reads')
    op.drop_table('user_update_reads')
    op.drop_index('idx_updates_created_at', table_name='updates')
    op.drop_table('updates')
