"""Order saved reviews by submission time; historical rows keep NULL (unknown time)."""
from alembic import op
import sqlalchemy as sa


revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('solution_feedback', sa.Column('submitted_at', sa.BigInteger(), nullable=True))
    op.create_index('ix_solution_feedback_submitted_at', 'solution_feedback', ['submitted_at'])


def downgrade():
    op.drop_index('ix_solution_feedback_submitted_at', table_name='solution_feedback')
    op.drop_column('solution_feedback', 'submitted_at')
