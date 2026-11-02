"""Mia tutor sessions, turns, and profile."""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tutor_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True, nullable=False),
        sa.Column('language', sa.String(2), server_default='en', nullable=False),
        sa.Column('mode', sa.String(20), server_default='classroom', nullable=False),
        sa.Column('step_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('question', sa.String(2000), server_default='', nullable=False),
        sa.Column('verified_solution', sa.JSON(), nullable=True),
        sa.Column('pace', sa.String(10), server_default='normal', nullable=False),
        sa.Column('method', sa.String(20), server_default='default', nullable=False),
        sa.Column('mistake_focus', sa.String(100), server_default='', nullable=False),
        sa.Column('created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('updated', sa.Integer(), server_default='0', nullable=False),
    )
    op.create_table(
        'tutor_turns',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('tutor_sessions.id'), index=True, nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True, nullable=False),
        sa.Column('role', sa.String(10), nullable=False),
        sa.Column('message', sa.String(4000), nullable=False),
        sa.Column('language', sa.String(2), server_default='en', nullable=False),
        sa.Column('step_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created', sa.Integer(), server_default='0', nullable=False),
    )
    op.create_table(
        'mia_profiles',
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('language', sa.String(2), server_default='en', nullable=False),
        sa.Column('pace', sa.String(10), server_default='normal', nullable=False),
        sa.Column('voice_rate', sa.Float(), server_default='0.88', nullable=False),
        sa.Column('updated', sa.Integer(), server_default='0', nullable=False),
    )


def downgrade():
    op.drop_table('mia_profiles')
    op.drop_table('tutor_turns')
    op.drop_table('tutor_sessions')
