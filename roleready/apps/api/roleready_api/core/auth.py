import os
import requests
import time
from jose import jwt
from fastapi import HTTPException, Header

SUPABASE_URL = os.getenv('SUPABASE_URL')
JWKS_URL = f"{SUPABASE_URL}/auth/v1/jwks"
JWKS_CACHE = {"keys": None, "ts": 0}

def _get_jwks():
    now = time.time()
    if not JWKS_CACHE["keys"] or now - JWKS_CACHE["ts"] > 3600:
        resp = requests.get(JWKS_URL, timeout=5)
        resp.raise_for_status()
        JWKS_CACHE["keys"] = resp.json()
        JWKS_CACHE["ts"] = now
    return JWKS_CACHE["keys"]

def require_user(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail='Missing bearer token')
    token = authorization.split()[1]
    jwks = _get_jwks()
    try:
        claims = jwt.decode(token, jwks, algorithms=['RS256'], options={"verify_aud": False})
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid token')
    user_id = claims.get('sub') or claims.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail='No user in token')
    return {"user_id": user_id, "claims": claims}
