"""Add email verification OTP fields to users

Revision ID: 0005_email_verification
Revises: 0004_backfill_queue
Create Date: 2026-04-15

"""

from alembic import op
import sqlalchemy as sa

revision = '0005_email_verification'
down_revision = '0004_backfill_queue'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add OTP verification columns
    op.add_column('users', sa.Column(
        'verification_code', sa.String(6), nullable=True
    ))
    op.add_column('users', sa.Column(
        'verification_code_expires_at', sa.TIMESTAMP(), nullable=True
    ))
    # Allow email to be nullable for Steam users who haven't added one yet
    op.alter_column('users', 'email', nullable=True)


def downgrade() -> None:
    op.drop_column('users', 'verification_code')
    op.drop_column('users', 'verification_code_expires_at')
    op.alter_column('users', 'email', nullable=False)
