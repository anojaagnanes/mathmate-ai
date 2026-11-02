import asyncio
import json
import sqlite3
import httpx
import pytest
from app.config import settings
from app.providers import MetaAIProvider, MockAIProvider, get_provider, _cache
from app.meta_usage import reserve

HTTP_CLIENT = httpx.AsyncClient

def test_expired_enable_window_never_calls(meta,monkeypatch):
    monkeypatch.setattr(settings,'meta_enabled_until',1)
    assert isinstance(get_provider('expired'),MockAIProvider)
    with pytest.raises(RuntimeError,match='disabled'):asyncio.run(MetaAIProvider('expired').request([]))
    assert meta==[]

def test_estimated_cost_limit_and_session_private_usage(meta,monkeypatch):
    from app.meta_usage import summary,record,success
    monkeypatch.setattr(settings,'meta_estimated_cost_budget_usd',0.00001)
    with pytest.raises(RuntimeError,match='cost budget'):reserve('one',2000,1000)
    monkeypatch.setattr(settings,'meta_estimated_cost_budget_usd',1)
    call=reserve('one',20,10);record(call,8,5,3);success(call)
    own=summary('one');other=summary('two')
    assert own['session_requests']==1 and own['input_tokens']==5 and own['output_tokens']==3
    assert own['live_verified'] and other['session_requests']==0 and other['session_tokens']==0

@pytest.mark.parametrize('status',[401,429,500,503])
def test_http_failures_are_not_retried(meta,monkeypatch,status):
    original=HTTP_CLIENT;calls=[]
    def handler(request):calls.append(1);return httpx.Response(status,json={'error':'test'})
    monkeypatch.setattr('app.providers.httpx.AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    with pytest.raises(httpx.HTTPStatusError):asyncio.run(MetaAIProvider('failure').request([]))
    assert len(calls)==1


@pytest.fixture
def meta(monkeypatch, tmp_path):
    for key, value in dict(ai_provider='meta', meta_enabled=True, model_api_key='test-secret',
                           meta_model='muse-spark-1.3', meta_host='meta', meta_request_budget=3,
                           meta_token_budget=10000, meta_session_request_limit=2,
                           meta_usage_db=str(tmp_path/'usage.db')).items():
        monkeypatch.setattr(settings,key,value)
    _cache.clear()
    calls=[]
    def handle(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':'A checked explanation.'}}], 'usage':{'total_tokens':15}})
    original=httpx.AsyncClient
    monkeypatch.setattr('app.providers.httpx.AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handle),**kw))
    return calls


def test_disabled_has_no_network_or_ledger(meta, monkeypatch):
    monkeypatch.setattr(settings,'meta_enabled',False)
    assert isinstance(get_provider('session'),MockAIProvider)
    with pytest.raises(RuntimeError,match='disabled'):
        asyncio.run(MetaAIProvider('session').request([]))
    assert meta==[]


def test_duplicate_requests_cache_and_usage_is_recorded(meta):
    async def run():
        provider=MetaAIProvider('session')
        return await asyncio.gather(provider.request([{'role':'user','content':'why'}]),provider.request([{'role':'user','content':'why'}]))
    assert len(asyncio.run(run()))==2
    assert len(meta)==1
    with sqlite3.connect(settings.meta_usage_db) as db:
        assert db.execute('SELECT COUNT(*),actual FROM calls').fetchone()==(1,15)


def test_session_and_global_budgets_persist(meta):
    reserve('one',10);reserve('one',10)
    with pytest.raises(RuntimeError,match='limit'):reserve('one',10)
    reserve('two',10)
    with pytest.raises(RuntimeError,match='limit'):reserve('three',10)


def test_token_budget_and_missing_session_fail_closed(meta,monkeypatch):
    monkeypatch.setattr(settings,'meta_token_budget',5)
    with pytest.raises(RuntimeError,match='limit'):reserve('one',10)
    with pytest.raises(RuntimeError,match='session'):reserve('',1)
    assert meta==[]


def test_bad_model_never_calls_network(meta,monkeypatch):
    monkeypatch.setattr(settings,'meta_model','invented-model')
    with pytest.raises(RuntimeError,match='configured'):asyncio.run(MetaAIProvider('one').request([]))
    assert meta==[]


def test_failure_consumes_reservation_without_retry(meta,monkeypatch):
    class FailedClient:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,*args,**kwargs):raise httpx.ReadTimeout('test')
    monkeypatch.setattr('app.providers.httpx.AsyncClient',FailedClient)
    with pytest.raises(httpx.ReadTimeout):asyncio.run(MetaAIProvider('one').request([]))
    with sqlite3.connect(settings.meta_usage_db) as db:
        assert db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]==1


def test_baseten_omits_unsupported_schema_mode(meta,monkeypatch):
    monkeypatch.setattr(settings,'meta_host','baseten')
    monkeypatch.setattr(settings,'baseten_api_key','test-baseten')
    monkeypatch.setattr(settings,'meta_model','meta-models/muse-spark-open')
    # Fixture text is not JSON: reject it without a second chargeable call.
    with pytest.raises(ValueError):asyncio.run(MetaAIProvider('one').interpret('question'))
    assert len(meta)==1
    assert 'response_format' not in meta[0]
    assert meta[0]['messages'][0]['role']=='system'
