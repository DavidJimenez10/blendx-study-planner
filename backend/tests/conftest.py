import pytest
from app.api.deps import get_openai_client
from app.core.database import get_db
from app.main import app
from app.models.base import Base
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_TEST_DB_URL = "sqlite:///./test.db"
_engine = create_engine(_TEST_DB_URL, connect_args={"check_same_thread": False})
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


class _MockOpenAIClient:
    tasks_to_return: list = []
    last_prompt: str | None = None

    def generate_tasks(self, prompt, response_model):
        self.last_prompt = prompt
        return self.tasks_to_return


_mock_llm = _MockOpenAIClient()


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.OPENAI_API_KEY", "test-api-key")

    _mock_llm.tasks_to_return = []
    _mock_llm.last_prompt = None

    def _override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_openai_client] = lambda: _mock_llm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_llm():
    return _mock_llm
