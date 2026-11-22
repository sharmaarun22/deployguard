import hmac

from fastapi import Header, HTTPException, status

from backend.app.config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if settings.api_key and (
        x_api_key is None or not hmac.compare_digest(x_api_key, settings.api_key)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
        )
