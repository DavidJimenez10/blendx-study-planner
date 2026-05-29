# Best Practices & Cheat Sheet

## Test Structure & Conventions

**Organization**
Keep tests in a `tests/` directory mirroring the `src/` or `app/` structure.
Shared fixtures belong in `conftest.py`.

**Naming**
- ✅ `test_user_creation_with_valid_email()`
- ❌ `test_user1()`

## AAA Pattern (Arrange-Act-Assert)

Keep tests logically separated into three steps:
```python
def test_user_creation():
    # Arrange: Set up data and dependencies
    user_data = {"email": "test@example.com"}
    service = UserService(db=mock_db)
    
    # Act: Perform the action
    result = service.create_user(user_data)
    
    # Assert: Verify outcome
    assert result.email == "test@example.com"
```

## Anti-patterns & Common Pitfalls

- ❌ **Tests depending on order**: Tests must run independently. Use fixtures to isolate states.
- ❌ **No teardown**: Always close DB connections or delete temp files (use `yield` in fixtures).
- ❌ **Testing internals**: Test behavior (inputs/outputs), not implementation details.
- ❌ **God fixtures**: Avoid fixtures that do everything. Compose small, focused fixtures.

## Terminal Commands & Coverage (Cheat Sheet)

**Basic Commands**
- `pytest`: Run all tests.
- `pytest -v`: Verbose output.
- `pytest -s`: Show print statements.
- `pytest tests/test_api.py::test_create`: Run a specific test.

**Markers & Filtering**
- `pytest -m "unit and not slow"`: Run by marker.
- `pytest -k "auth"`: Run tests matching a keyword.
- `pytest -x`: Stop on first failure.
- `pytest --lf`: Run only last failed tests.

**Coverage (`pytest-cov`)**
- `pytest --cov=app --cov-report=html`: Generate HTML coverage report.
- `pytest --cov=app --cov-report=term-missing`: Show lines missing coverage in terminal.
- `pytest --cov-fail-under=80`: Fail CI if coverage is < 80%.

**Debugging**
- `pytest --pdb`: Drop into debugger on failure.
