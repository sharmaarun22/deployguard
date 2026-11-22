import pytest

from backend.app.services.notifications import validate_webhook_url


def test_rejects_local_webhook_target() -> None:
    with pytest.raises(ValueError, match="Local webhook"):
        validate_webhook_url("http://127.0.0.1/hook")


def test_rejects_invalid_webhook_scheme() -> None:
    with pytest.raises(ValueError, match="HTTP or HTTPS"):
        validate_webhook_url("ftp://example.com/hook")


def test_accepts_https_webhook() -> None:
    url = "https://example.com/deployguard"
    assert validate_webhook_url(url) == url
