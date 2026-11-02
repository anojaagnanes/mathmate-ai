"""Mia agent trajectory traces."""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'mia_traces',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('tutor_sessions.id'), index=True, nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True, nullable=False),
        sa.Column('turn', sa.Integer(), server_default='0', nullable=False),
        sa.Column('step', sa.Integer(), server_default='0', nullable=False),
        sa.Column('kind', sa.String(12), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('created', sa.Integer(), server_default='0', nullable=False),
    )


def downgrade():
    op.drop_table('mia_traces')
