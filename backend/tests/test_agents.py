import asyncio
import json
import httpx
import pytest
from app.config import settings
from app.providers import MetaAIProvider, WorkTeaching, _cache
from app.agents.vision import VisionAgent
from app.agents.practice import PracticeAgent
from app.agents.orchestrator import TeachingSession
from app.work_review import review_work

@pytest.mark.parametrize('line,correct',[('1/2 + 1/4 = 2/6',False),('1/2 + 1/4 = 3/4',True),('1/2 = 2/4',True),('1/2 = 1/3',False),('1/2 > 1/4',True),('1/2 < 1/4',False)])
def test_fraction_verification(line,correct):
    r=review_work([line]);assert (r['status']=='correct')==correct
    assert r['corrected']['verified']
    if '+' in line:assert r['corrected']['solution']=='3/4'

def test_first_error_and_dependent_lines():
    r=review_work(['1/2+1/4=2/6','2/6=1/3'])
    assert r['first_incorrect_step']==1 and r['lines'][1]['status']=='dependent'

def test_detective_only_identifies_matching_pattern():
    assert 'adding both numerators and denominators' in review_work(['1/2+1/4=2/6'])['message']
    assert 'matches adding' not in review_work(['1/2+1/4=1/8'])['message']

def test_memory_and_three_attempt_support(client,auth):
    review=client.post('/api/v1/work/review',headers=auth,json={'steps':['1/2+1/4=2/6']}).json()
    memory=client.get('/api/v1/work/memory',headers=auth).json()
    assert memory['revision']=='1/2 + 1/4 = ?'
    for attempt in range(3):
        response=client.post(f"/api/v1/work/{review['id']}/practice",headers=auth,json={'answer':'99'}).json()
        assert response['supportive_visual']==(attempt==2)
    other=client.post('/api/v1/auth/register',json={'name':'Other','email':'other@example.com','password':'Long-password-123'}).json()
    assert client.get('/api/v1/work/memory',headers={'Authorization':'Bearer '+other['access_token']}).json()['patterns']==[]

def test_explanation_style_forwarded(client,auth,monkeypatch):
    review=client.post('/api/v1/work/review',headers=auth,json={'steps':['1/2+1/4=2/6']}).json()
    class Provider:
        name='test provider'
        async def teach_work(self,verified,language):
            assert language=='Tamil' and verified['teaching_style']=='chocolate'
            return WorkTeaching(misconception='Pattern',explanation='Explanation',strategy='Visual',encouragement='Try again')
    monkeypatch.setattr('app.main.get_provider',lambda *_:Provider())
    response=client.post(f"/api/v1/work/{review['id']}/teach",headers=auth,json={'language':'Tamil','style':'chocolate'})
    assert response.status_code==200

def test_meta_crop_payload_is_compact_without_changing_original(client,auth,monkeypatch):
    import io
    from PIL import Image
    image=io.BytesIO();Image.new('RGBA',(256,256),'white').save(image,format='PNG',compress_level=0)
    original=image.getvalue()
    class Provider:
        name='test recognizer'
        async def transcribe(self,raw,mime):
            assert mime=='image/jpeg' and len(raw)<len(original)
            with Image.open(io.BytesIO(raw)) as decoded:assert decoded.size==(256,256)
            return ['2x+3=11']
    monkeypatch.setattr('app.main.meta_active',lambda:True)
    monkeypatch.setattr('app.main.get_provider',lambda *_:Provider())
    response=client.post('/api/v1/handwriting/upload',headers=auth,files={'file':('crop.png',original,'image/png')})
    assert response.json()['steps']==['2x+3=11']
    assert image.getvalue()==original

def test_practice_adapts_without_repetition():
    p=PracticeAgent(); first=p.generate(); seen=[first['equation']]
    for level,history in [(1,[{'correct':True}]),(2,[{'correct':True}]*3),(0,[{'correct':False}])]:
        new=p.generate(history=history,seen=seen);seen.append(new['equation'])
        assert new['difficulty']==level and len(seen)==len(set(seen))
        import sympy as sp
        from app.math_parser import parse
        assert parse(new['equation'])[0]==sp.Rational(new['answer'])
        assert 'answer' not in p.public(new)

def test_hackathon_vision_request_and_response(monkeypatch,tmp_path):
    for name,value in dict(ai_provider='meta',meta_enabled=True,meta_host='baseten',meta_base_url='https://inference.baseten.co/v1',meta_model='meta-models/muse-spark-open-1026',model_api_key='test-key',baseten_api_key='',meta_request_budget=2,meta_token_budget=50000,meta_usage_db=str(tmp_path/'usage.db')).items():monkeypatch.setattr(settings,name,value)
    _cache.clear();calls=[]; original=httpx.AsyncClient
    def handler(request):
        payload=json.loads(request.content);calls.append(payload)
        assert str(request.url)=='https://inference.baseten.co/v1/chat/completions'
        assert payload['model']=='meta-models/muse-spark-open-1026'
        assert 'response_format' not in payload
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'steps':['1/2 + 1/4 = ?']})}}],'usage':{'total_tokens':25}})
    monkeypatch.setattr('app.providers.httpx.AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    result=asyncio.run(TeachingSession(MetaAIProvider('test-session')).extract(b'fixture','image/png'))
    assert result.requires_confirmation and result.ambiguous_lines==[1]
    assert calls[0]['messages'][-1]['content'][1]['image_url']['url'].startswith('data:image/png;base64,')

def test_fraction_api_flow_and_next_question(client,auth,monkeypatch):
    r=client.post('/api/v1/work/review',headers=auth,json={'steps':['1/2+1/4=2/6']})
    assert r.status_code==200,r.text
    review=r.json();assert review['corrected']['solution']=='3/4'
    assert 'answer' not in review['practice']
    class Provider:
        name='test Meta response'
        async def teach_work(self,verified,language):
            assert verified['corrected']['solution']=='3/4'
            return WorkTeaching(misconception='Possible denominator addition.',explanation='Use a common denominator.',strategy='Rewrite halves as quarters.',encouragement='Try again.')
    monkeypatch.setattr('app.main.get_provider',lambda *_:Provider())
    t=client.post(f"/api/v1/work/{review['id']}/teach",headers=auth,json={'language':'English'})
    assert t.status_code==200 and t.json()['guidance']['explanation']=='Use a common denominator.'
    answer=client.post(f"/api/v1/work/{review['id']}/practice",headers=auth,json={'answer':'2/3'})
    assert answer.status_code==200 and answer.json()['correct']
    assert answer.json()['next_question']['difficulty']==1
    assert answer.json()['next_question']['equation']!=review['practice']['equation']

def test_meta_practice_is_computed_and_bad_difficulty_falls_back():
    from app.providers import FractionPracticeDraft
    class Provider:
        async def draft_practice(self,*args):return FractionPracticeDraft(numerator_a=1,denominator_a=3,numerator_b=1,denominator_b=6)
    p=PracticeAgent()
    result=asyncio.run(p.generate_with_provider(Provider(),'addition',[{'correct':True}],[]))
    assert result['answer']=='1/2' and 'source' not in result
    fallback=asyncio.run(p.generate_with_provider(Provider(),'addition',[],[]))
    assert 'source' not in fallback and fallback['difficulty']==0
