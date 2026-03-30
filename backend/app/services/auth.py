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


def _allowed_issuers(tenant_id: str) -> set[str]:
    return {
        f'https://login.microsoftonline.com/{tenant_id}/v2.0',
        f'https://login.microsoftonline.com/{tenant_id}/',
        f'https://sts.windows.net/{tenant_id}/',
    }


def validate_entra_token(credentials: HTTPAuthorizationCredentials) -> dict:
    token = credentials.credentials
    try:
        headers = jwt.get_unverified_header(token)
        unverified_payload = jwt.decode(token, options={'verify_signature': False, 'verify_aud': False})
        key = next((k for k in _get_jwks()['keys'] if k['kid'] == headers.get('kid')), None)
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Brak klucza podpisu')

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=settings.entra_audience,
            options={'verify_iss': False},
        )

        token_tenant = unverified_payload.get('tid')
        allowed = _allowed_issuers(settings.entra_tenant_id)
        if token_tenant:
            allowed |= _allowed_issuers(token_tenant)

        issuer = payload.get('iss')
        if issuer not in allowed:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f'Niepoprawny token: Invalid issuer ({issuer})',
            )

        return payload
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Niepoprawny token: {exc}') from exc
