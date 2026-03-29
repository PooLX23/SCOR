from functools import lru_cache

import httpx
import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=True)


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    jwks_url = f'https://login.microsoftonline.com/{settings.entra_tenant_id}/discovery/v2.0/keys'
    response = httpx.get(jwks_url, timeout=10)
    response.raise_for_status()
    return response.json()


def validate_entra_token(credentials: HTTPAuthorizationCredentials) -> dict:
    token = credentials.credentials
    try:
        headers = jwt.get_unverified_header(token)
        key = next((k for k in _get_jwks()['keys'] if k['kid'] == headers.get('kid')), None)
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Brak klucza podpisu')

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=settings.entra_audience,
            issuer=f'https://login.microsoftonline.com/{settings.entra_tenant_id}/v2.0',
        )
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Niepoprawny token: {exc}') from exc
