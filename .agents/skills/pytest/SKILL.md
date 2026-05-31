---
name: pytest
description: "Use this skill whenever the user says 'write tests for', 'debug these tests', 'create a test suite', 'mock this function', or 'check test coverage'. Do NOT use this skill for frontend testing (Jest/Cypress) or non-Python testing. Reads context to generate TDD-aligned pytest code."
version: 1.0.0
---

# pytest

## Overview

This skill provides a complete set of guidelines and reference material for creating, debugging, and structuring tests in Python using the `pytest` framework. By analyzing the user's request and the codebase context, you will leverage these references to generate idiomatic, clean, and well-structured tests using features like fixtures, parametrization, and mocking.

## References

Determine the context of the user's request and read the appropriate reference file before generating the test code:

- **If the user asks for basic tests, assertions, or parametrization:**
  Read `references/01-core-pytest.md`
- **If the code involves complex dependencies, databases, or requires mocking:**
  Read `references/02-fixtures-mocking.md`
- **If the code uses FastAPI or Asyncio (`async`/`await`):**
  Read `references/03-frameworks.md`
- **CRITICAL - Before writing any final test code:**
  Read `references/04-best-practices.md` to ensure your code follows the AAA pattern, naming conventions, and avoids anti-patterns.

## Workflow

1. **Read the source code:** Understand the target function/class, its inputs, outputs, and side effects.
2. **Identify dependencies:** Note if the code relies on databases, external APIs, FastAPI requests, or async logic.
3. **Read the appropriate reference:** Based on the dependencies identified in step 2, read the correct file(s) from the `References` section.
4. **Read Best Practices:** Review `references/04-best-practices.md` to set up the test structure.
5. **Apply the AAA Pattern:** Structure your test clearly using the Arrange, Act, and Assert blocks.
6. **Return the code:** Produce the final test file applying all relevant fixtures, mocks, or parameters.

## Output Format

Return the test code using standard Markdown Python code blocks. Ensure the following structure:
- **Imports:** Place standard library imports first, followed by third-party imports (like `pytest`), and then project-specific imports.
- **Fixtures:** Define any required fixtures before the test functions.
- **Test Functions:** Follow the `test_<behavior_being_tested>` naming convention. Include comments separating the Arrange, Act, and Assert sections if helpful for clarity.

## Edge Cases

- **Code with mixed async/sync logic:** Clearly separate async test functions (marked with `@pytest.mark.asyncio`) and sync ones. Ensure the correct async fixtures are used.
- **Unclear dependencies:** If a function uses an external library that isn't clearly injectable, use `pytest-mock` (`mocker.patch`) to isolate the test from the network or database.
- **Missing setup instructions:** Do not guess the database schema; mock the data objects instead unless the user provides clear `conftest.py` setups.

## Examples

**Example 1: Basic Math Function**
*Input:* "Write tests for this simple add function: `def add(a, b): return a + b`"
*Output Expected:*
```python
import pytest

# Applied from references/01-core-pytest.md (Parametrization) and references/04-best-practices.md (AAA)
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (-1, 1, 0),
    (0, 0, 0)
])
def test_add_calculates_correct_sum(a, b, expected):
    # Arrange & Act
    result = add(a, b)
    
    # Assert
    assert result == expected
```

**Example 2: API Mocking**
*Input:* "Mock this function to test its error handling: `def fetch_data(): return requests.get('http://api').json()`"
*Output Expected:*
```python
import pytest
from requests.exceptions import Timeout

# Applied from references/02-fixtures-mocking.md
def test_fetch_data_handles_timeout(mocker):
    # Arrange
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = Timeout("Connection timed out")
    
    # Act & Assert
    with pytest.raises(Timeout):
        fetch_data()
```