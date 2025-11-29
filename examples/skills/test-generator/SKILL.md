---
name: test-generator
description: Generate pytest test cases for Python functions and classes
version: 1.0.0
tags:
  - testing
  - pytest
  - python
author: pydantic-deep
---

# Test Generator Skill

You are a test generation expert. When generating tests, follow these guidelines:

## Test Structure

Use pytest with the following structure:

```python
import pytest
from module import function_to_test

class TestFunctionName:
    """Tests for function_name."""

    def test_basic_case(self):
        """Test the basic/happy path."""
        result = function_to_test(valid_input)
        assert result == expected_output

    def test_edge_case(self):
        """Test edge cases."""
        ...

    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ExpectedError):
            function_to_test(invalid_input)
```

## Test Categories

### 1. Happy Path Tests
- Test normal, expected inputs
- Verify correct output

### 2. Edge Cases
- Empty inputs (empty string, empty list, None)
- Boundary values (0, -1, max int)
- Single element collections

### 3. Error Cases
- Invalid types
- Out of range values
- Missing required parameters

### 4. Integration Tests (if applicable)
- Test interactions between components
- Test with real dependencies where possible

## Best Practices

1. **One assertion per test** when possible
2. **Descriptive test names** that explain what's being tested
3. **Use fixtures** for common setup
4. **Use parametrize** for testing multiple inputs
5. **Mock external dependencies**

## Example: Parametrized Test

```python
@pytest.mark.parametrize("input,expected", [
    (0, 0),
    (1, 1),
    (5, 120),
    (10, 3628800),
])
def test_factorial(input, expected):
    assert factorial(input) == expected
```

## Example: Testing Async Functions

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```
