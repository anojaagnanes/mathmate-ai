import io
import zipfile
import pytest
from app.work_review import review_work
from app.docx_text import extract_docx
from app.document_text import DocumentError


def test_first_inverse_error_and_downstream():
    result=review_work(['2x + 6 = 14','2x = 14 + 6','x = 10'])
    assert result['first_incorrect_step']==2
    assert result['error_category']=='inverse_operation'
    assert result['verified_correction']=='2*x = 14 - (6)'
    assert result['lines'][2]['status']=='dependent'
    assert result['corrected']['solution']=='4'


@pytest.mark.parametrize('lines',[
    ['2x+6=14','2x=8','x=4'],['2x+6=14','x+3=7','x=4'],
    ['2(x+3)=14','2x+6=14','x=4'],['1/2+1/4=3/4'],['sqrt(16)=4'],['sin(pi/2)=1']])
def test_supported_correct_work(lines):
    assert review_work(lines)['status']=='correct'


def test_normalization_is_reviewed_never_silent():
    result=review_work(['Step 1: 2x + 6 = 14','2) 2x = 14 − 6','x = 4'])
    assert result['status']=='review_required'
    assert result['lines'][0]['original'].startswith('Step 1:')
    assert review_work([r['normalized'] for r in result['lines']])['status']=='correct'
    assert review_work(['3 × 4 = 12'])['status']=='review_required'


@pytest.mark.parametrize('line',['x=?','__import__("os")=1','x=4 # answer','x=4=4','Now subtract six','x^2+5x+6=0','x/x=1'])
def test_unsupported_never_becomes_a_math_mistake(line):
    r=review_work(['2x+6=14',line])
    assert r['status']=='unable_to_verify'
    assert r['first_incorrect_step'] is None


@pytest.mark.parametrize('line',['x=8','4x=8','0*x=0'])
def test_lost_or_changed_solutions(line):
    assert review_work(['2x=8',line])['first_incorrect_step']==2


def test_workflow_and_ownership(client,auth):
    r=client.post('/api/v1/work/review',json={'steps':['2x+6=14','2x=20','x=10']},headers=auth)
    assert r.status_code==200,r.text
    review=r.json();assert review['id']
    teach=client.post(f"/api/v1/work/{review['id']}/teach",json={'language':'English'},headers=auth).json()
    assert teach['mode'] == 'Mia'
    assert client.post(f"/api/v1/work/{review['id']}/practice",json={'answer':'10'},headers=auth).json()['state']=='NEEDS_RETEACHING'
    assert client.post(f"/api/v1/work/{review['id']}/practice",json={'answer':'x=5'},headers=auth).json()['state']=='MASTERED'
    other=client.post('/api/v1/auth/register',json={'name':'Other','email':'work@example.com','password':'Another-long-password-123'}).json()
    assert client.post(f"/api/v1/work/{review['id']}/practice",json={'answer':'5'},headers={'Authorization':'Bearer '+other['access_token']}).status_code==404


def test_docx_order_tables_and_unsupported_math():
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w') as z:
        z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Question 1</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>2x+6=14</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>')
    assert extract_docx(data.getvalue())['text']=='Question 1\n2x+6=14'
    with pytest.raises(DocumentError):extract_docx(b'not a document')


def test_teaching_schema_and_failure_fallback(client, auth, monkeypatch):
    from app.providers import WorkTeaching
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        WorkTeaching.model_validate({'explanation': 'Only one field'})
    with pytest.raises(ValidationError):
        WorkTeaching.model_validate(dict(misconception='', explanation='Keep balance.', strategy='', encouragement='', answer='invented'))
    review=client.post('/api/v1/work/review',json={'steps':['2x+6=14','2x=20']},headers=auth).json()
    class Failed:
        async def teach_work(self,*args):raise RuntimeError('simulated provider failure')
    monkeypatch.setattr('app.main.get_provider',lambda *args:Failed())
    response=client.post(f"/api/v1/work/{review['id']}/teach",json={'language':'English'},headers=auth)
    assert response.status_code==200
    assert response.json()['mode'] == 'Mia'
    assert response.json()['guidance']['explanation']==review['message']


def test_docx_rejects_encoded_entity_declarations():
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w') as z:
        z.writestr('word/document.xml','<!DOCTYPE doc [<!ENTITY secret "bad">]><doc>&secret;</doc>'.encode('utf-16'))
    with pytest.raises(DocumentError):extract_docx(data.getvalue())


def test_photographed_sequence_review_to_answer():
    r=review_work(['III. 3n + 4 = Tn','3n + 4 = 40','3n = 36','n = 12'])
    assert r['normalization_required']
    r=review_work([line['normalized'] for line in r['lines']])
    assert r['normalization_required'] and '40' in r['message']
    r=review_work([line['normalized'] for line in r['lines']])
    assert r['status']=='correct' and r['corrected']['solution']=='12'


def test_sequence_does_not_invent_value_or_match_unrelated_equation():
    for lines in (['3n+4=T_n'],['3n+4=Tn','2n+4=40'],['3n+4=Tn','3n+4=?']):
        r=review_work(lines)
        assert r['corrected'] is None and not r['normalization_required']
