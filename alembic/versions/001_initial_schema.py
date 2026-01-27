"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-01-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create task_status enum
    task_status_enum = sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='task_status')
    task_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('experiment_name', sa.String(255), nullable=False),
        sa.Column('config', postgresql.JSON, nullable=False),
        sa.Column('status', task_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON, nullable=True),
    )
    op.create_index('ix_tasks_experiment_name', 'tasks', ['experiment_name'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_created_at', 'tasks', ['created_at'])
    
    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dataset_config', postgresql.JSON, nullable=False),
        sa.Column('scorers_config', postgresql.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSON, nullable=True),
    )
    op.create_index('ix_experiments_name', 'experiments', ['name'])
    op.create_index('ix_experiments_created_at', 'experiments', ['created_at'])
    
    # Create experiment_runs table
    op.create_table(
        'experiment_runs',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('run_id', sa.String(255), nullable=False, unique=True),
        sa.Column('dataset_id', sa.String(255), nullable=False),
        sa.Column('model', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id']),
    )
    op.create_index('ix_experiment_runs_experiment_id', 'experiment_runs', ['experiment_id'])
    op.create_index('ix_experiment_runs_run_id', 'experiment_runs', ['run_id'])
    op.create_index('ix_experiment_runs_dataset_id', 'experiment_runs', ['dataset_id'])
    op.create_index('ix_experiment_runs_model', 'experiment_runs', ['model'])
    op.create_index('ix_experiment_runs_created_at', 'experiment_runs', ['created_at'])
    
    # Create scores table
    op.create_table(
        'scores',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('experiment_run_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('eval_id', sa.String(255), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON, nullable=True),
        sa.Column('trace_id', sa.String(255), nullable=True),
        sa.Column('observation_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_run_id'], ['experiment_runs.id']),
    )
    op.create_index('ix_scores_experiment_run_id', 'scores', ['experiment_run_id'])
    op.create_index('ix_scores_name', 'scores', ['name'])
    op.create_index('ix_scores_eval_id', 'scores', ['eval_id'])
    op.create_index('ix_scores_trace_id', 'scores', ['trace_id'])
    op.create_index('ix_scores_created_at', 'scores', ['created_at'])
    
    # Create task_results table
    op.create_table(
        'task_results',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=False), nullable=False, unique=True),
        sa.Column('experiment_run_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('execution_time_seconds', sa.Float(), nullable=False),
        sa.Column('metadata', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['experiment_run_id'], ['experiment_runs.id']),
    )
    op.create_index('ix_task_results_task_id', 'task_results', ['task_id'])
    op.create_index('ix_task_results_experiment_run_id', 'task_results', ['experiment_run_id'])


def downgrade() -> None:
    op.drop_table('task_results')
    op.drop_table('scores')
    op.drop_table('experiment_runs')
    op.drop_table('experiments')
    op.drop_table('tasks')
    op.execute('DROP TYPE IF EXISTS task_status')
