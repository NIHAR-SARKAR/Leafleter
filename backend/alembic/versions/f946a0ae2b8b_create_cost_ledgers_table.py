"""create cost ledgers table

Revision ID: f946a0ae2b8b
Revises: a27710824b7a
Create Date: 2026-06-19 00:45:57.622398

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'f946a0ae2b8b'
down_revision = 'a27710824b7a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cost_ledgers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('provider_type', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('operation', sa.String(length=50), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=True),
        sa.Column('provider_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('trace_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cost_ledgers_id'), 'cost_ledgers', ['id'], unique=False)
    op.create_index(op.f('ix_cost_ledgers_model'), 'cost_ledgers', ['model'], unique=False)
    op.create_index(op.f('ix_cost_ledgers_operation'), 'cost_ledgers', ['operation'], unique=False)
    op.create_index(op.f('ix_cost_ledgers_organization_id'), 'cost_ledgers', ['organization_id'], unique=False)
    op.create_index(op.f('ix_cost_ledgers_provider_id'), 'cost_ledgers', ['provider_id'], unique=False)
    op.create_index(op.f('ix_cost_ledgers_provider_type'), 'cost_ledgers', ['provider_type'], unique=False)
    op.create_index(op.f('ix_cost_ledgers_topic_id'), 'cost_ledgers', ['topic_id'], unique=False)
    op.create_index(op.f('ix_cost_ledgers_trace_id'), 'cost_ledgers', ['trace_id'], unique=False)
    op.create_index(op.f('ix_cost_ledgers_user_id'), 'cost_ledgers', ['user_id'], unique=False)
    op.create_foreign_key(op.f('fk_cost_ledgers_organization_id_organizations'), 'cost_ledgers', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_cost_ledgers_provider_id_providers'), 'cost_ledgers', 'providers', ['provider_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('fk_cost_ledgers_topic_id_topics'), 'cost_ledgers', 'topics', ['topic_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('fk_cost_ledgers_user_id_users'), 'cost_ledgers', 'users', ['user_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_index(op.f('ix_cost_ledgers_user_id'), table_name='cost_ledgers')
    op.drop_index(op.f('ix_cost_ledgers_trace_id'), table_name='cost_ledgers')
    op.drop_index(op.f('ix_cost_ledgers_topic_id'), table_name='cost_ledgers')
    op.drop_index(op.f('ix_cost_ledgers_provider_type'), table_name='cost_ledgers')
    op.drop_index(op.f('ix_cost_ledgers_provider_id'), table_name='cost_ledgers')
    op.drop_index(op.f('ix_cost_ledgers_organization_id'), table_name='cost_ledgers')
    op.drop_index(op.f('ix_cost_ledgers_operation'), table_name='cost_ledgers')
    op.drop_index(op.f('ix_cost_ledgers_model'), table_name='cost_ledgers')
    op.drop_index(op.f('ix_cost_ledgers_id'), table_name='cost_ledgers')
    op.drop_table('cost_ledgers')
