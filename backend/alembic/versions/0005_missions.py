"""Autonomous mistake-to-mastery missions."""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'missions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True, nullable=False),
        sa.Column('goal', sa.String(300), nullable=False),
        sa.Column('topic', sa.String(40), nullable=False),
        sa.Column('error_code', sa.String(40), nullable=True),
        sa.Column('state', sa.String(10), server_default='active', nullable=False),
        sa.Column('difficulty', sa.Integer(), server_default='1', nullable=False),
        sa.Column('exit_wins', sa.Integer(), server_default='3', nullable=False),
        sa.Column('max_drills', sa.Integer(), server_default='10', nullable=False),
        sa.Column('max_replans', sa.Integer(), server_default='2', nullable=False),
        sa.Column('drills_done', sa.Integer(), server_default='0', nullable=False),
        sa.Column('correct_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('consecutive', sa.Integer(), server_default='0', nullable=False),
        sa.Column('replans', sa.Integer(), server_default='0', nullable=False),
        sa.Column('current', sa.JSON(), nullable=True),
        sa.Column('example', sa.JSON(), nullable=True),
        sa.Column('drills', sa.JSON(), nullable=False),
        sa.Column('trace', sa.JSON(), nullable=False),
        sa.Column('accuracy_before', sa.Float(), server_default='0', nullable=False),
        sa.Column('verdict', sa.JSON(), nullable=True),
        sa.Column('created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('updated', sa.Integer(), server_default='0', nullable=False),
    )


def downgrade():
    op.drop_table('missions')
