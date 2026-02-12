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
    # Create task_status enum only if it doesn't exist (idempotent for re-runs)
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
                CREATE TYPE task_status AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED');
            END IF;
        END
        $$;
    """))
    # Use postgresql.ENUM with create_type=False so create_table does not emit CREATE TYPE
    task_status_enum = postgresql.ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='task_status', create_type=False)
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('eval_name', sa.String(255), nullable=False),
        sa.Column('config', postgresql.JSON, nullable=False),
        sa.Column('status', task_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('meta_data', postgresql.JSON, nullable=True),
    )
    op.create_index('ix_tasks_eval_name', 'tasks', ['eval_name'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_created_at', 'tasks', ['created_at'])
    
    # Create evals table (formerly experiments)
    op.create_table(
        'evals',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dataset_config', postgresql.JSON, nullable=False),
        sa.Column('scorers_config', postgresql.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('meta_data', postgresql.JSON, nullable=True),
    )
    op.create_index('ix_evals_name', 'evals', ['name'])
    op.create_index('ix_evals_created_at', 'evals', ['created_at'])
    
    # Create runs table (formerly experiment_runs)
    op.create_table(
        'runs',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('eval_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('run_id', sa.String(255), nullable=False, unique=True),
        sa.Column('dataset_id', sa.String(255), nullable=False),
        sa.Column('model', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('meta_data', postgresql.JSON, nullable=True),
        sa.ForeignKeyConstraint(['eval_id'], ['evals.id']),
    )
    op.create_index('ix_runs_eval_id', 'runs', ['eval_id'])
    op.create_index('ix_runs_run_id', 'runs', ['run_id'])
    op.create_index('ix_runs_dataset_id', 'runs', ['dataset_id'])
    op.create_index('ix_runs_model', 'runs', ['model'])
    op.create_index('ix_runs_created_at', 'runs', ['created_at'])
    
    # Create scores table
    op.create_table(
        'scores',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('eval_id', sa.String(255), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('meta_data', postgresql.JSON, nullable=True),
        sa.Column('trace_id', sa.String(255), nullable=True),
        sa.Column('observation_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id']),
    )
    op.create_index('ix_scores_run_id', 'scores', ['run_id'])
    op.create_index('ix_scores_name', 'scores', ['name'])
    op.create_index('ix_scores_eval_id', 'scores', ['eval_id'])
    op.create_index('ix_scores_trace_id', 'scores', ['trace_id'])
    op.create_index('ix_scores_created_at', 'scores', ['created_at'])
    
    # Create task_results table
    op.create_table(
        'task_results',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=False), nullable=False, unique=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('execution_time_seconds', sa.Float(), nullable=False),
        sa.Column('meta_data', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id']),
    )
    op.create_index('ix_task_results_task_id', 'task_results', ['task_id'])
    op.create_index('ix_task_results_run_id', 'task_results', ['run_id'])


def downgrade() -> None:
    op.drop_table('task_results')
    op.drop_table('scores')
    op.drop_table('runs')
    op.drop_table('evals')
    op.drop_table('tasks')
    op.execute('DROP TYPE IF EXISTS task_status')
