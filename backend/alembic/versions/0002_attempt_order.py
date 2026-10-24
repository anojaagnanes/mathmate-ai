"""Preserve historical rows and add precise ordering for new quiz submissions."""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('quiz_attempts', sa.Column('submitted_at', sa.BigInteger(), nullable=False, server_default='0'))
    op.execute('UPDATE quiz_attempts SET submitted_at = CAST(created AS BIGINT) * 1000000000 WHERE submitted_at = 0')
    op.create_index('ix_quiz_attempts_submitted_at', 'quiz_attempts', ['submitted_at'])


def downgrade():
    op.drop_index('ix_quiz_attempts_submitted_at', table_name='quiz_attempts')
    op.drop_column('quiz_attempts', 'submitted_at')
