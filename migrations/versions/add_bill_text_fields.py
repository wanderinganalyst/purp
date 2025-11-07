"""Add full_text columns to bills table

Revision ID: add_bill_text_fields
Revises: c77eb2aba228
Create Date: 2025-11-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_bill_text_fields'
down_revision = 'c77eb2aba228'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns for bill text storage
    op.add_column('bills', sa.Column('full_text', sa.Text(), nullable=True))
    op.add_column('bills', sa.Column('text_pdf_url', sa.String(length=500), nullable=True))
    op.add_column('bills', sa.Column('summary_pdf_url', sa.String(length=500), nullable=True))
    op.add_column('bills', sa.Column('text_fetched_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove columns if rolling back
    op.drop_column('bills', 'text_fetched_at')
    op.drop_column('bills', 'summary_pdf_url')
    op.drop_column('bills', 'text_pdf_url')
    op.drop_column('bills', 'full_text')
