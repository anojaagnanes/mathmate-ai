from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from app import db as database


def test_migrations_preserve_existing_records(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///' + str(tmp_path / 'migration-test.db'))
    monkeypatch.setattr(database, 'engine', engine)
    cfg = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    command.upgrade(cfg, '0001')
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO users (id,email,name,password_hash) VALUES ('u','preserve@example.com','Preserved','test')"))
        connection.execute(text("INSERT INTO topics (id,title,description) VALUES ('equations','Linear','Test')"))
        connection.execute(text("INSERT INTO quiz_questions (id,user_id,topic_id,equation,difficulty,hinted) VALUES ('q','u','equations','x=4',1,0)"))
        connection.execute(text("INSERT INTO quiz_attempts (id,user_id,question_id,correct,hinted,created) VALUES ('a','u','q',1,0,1700000000)"))
    command.upgrade(cfg, 'head')
    with engine.connect() as connection:
        assert connection.scalar(text('SELECT name FROM users')) == 'Preserved'
        assert connection.scalar(text('SELECT submitted_at FROM quiz_attempts')) == 1700000000000000000
        assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '0002'
    assert len(inspect(engine).get_table_names()) == 17  # 16 app tables plus alembic_version
    engine.dispose()
