from app.providers import MockAIProvider

def test_context_uses_server_verified_math_and_language(client,auth,monkeypatch):
    class Provider:
        name='test Meta'
        async def teach_work(self,*args):pass
        async def explain(self,message,verified):
            assert 'Tamil' in message and 'pizza' in message
            assert verified['verified'] and verified['solution']=='4'
            return 'ஒரு விளக்கம்.'
    monkeypatch.setattr('app.main.get_provider',lambda *_:Provider())
    response=client.post('/api/v1/tutor/real-world',headers=auth,json={'equation':'2x+3=11','context':'pizza','language':'Tamil'})
    assert response.status_code==200
    assert response.json()['mode']=='test Meta'

def test_review_context_is_owned_and_uses_corrected_result(client,auth,monkeypatch):
    review=client.post('/api/v1/work/review',headers=auth,json={'steps':['1/2+1/4=2/6']}).json()
    class Provider:
        name='test Meta'
        async def teach_work(self,*args):pass
        async def explain(self,message,verified):
            assert verified['solution']=='3/4'
            return 'Three quarters of the same pizza.'
    monkeypatch.setattr('app.main.get_provider',lambda *_:Provider())
    body={'equation':'99','review_id':review['id'],'context':'pizza'}
    assert client.post('/api/v1/tutor/real-world',headers=auth,json=body).status_code==200
    other=client.post('/api/v1/auth/register',json={'name':'Other','email':'other2@example.com','password':'Long-password-123'}).json()
    assert client.post('/api/v1/tutor/real-world',headers={'Authorization':'Bearer '+other['access_token']},json=body).status_code==404

def test_no_mock_story_claimed_as_ai(client,auth,monkeypatch):
    monkeypatch.setattr('app.main.get_provider',lambda *_:MockAIProvider())
    assert client.post('/api/v1/tutor/real-world',headers=auth,json={'equation':'2x+3=11'}).status_code==503
    assert client.post('/api/v1/tutor/real-world',headers=auth,json={'equation':'not maths'}).status_code==422
