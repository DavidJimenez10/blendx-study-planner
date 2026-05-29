# Core pytest Guide

## Basic Testing Patterns

**Simple Test Functions**
- Naming convention: Files `test_*.py`, Functions `test_*`.
- Use standard `assert`.

```python
def test_add():
    assert 2 + 3 == 5
    assert -1 + 1 == 0
```

**Test Classes for Organization**
- Group tests logically without `__init__`.
- Class name must start with `Test`.

```python
class TestCalculator:
    def test_add(self):
        assert 2 + 3 == 5
```

## Assertions and Expected Failures

**Exception Raising**
Use `pytest.raises` to verify exceptions.
```python
import pytest

def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)
```

**Approximate Equality**
For floating-point comparison.
```python
def test_float_comparison():
    assert 0.1 + 0.2 == pytest.approx(0.3)
```

## Parametrization (Data-Driven)

Run the same test with different inputs using `@pytest.mark.parametrize`.

**Basic Parametrization**
```python
import pytest

@pytest.mark.parametrize("a,b,expected", [
    (2, 3, 5),
    (-1, 1, 0),
    (0, 0, 0),
])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected
```

**Parametrize with IDs**
Make test outputs clearer by naming test cases.
```python
@pytest.mark.parametrize("input_data,expected", [
    pytest.param({"name": "Alice"}, "Alice", id="valid_name"),
    pytest.param({}, None, id="missing_name"),
])
def test_extract_name(input_data, expected):
    assert extract_name(input_data) == expected
```

## Test Markers

**Built-in Markers**
- `@pytest.mark.skip(reason="Not implemented")`: Skip unconditionally.
- `@pytest.mark.skipif(condition, reason="...")`: Skip based on condition.
- `@pytest.mark.xfail(reason="Known bug")`: Expect failure.

**Custom Markers**
Group tests logically (e.g., slow, integration).
```python
@pytest.mark.slow
def test_expensive_operation():
    pass
```
*Note: Custom markers should be registered in `pytest.ini`.*

```ini
# pytest.ini
[pytest]
markers =
    slow: marks tests as slow
    integration: marks integration tests
```
