"""PDF text extraction with bounded input, pages, output, time and concurrency."""
import io
import multiprocessing as mp
from threading import BoundedSemaphore

SLOTS = BoundedSemaphore(2)
MAX_BYTES = 5 * 1024 * 1024


class DocumentError(ValueError):
    pass


def _extract(raw):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw), strict=True)
    if reader.is_encrypted:
        raise DocumentError('Password-protected PDFs are not supported. Export an unlocked copy.')
    count = len(reader.pages)
    if not 1 <= count <= 5:
        raise DocumentError('Choose a PDF with 1–5 pages.')
    texts, empty, page_text = [], [], []
    for index, page in enumerate(reader.pages, 1):
        contents = page.get_contents()
        if contents is not None and len(contents.get_data()) > 2 * 1024 * 1024:
            raise DocumentError('A PDF page is too complex. Export a simpler or shorter document.')
        text = (page.extract_text() or '').strip()
        page_text.append({'page': index, 'text': text})
        if text:
            texts.append(text)
        else:
            empty.append(str(index))
        if sum(len(t) + 2 for t in texts) > 4000:
            raise DocumentError('This PDF contains too much text. Upload a shorter excerpt (up to 4,000 characters).')
    text = '\n\n'.join(texts)
    message = ('PDF text extracted. Review reading order, mathematical notation and every quantity before submitting.'
               if text else 'No embedded text was found. This may be a scanned PDF. Upload a page as an image for local OCR or type the question manually.')
    if text and empty:
        message += ' No text was extracted from page(s) ' + ', '.join(empty) + '; these pages may contain scans or diagrams and were not understood.'
    return {'text': text, 'mode': 'pdf_text' if text else 'manual', 'pages': count, 'message': message,
            'page_text': page_text, 'unread_pages': [int(index) for index in empty]}


def _worker(connection, raw):
    try:
        connection.send(('ok', _extract(raw)))
    except DocumentError as exc:
        connection.send(('error', str(exc)))
    except Exception:
        connection.send(('error', 'This PDF could not be read safely. Export a valid, unlocked PDF and try again.'))
    finally:
        connection.close()


def extract_pdf(raw, timeout=25):
    if not raw.startswith(b'%PDF-'):
        raise DocumentError('The file is not a valid PDF.')
    if len(raw) > MAX_BYTES:
        raise DocumentError('Choose a PDF no larger than 5 MB.')
    if not SLOTS.acquire(blocking=False):
        raise DocumentError('Document processing is busy. Please try again shortly.')
    context = mp.get_context('spawn')
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(child, raw), daemon=True)
    try:
        if timeout <= 0:
            raise DocumentError('PDF extraction timed out. Upload a simpler document.')
        process.start(); child.close()
        if not parent.poll(timeout):
            raise DocumentError('PDF extraction timed out. Upload a simpler document.')
        try:
            status, result = parent.recv()
        except EOFError:
            raise DocumentError('PDF extraction stopped safely. Try a simpler document.')
        if status == 'error':
            raise DocumentError(result)
        return result
    finally:
        if process.pid:
            process.join(.1)
            if process.is_alive():
                process.terminate(); process.join()
            process.close()
        parent.close(); child.close(); SLOTS.release()
