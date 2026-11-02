"""Persistent local request reservations, not a billing-provider spending cap."""
import hashlib
import sqlite3
import time
from .config import settings


def prepare(db):
    db.execute('CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY, session TEXT, reserved INTEGER, actual INTEGER, created REAL)')
    columns={row[1] for row in db.execute('PRAGMA table_info(calls)')}
    for name,kind in [('input_tokens','INTEGER'),('output_tokens','INTEGER'),('estimated_usd','REAL'),('model','TEXT'),('successful','INTEGER')]:
        if name not in columns:db.execute(f'ALTER TABLE calls ADD COLUMN {name} {kind}')

def reserve(session: str, tokens: int, output_limit: int = 0) -> int:
    if not session:
        raise RuntimeError('An authenticated session is required for enhanced answers.')
    with sqlite3.connect(settings.meta_usage_db, timeout=5) as db:
        prepare(db)
        db.execute('BEGIN IMMEDIATE')
        count, total = db.execute('SELECT COUNT(*), COALESCE(SUM(MAX(reserved,COALESCE(actual,0))),0) FROM calls').fetchone()
        session_hash = hashlib.sha256(session.encode()).hexdigest()
        used = db.execute('SELECT COUNT(*) FROM calls WHERE session=?', (session_hash,)).fetchone()[0]
        if count >= settings.meta_request_budget or used >= settings.meta_session_request_limit or total + tokens > settings.meta_token_budget:
            raise RuntimeError('Answer usage limit reached; answering with built-in explanations.')
        # Published standard rates, not a guarantee of the hackathon's billing.
        estimate=max(0,tokens-output_limit)*1.25/1_000_000+output_limit*4.25/1_000_000
        spent=db.execute('SELECT COALESCE(SUM(estimated_usd),0) FROM calls').fetchone()[0]
        if settings.meta_estimated_cost_budget_usd>0 and spent+estimate>settings.meta_estimated_cost_budget_usd:
            raise RuntimeError('Estimated cost budget reached; answering with built-in explanations.')
        cursor = db.execute('INSERT INTO calls(session,reserved,created,estimated_usd,model,successful) VALUES(?,?,?,?,?,0)', (session_hash,tokens,time.time(),estimate,settings.meta_model))
        return cursor.lastrowid


def record(call_id: int, total: int | None, input_tokens=None, output_tokens=None):
    with sqlite3.connect(settings.meta_usage_db, timeout=5) as db:
        db.execute('UPDATE calls SET actual=?,input_tokens=?,output_tokens=? WHERE id=?', (total,input_tokens,output_tokens,call_id))

def success(call_id):
    with sqlite3.connect(settings.meta_usage_db,timeout=5) as db:
        db.execute('UPDATE calls SET successful=1 WHERE id=?',(call_id,))

def summary(session):
    with sqlite3.connect(settings.meta_usage_db,timeout=5) as db:
        prepare(db)
        hashed=hashlib.sha256(session.encode()).hexdigest()
        count,actual,inputs,outputs=db.execute('SELECT COUNT(*),COALESCE(SUM(actual),0),COALESCE(SUM(input_tokens),0),COALESCE(SUM(output_tokens),0) FROM calls WHERE session=?',(hashed,)).fetchone()
        total=db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
        verified=db.execute('SELECT COUNT(*) FROM calls WHERE successful=1 AND model=?',(settings.meta_model,)).fetchone()[0]>0
        return dict(session_requests=count,session_tokens=actual,input_tokens=inputs,output_tokens=outputs,requests_remaining=max(0,min(settings.meta_request_budget-total,settings.meta_session_request_limit-count)),live_verified=verified,estimated_session_usd=round(inputs*1.25/1_000_000+outputs*4.25/1_000_000,6),billing_note='Estimate at standard rates; check your provider for actual usage. Older calls may lack token breakdown.')
