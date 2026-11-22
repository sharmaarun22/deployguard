import pytest

from backend.app.services.notifications import validate_webhook_url


def test_rejects_local_webhook_target() -> None:
    with pytest.raises(ValueError):
        validate_webhook_url("http://127.0.0.1/hook")


def test_rejects_invalid_webhook_scheme() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        validate_webhook_url("ftp://example.com/hook")


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1/hook",
        "https://10.0.0.2/hook",
        "https://service.internal/hook",
        "https://user:pass@example.com/hook",
    ],
)
def test_rejects_non_public_or_credentialed_webhook_targets(url: str) -> None:
    with pytest.raises(ValueError):
        validate_webhook_url(url)


def test_accepts_https_webhook() -> None:
    url = "https://example.com/deployguard"
    assert validate_webhook_url(url) == url
