import os
import secrets

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader


API_KEY = os.environ["API_KEY"]

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def verify_api_key(
    key: str = Security(api_key_header)
) -> None:
    if key is None or not secrets.compare_digest(key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida o ausente",
        )