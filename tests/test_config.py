import pytest
from pydantic import ValidationError

from backend.app.config import Settings


def test_reads_documented_api_key_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPLOYGUARD_API_KEY", "configured-key")
    monkeypatch.delenv("API_KEY", raising=False)
    configured = Settings(_env_file=None)
    assert configured.api_key == "configured-key"


def test_production_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEPLOYGUARD_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(ValidationError, match="required in production"):
        Settings(_env_file=None, environment="production")
