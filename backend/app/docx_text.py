"""Text-only DOCX extraction. No macros, embedded objects or external references executed."""
import io
import zipfile
import xml.etree.ElementTree as ET
from .document_text import DocumentError


def extract_docx(raw):
    if len(raw)>5*1024*1024:raise DocumentError('Choose a DOCX smaller than 5 MB.')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members=archive.infolist()
            if len(members)>500 or sum(m.file_size for m in members)>20*1024*1024:
                raise DocumentError('This document is too large after decompression. Export a shorter excerpt.')
            entry=archive.getinfo('word/document.xml')
            if entry.file_size>2*1024*1024:raise DocumentError('The document text is too large.')
            data=archive.read(entry)
        if b'\x00' in data or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():raise DocumentError('Unsupported document XML encoding or declarations.')
        root=ET.fromstring(data)
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
        lines=[]
        for paragraph in root.findall('.//w:p',ns):
            text=''.join(node.text or '' for node in paragraph.findall('.//w:t',ns)).strip()
            if paragraph.findall('.//m:oMath',ns):text+=' [Embedded equation: retype or export as an image]'
            if text:lines.append(text)
        text='\n'.join(lines)
        if len(text)>4000:raise DocumentError('Choose a shorter document, up to 4,000 text characters.')
        return {'text':text,'message':'Paragraph and table text extracted in document order. Embedded equations and images require manual entry or image upload; DOCX page boundaries are not available.'}
    except (KeyError,zipfile.BadZipFile,ET.ParseError,RuntimeError):
        raise DocumentError('This is not a readable DOCX. Export a valid DOCX or PDF.')
