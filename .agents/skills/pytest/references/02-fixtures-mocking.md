# Fixtures and Mocking Guide

## Fixtures (Dependency Injection)

**Basic Fixtures**
Provide reusable data or objects.
```python
import pytest

@pytest.fixture
def sample_user():
    return {"id": 1, "name": "Alice"}

def test_user(sample_user):
    assert sample_user["name"] == "Alice"
```

**Fixture Scopes**
Control how often a fixture runs.
- `function` (default): Once per test.
- `class`: Once per test class.
- `module`: Once per test module.
- `session`: Once per test session.
```python
@pytest.fixture(scope="session")
def db_connection():
    return connect_to_db()
```

**Setup and Teardown**
Use `yield` to execute teardown code after the test.
```python
@pytest.fixture
def temp_file():
    # Setup
    f = create_temp_file()
    yield f
    # Teardown
    f.delete()
```

**Fixture Dependencies**
Fixtures can depend on other fixtures.
```python
@pytest.fixture
def db_session(db_connection):
    session = create_session(db_connection)
    yield session
    session.rollback()
```

## Mocking (pytest-mock)

Use the `mocker` fixture provided by `pytest-mock` to isolate tests.

**Mocking Functions**
```python
def test_get_user(mocker):
    # Mock requests.get
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {"id": 1, "name": "Alice"}
    
    mocker.patch("requests.get", return_value=mock_resp)
    
    result = fetch_user_data(1)
    assert result["name"] == "Alice"
```

**Mocking Class Methods**
```python
def test_service(mocker):
    service = UserService()
    mocker.patch.object(
        service, "get_user", return_value={"id": 1, "name": "Alice"}
    )
    assert service.get_user_name(1) == "Alice"
```

**Side Effects**
Simulate exceptions or sequential return values.
```python
def test_retry(mocker):
    mock_api = mocker.patch("requests.get")
    mock_api.side_effect = [
        Timeout(),
        mocker.Mock(json=lambda: {"status": "ok"})
    ]
    
    result = call_with_retry()
    assert mock_api.call_count == 2
```

**Spy on Calls**
Verify a function was called without altering its behavior.
```python
def test_spy(mocker):
    spy = mocker.spy(module, "my_func")
    module.run_workflow()
    spy.assert_called_once_with(arg=42)
```
