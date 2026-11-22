from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app import main
from backend.app.config import settings
from backend.app.db import Base, get_db


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    test_engine = create_engine(database_url, connect_args={"check_same_thread": False})
    test_session = sessionmaker(bind=test_engine, expire_on_commit=False)
    monkeypatch.setattr(settings, "api_key", None)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db() -> Generator[Session, None, None]:
        with test_session() as session:
            yield session

    main.app.dependency_overrides[get_db] = override_get_db
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()
    test_engine.dispose()
