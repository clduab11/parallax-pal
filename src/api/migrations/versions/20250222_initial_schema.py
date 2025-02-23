"""Initial database schema

Revision ID: 20250222_initial
Create Date: 2025-02-22 22:14:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '20250222_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'researcher', 'viewer')")
    op.execute("CREATE TYPE research_status AS ENUM ('pending', 'in_progress', 'completed', 'failed')")
    op.execute("CREATE TYPE subscription_status AS ENUM ('active', 'canceled', 'past_due', 'unpaid', 'trialing')")
    op.execute("CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded')")
    op.execute("CREATE TYPE query_purchase_type AS ENUM ('single', 'pack_5', 'pack_10')")
    op.execute("CREATE TYPE ai_model_type AS ENUM ('openai', 'anthropic', 'gemini', 'ollama')")

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', postgresql.ENUM('admin', 'researcher', 'viewer', name='user_role'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('mfa_secret', sa.String()),
        sa.Column('is_mfa_enabled', sa.Boolean(), default=False),
        sa.Column('stripe_customer_id', sa.String()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )

    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('interval', sa.String(), nullable=False),
        sa.Column('stripe_price_id', sa.String(), nullable=False),
        sa.Column('features', postgresql.JSON()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('allows_ollama', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('stripe_price_id')
    )

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'canceled', 'past_due', 'unpaid', 'trialing', name='subscription_status'), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cancel_at_period_end', sa.Boolean(), default=False),
        sa.Column('canceled_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_subscription_id')
    )

    # Create payment_methods table
    op.create_table(
        'payment_methods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stripe_payment_method_id', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('last4', sa.String(), nullable=False),
        sa.Column('exp_month', sa.Integer()),
        sa.Column('exp_year', sa.Integer()),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_payment_method_id')
    )

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), default='USD'),
        sa.Column('stripe_payment_intent_id', sa.String(), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'completed', 'failed', 'refunded', name='payment_status'), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('metadata', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('purchase_type', sa.String()),
        sa.Column('query_quantity', sa.Integer()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_payment_intent_id')
    )

    # Create query_purchases table
    op.create_table(
        'query_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('purchase_type', postgresql.ENUM('single', 'pack_5', 'pack_10', name='query_purchase_type'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price_per_query', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create query_credits table
    op.create_table(
        'query_credits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('remaining_queries', sa.Integer(), default=0),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create research_tasks table
    op.create_table(
        'research_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'failed', name='research_status'), nullable=False),
        sa.Column('result', sa.Text()),
        sa.Column('error_message', sa.Text()),
        sa.Column('continuous_mode', sa.Boolean(), default=False),
        sa.Column('max_iterations', sa.Integer(), default=1),
        sa.Column('current_iteration', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('web_results', postgresql.JSON()),
        sa.Column('ai_analyses', postgresql.JSON()),
        sa.Column('models_used', postgresql.ARRAY(sa.String())),
        sa.Column('used_ollama', sa.Boolean(), default=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create research_analytics table
    op.create_table(
        'research_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('processing_time', sa.Integer(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('source_count', sa.Integer(), nullable=False),
        sa.Column('model_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('avg_source_processing_time', sa.Float()),
        sa.Column('avg_tokens_per_source', sa.Float()),
        sa.Column('cache_hit_rate', sa.Float()),
        sa.Column('avg_model_confidence', sa.Float()),
        sa.ForeignKeyConstraint(['task_id'], ['research_tasks.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id')
    )

    # Create research_sources table
    op.create_table(
        'research_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String()),
        sa.Column('snippet', sa.Text()),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('processing_time', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['research_tasks.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create model_results table
    op.create_table(
        'model_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('model_type', postgresql.ENUM('openai', 'anthropic', 'gemini', 'ollama', name='ai_model_type'), nullable=False),
        sa.Column('analysis', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('processing_time', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['task_id'], ['research_tasks.id']),
        sa.ForeignKeyConstraint(['source_id'], ['research_sources.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('last_used', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )

    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('replaced_by', sa.Integer()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['replaced_by'], ['refresh_tokens.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('ip_address', sa.String(), nullable=False),
        sa.Column('user_agent', sa.String(), nullable=False),
        sa.Column('details', sa.Text()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_research_tasks_status', 'research_tasks', ['status'])
    op.create_index('ix_research_tasks_owner_created', 'research_tasks', ['owner_id', sa.text('created_at DESC')])
    op.create_index('ix_api_keys_active', 'api_keys', ['is_active'])
    op.create_index('ix_audit_logs_user_timestamp', 'audit_logs', ['user_id', sa.text('timestamp DESC')])
    op.create_index('ix_subscriptions_user_status', 'subscriptions', ['user_id', 'status'])
    op.create_index('ix_transactions_user_created', 'transactions', ['user_id', sa.text('created_at DESC')])
    op.create_index('ix_payment_methods_user_default', 'payment_methods', ['user_id', 'is_default'])
    op.create_index('ix_model_results_task_model', 'model_results', ['task_id', 'model_type'])
    op.create_index('ix_research_sources_task_relevance', 'research_sources', ['task_id', sa.text('relevance_score DESC')])
    op.create_index('ix_query_purchases_user_created', 'query_purchases', ['user_id', sa.text('created_at DESC')])
    op.create_index('ix_query_credits_user', 'query_credits', ['user_id'])
    op.create_index('ix_query_usage_credit', 'query_usage', ['credit_id', sa.text('used_at DESC')])

def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_query_usage_credit')
    op.drop_index('ix_query_credits_user')
    op.drop_index('ix_query_purchases_user_created')
    op.drop_index('ix_research_sources_task_relevance')
    op.drop_index('ix_model_results_task_model')
    op.drop_index('ix_payment_methods_user_default')
    op.drop_index('ix_transactions_user_created')
    op.drop_index('ix_subscriptions_user_status')
    op.drop_index('ix_audit_logs_user_timestamp')
    op.drop_index('ix_api_keys_active')
    op.drop_index('ix_research_tasks_owner_created')
    op.drop_index('ix_research_tasks_status')

    # Drop tables in reverse order of creation
    op.drop_table('audit_logs')
    op.drop_table('refresh_tokens')
    op.drop_table('api_keys')
    op.drop_table('model_results')
    op.drop_table('research_sources')
    op.drop_table('research_analytics')
    op.drop_table('research_tasks')
    op.drop_table('query_credits')
    op.drop_table('query_purchases')
    op.drop_table('transactions')
    op.drop_table('payment_methods')
    op.drop_table('subscriptions')
    op.drop_table('subscription_plans')
    op.drop_table('users')

    # Drop enum types
    op.execute('DROP TYPE ai_model_type')
    op.execute('DROP TYPE query_purchase_type')
    op.execute('DROP TYPE payment_status')
    op.execute('DROP TYPE subscription_status')
    op.execute('DROP TYPE research_status')
    op.execute('DROP TYPE user_role')