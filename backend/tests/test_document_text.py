import io
import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from app.document_text import extract_pdf, DocumentError


def pdf_bytes(text='2x + 3 = 11', pages=1, encrypted=False):
    writer = PdfWriter()
    for _ in range(pages):
        page = writer.add_blank_page(width=300, height=200)
        if text:
            font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
            page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
            stream = DecodedStreamObject()
            stream.set_data(f'BT /F1 18 Tf 20 100 Td ({text}) Tj ET'.encode())
            page[NameObject('/Contents')] = writer._add_object(stream)
    if encrypted:
        writer.encrypt('test-password')
    output = io.BytesIO(); writer.write(output)
    return output.getvalue()


def test_pdf_text_requires_review(client, auth):
    response = client.post('/api/v1/math/question', data={'question': 'Please check this question'}, files={'file': ('question.pdf', pdf_bytes(), 'application/pdf')}, headers=auth)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['route'] == 'document' and result['status'] == 'review_required'
    assert result['solution'] is None and result['upload'] is None
    assert result['document']['text'] == '2x + 3 = 11'
    assert result['question'] == 'Please check this question'
    confirmed = client.post('/api/v1/math/question', data={'question': result['document']['text']}, headers=auth).json()
    assert confirmed['solution']['solution'] == '4'


def test_scan_has_honest_fallback(client, auth):
    response = client.post('/api/v1/math/question', files={'file': ('scan.pdf', pdf_bytes(text=''), 'application/pdf')}, headers=auth)
    result = response.json()
    assert response.status_code == 200
    assert result['status'] == 'manual_required' and result['document']['text'] == ''
    assert 'scanned PDF' in result['message']


@pytest.mark.parametrize('raw', [b'%PDF-invalid', pdf_bytes(pages=6), pdf_bytes(encrypted=True), pdf_bytes(text='x'*4001)])
def test_reject_invalid_or_excessive_documents(client, auth, raw):
    response = client.post('/api/v1/math/question', files={'file': ('bad.pdf', raw, 'application/pdf')}, headers=auth)
    assert response.status_code == 422


def test_pdf_size_mime_auth_and_deadline(client, auth):
    raw = pdf_bytes()
    assert client.post('/api/v1/math/question', files={'file': ('x.pdf', raw, 'application/pdf')}).status_code == 401
    assert client.post('/api/v1/math/question', files={'file': ('x.png', raw, 'image/png')}, headers=auth).status_code == 422
    assert client.post('/api/v1/math/question', files={'file': ('x.pdf', b'%PDF-'+b'x'*(5*1024*1024), 'application/pdf')}, headers=auth).status_code == 413
    with pytest.raises(DocumentError, match='timed out'):
        extract_pdf(raw, timeout=0)
    assert extract_pdf(raw)['text'] == '2x + 3 = 11'


def test_pdf_worker_capacity(monkeypatch):
    from threading import BoundedSemaphore
    monkeypatch.setattr('app.document_text.SLOTS', BoundedSemaphore(0))
    with pytest.raises(DocumentError, match='busy'):
        extract_pdf(pdf_bytes())


def test_mixed_pdf_preserves_page_order_and_unread_pages(client, auth):
    from pypdf import PdfReader
    writer = PdfWriter()
    for text in ['2x+6=14', '', '3n+4=40']:
        writer.add_page(PdfReader(io.BytesIO(pdf_bytes(text))).pages[0])
    stream = io.BytesIO(); writer.write(stream)
    result = client.post('/api/v1/math/question', files={'file': ('mixed.pdf', stream.getvalue(), 'application/pdf')}, headers=auth).json()
    assert result['document']['page_text'] == [{'page': 1, 'text': '2x+6=14'}, {'page': 2, 'text': ''}, {'page': 3, 'text': '3n+4=40'}]
    assert result['document']['unread_pages'] == [2]
    assert result['status'] == 'review_required' and result['solution'] is None
