# Frameworks Integration Guide

## FastAPI Testing

**Basic FastAPI Test Setup (TestClient)**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
```

**FastAPI Database Overrides**
Override dependencies for testing.
```python
from app.database import get_db

@pytest.fixture
def client(test_db):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

## Async Testing

Requires `pytest-asyncio`. Configure `asyncio_mode = auto` in `pytest.ini`.

**Async Functions**
Mark tests with `@pytest.mark.asyncio`.
```python
import pytest

@pytest.mark.asyncio
async def test_fetch_data(mocker):
    # Setup async mock
    mock_resp = mocker.AsyncMock()
    mock_resp.json.return_value = {"data": "test"}
    # ... patch session ...
    result = await fetch_data("http://test")
    assert result["data"] == "test"
```

**Async FastAPI Client (httpx)**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
```

**Async Fixtures**
Use `async def` and `yield` for async setup/teardown.
```python
@pytest.fixture
async def async_db_session():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSession(async_engine) as session:
        yield session
        
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```
