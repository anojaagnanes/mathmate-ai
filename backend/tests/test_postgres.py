"""Optional real PostgreSQL migration/persistence check in an isolated temporary schema."""
import os
import uuid
from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, text, inspect
from sqlalchemy.orm import Session
from app import db as database
from app.models import User, Topic, QuizQuestion, QuizAttempt


@pytest.mark.skipif(not os.getenv('TEST_POSTGRES_URL'), reason='TEST_POSTGRES_URL not configured; no PostgreSQL runtime available')
def test_postgres_migrations_and_persistence(monkeypatch):
    url = os.environ['TEST_POSTGRES_URL']
    if not url.startswith('postgresql'):
        pytest.fail('TEST_POSTGRES_URL must use PostgreSQL.')
    schema = 'mathmate_test_' + uuid.uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url)

    @event.listens_for(engine, 'connect')
    def select_schema(connection, record):
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}"')
        connection.commit()

    try:
        monkeypatch.setattr(database, 'engine', engine)
        command.upgrade(Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini')), 'head')
        with Session(engine) as db:
            db.add(User(id='postgres-test-user', email='pg-test@example.com', name='Postgres test', password_hash='not-a-login'))
            db.add(Topic(id='equations', title='Equations', description='Test'))
            db.flush()
            db.add(QuizQuestion(id='postgres-test-question', user_id='postgres-test-user', topic_id='equations', equation='2x=8', difficulty=1, hinted=False))
            db.flush()
            db.add(QuizAttempt(user_id='postgres-test-user', question_id='postgres-test-question', correct=True, hinted=False))
            db.commit()
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT count(*) FROM quiz_attempts')) == 1
            assert connection.scalar(text('SELECT submitted_at FROM quiz_attempts')) > 10**18
        assert len(inspect(engine).get_table_names(schema=schema)) == 17
    finally:
        engine.dispose()
        # Only the uniquely generated schema created by this test is removed.
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()
