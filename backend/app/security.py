import hashlib
import secrets
import time
import uuid
from collections import defaultdict, deque
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User, RefreshToken

passwords = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
attempts: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request):
    key = request.client.host if request.client else 'unknown'
    now = time.time()
    queue = attempts[key]
    while queue and queue[0] < now - 60:
        queue.popleft()
    if len(queue) >= 20:
        raise HTTPException(429, 'Too many authentication attempts. Try again in a minute.')
    queue.append(now)


def csrf(request: Request):
    origin = request.headers.get('origin')
    client = request.headers.get('x-mathmate-client')





    if origin != settings.frontend_origin or client != 'web':
        raise HTTPException(403, 'Request origin or CSRF header missing.')


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def issue(db: Session, user: User, response: Response, family=None):
    token = secrets.token_urlsafe(48)
    family = family or str(uuid.uuid4())
    db.add(RefreshToken(digest=digest(token), user_id=user.id, family=family, expires=int(time.time()) + 604800))
    db.commit()
    response.set_cookie('mathmate_refresh', token, httponly=True, secure=settings.secure_cookies, samesite='strict', max_age=604800, path='/api/v1/auth')
    access = jwt.encode({'sub': user.id, 'sid': family, 'iat': int(time.time()), 'exp': int(time.time()) + 900, 'iss': 'mathmate'}, settings.jwt_secret, algorithm='HS256')
    return {'access_token': access, 'token_type': 'bearer', 'user': {'id': user.id, 'name': user.name, 'email': user.email}}


def current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    try:
        if not credentials:
            raise ValueError()
        claims = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=['HS256'], issuer='mathmate', options={'require': ['exp', 'iat', 'sub', 'sid']})
        user = db.get(User, claims['sub'])
        active = db.scalar(select(RefreshToken).where(RefreshToken.family == claims['sid'], RefreshToken.user_id == claims['sub'], RefreshToken.revoked.is_(False), RefreshToken.expires > int(time.time())))
        if not user or not active:
            raise ValueError()
        request.state.meta_session = claims['sid']
        return user
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(401, 'Please sign in again.')


def revoke_family(db, family):
    db.execute(update(RefreshToken).where(RefreshToken.family == family).values(revoked=True))
    db.commit()
