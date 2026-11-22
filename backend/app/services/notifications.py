from __future__ import annotations

import asyncio
from urllib.parse import urlparse

import httpx


def validate_webhook_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Webhook URL must use HTTP or HTTPS")
    if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Local webhook targets are not allowed")
    return url


async def send_webhook(url: str, payload: dict[str, object], attempts: int = 3) -> bool:
    validate_webhook_url(url)
    timeout = httpx.Timeout(5.0, connect=2.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for attempt in range(attempts):
            try:
                response = await client.post(url, json=payload)
                if response.is_success:
                    return True
            except httpx.HTTPError:
                pass
            if attempt < attempts - 1:
                await asyncio.sleep(0.25 * (2**attempt))
    return False
