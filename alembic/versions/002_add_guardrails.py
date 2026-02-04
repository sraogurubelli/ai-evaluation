"""Add guardrails tables

Revision ID: 002
Revises: 001
Create Date: 2026-01-26 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create guardrail_tasks table
    op.create_table(
        'guardrail_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('meta_data', postgresql.JSON, nullable=True),
    )
    op.create_index('ix_guardrail_tasks_name', 'guardrail_tasks', ['name'])
    op.create_index('ix_guardrail_tasks_created_at', 'guardrail_tasks', ['created_at'])
    
    # Create guardrail_policies table
    op.create_table(
        'guardrail_policies',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, server_default='v1'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('policy_yaml', sa.Text(), nullable=False),
        sa.Column('is_global', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('meta_data', postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['guardrail_tasks.id']),
    )
    op.create_index('ix_guardrail_policies_task_id', 'guardrail_policies', ['task_id'])
    op.create_index('ix_guardrail_policies_name', 'guardrail_policies', ['name'])
    op.create_index('ix_guardrail_policies_is_global', 'guardrail_policies', ['is_global'])
    op.create_index('ix_guardrail_policies_enabled', 'guardrail_policies', ['enabled'])
    op.create_index('ix_guardrail_policies_created_at', 'guardrail_policies', ['created_at'])
    
    # Create guardrail_rules table
    op.create_table(
        'guardrail_rules',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('policy_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('rule_id', sa.String(255), nullable=False),
        sa.Column('check_type', sa.String(100), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('threshold', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('action', sa.String(50), nullable=False, server_default='warn'),
        sa.Column('config', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['guardrail_policies.id']),
    )
    op.create_index('ix_guardrail_rules_policy_id', 'guardrail_rules', ['policy_id'])
    op.create_index('ix_guardrail_rules_rule_id', 'guardrail_rules', ['rule_id'])
    op.create_index('ix_guardrail_rules_check_type', 'guardrail_rules', ['check_type'])
    op.create_index('ix_guardrail_rules_enabled', 'guardrail_rules', ['enabled'])
    op.create_index('ix_guardrail_rules_created_at', 'guardrail_rules', ['created_at'])
    
    # Create inferences table
    op.create_table(
        'inferences',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(255), nullable=True),
        sa.Column('experiment_run_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('rule_results', postgresql.JSON, nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('blocked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('meta_data', postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['guardrail_tasks.id']),
        sa.ForeignKeyConstraint(['experiment_run_id'], ['experiment_runs.id']),
    )
    op.create_index('ix_inferences_task_id', 'inferences', ['task_id'])
    op.create_index('ix_inferences_model_name', 'inferences', ['model_name'])
    op.create_index('ix_inferences_experiment_run_id', 'inferences', ['experiment_run_id'])
    op.create_index('ix_inferences_passed', 'inferences', ['passed'])
    op.create_index('ix_inferences_blocked', 'inferences', ['blocked'])
    op.create_index('ix_inferences_created_at', 'inferences', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_inferences_created_at', table_name='inferences')
    op.drop_index('ix_inferences_blocked', table_name='inferences')
    op.drop_index('ix_inferences_passed', table_name='inferences')
    op.drop_index('ix_inferences_experiment_run_id', table_name='inferences')
    op.drop_index('ix_inferences_model_name', table_name='inferences')
    op.drop_index('ix_inferences_task_id', table_name='inferences')
    op.drop_table('inferences')
    
    op.drop_index('ix_guardrail_rules_created_at', table_name='guardrail_rules')
    op.drop_index('ix_guardrail_rules_enabled', table_name='guardrail_rules')
    op.drop_index('ix_guardrail_rules_check_type', table_name='guardrail_rules')
    op.drop_index('ix_guardrail_rules_rule_id', table_name='guardrail_rules')
    op.drop_index('ix_guardrail_rules_policy_id', table_name='guardrail_rules')
    op.drop_table('guardrail_rules')
    
    op.drop_index('ix_guardrail_policies_created_at', table_name='guardrail_policies')
    op.drop_index('ix_guardrail_policies_enabled', table_name='guardrail_policies')
    op.drop_index('ix_guardrail_policies_is_global', table_name='guardrail_policies')
    op.drop_index('ix_guardrail_policies_name', table_name='guardrail_policies')
    op.drop_index('ix_guardrail_policies_task_id', table_name='guardrail_policies')
    op.drop_table('guardrail_policies')
    
    op.drop_index('ix_guardrail_tasks_created_at', table_name='guardrail_tasks')
    op.drop_index('ix_guardrail_tasks_name', table_name='guardrail_tasks')
    op.drop_table('guardrail_tasks')
