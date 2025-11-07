"""Add draft bills, draft bill comments, and staffer support

Revision ID: add_draft_bills_and_staffers
Revises: add_bill_text_fields
Create Date: 2025-11-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_draft_bills_and_staffers'
down_revision = 'add_bill_text_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add staffer support to users table
    op.add_column('users', sa.Column('rep_boss_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_rep_boss', 'users', 'representatives', ['rep_boss_id'], ['id'])
    
    # Create draft_bills table
    op.create_table('draft_bills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('representative_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default='hidden'),
        sa.Column('topic', sa.String(length=100), nullable=True),
        sa.Column('llm_prompt_used', sa.Text(), nullable=True),
        sa.Column('based_on_bills', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['representative_id'], ['representatives.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_draft_bills_representative_id'), 'draft_bills', ['representative_id'], unique=False)
    
    # Create draft_bill_comments table
    op.create_table('draft_bill_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('draft_bill_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('is_staffer', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['draft_bill_id'], ['draft_bills.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_draft_bill_comments_draft_bill_id'), 'draft_bill_comments', ['draft_bill_id'], unique=False)
    op.create_index(op.f('ix_draft_bill_comments_user_id'), 'draft_bill_comments', ['user_id'], unique=False)


def downgrade():
    # Drop tables and columns in reverse order
    op.drop_index(op.f('ix_draft_bill_comments_user_id'), table_name='draft_bill_comments')
    op.drop_index(op.f('ix_draft_bill_comments_draft_bill_id'), table_name='draft_bill_comments')
    op.drop_table('draft_bill_comments')
    
    op.drop_index(op.f('ix_draft_bills_representative_id'), table_name='draft_bills')
    op.drop_table('draft_bills')
    
    op.drop_constraint('fk_users_rep_boss', 'users', type_='foreignkey')
    op.drop_column('users', 'rep_boss_id')
