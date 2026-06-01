import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_openai_client
from app.core.database import get_db
from app.main import app
from app.models.base import Base

_TEST_DB_URL = "sqlite:///./test.db"
_engine = create_engine(_TEST_DB_URL, connect_args={"check_same_thread": False})
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


class _MockOpenAIClient:
    tasks_to_return: list = []
    last_prompt: str | None = None
    embedding_to_return: list[float] | None = None
    chat_response: str = ""
    generate_tasks_fn: object = None

    def generate_tasks(self, prompt, response_model):
        self.last_prompt = prompt
        if self.generate_tasks_fn:
            return self.generate_tasks_fn(prompt, response_model)
        return self.tasks_to_return

    def generate_embedding(self, text):
        if self.embedding_to_return is not None:
            return self.embedding_to_return
        return [0.0] * 1536

    def chat(self, messages):
        return self.chat_response or "Mock response"


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
    _mock_llm.embedding_to_return = None
    _mock_llm.chat_response = ""
    _mock_llm.generate_tasks_fn = None

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


@pytest.fixture
def plan(client):
    user = client.post("/users", json={"name": "Alice"}).json()
    return client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Learn Python", "hours_per_week": 10.0},
    ).json()


@pytest.fixture
def plan_for_agent(client):
    user = client.post("/users", json={"name": "AgentUser"}).json()
    return client.post(
        "/plans",
        json={
            "user_id": user["id"],
            "goal": "Master React 18",
            "hours_per_week": 10.0,
            "target_date": "2026-09-01",
            "constraints": "All tasks must include practical exercises",
        },
    ).json()
