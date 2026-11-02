import os
os.environ['JWT_SECRET'] = 'test-only-secret-never-use-in-production-123456789'
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['AI_PROVIDER'] = 'mock'
os.environ['VISION_PROVIDER'] = 'default'
os.environ['FRONTEND_ORIGIN'] = 'http://localhost:3000'
os.environ['META_ENABLED'] = 'false'
os.environ['META_ENABLED_UNTIL'] = '0'
os.environ['META_ESTIMATED_COST_BUDGET_USD'] = '0'
os.environ['META_BASE_URL'] = ''
os.environ['META_HOST'] = 'meta'
os.environ['META_MODEL'] = 'muse-spark-1.3'
os.environ['MODEL_API_KEY'] = ''
os.environ['BASETEN_API_KEY'] = ''

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.db import Base, get_db
from app.main import app
from app.models import Topic, Lesson
from app.security import attempts


@pytest.fixture
def client(monkeypatch,tmp_path):
    from app.config import settings
    monkeypatch.setattr(settings,'meta_usage_db',str(tmp_path/'test-usage.db'))
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as db:
        db.add_all([Topic(id='equations', title='Equations', description='Learn'), Topic(id='graphs', title='Graphs', description='See')])
        db.flush()
        db.add(Lesson(id='balance', topic_id='equations', title='Balance', equation='2x+3=11'))
        db.commit()
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    attempts.clear()
    with TestClient(app, headers={'Origin': 'http://localhost:3000', 'X-MathMate-Client': 'web'}) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def auth(client):
    response = client.post('/api/v1/auth/register', json={'name': 'Ada', 'email': 'ada@example.com', 'password': 'Long-password-123'})
    assert response.status_code == 201, response.text
    return {'Authorization': 'Bearer ' + response.json()['access_token']}
