# Frontend Unit Tests

This directory contains unit tests for the Server Monitoring Dashboard Frontend.

## Setup

### Install Test Dependencies

```bash
# Install pytest and coverage tools
pip install pytest pytest-cov pytest-mock
```

### Run All Tests

```bash
# From the Frontend directory
cd /home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_validation.py

# Run specific test class
pytest tests/test_validation.py::TestValidatePercentage

# Run specific test
pytest tests/test_validation.py::TestValidatePercentage::test_valid_percentage_int
```

## Test Structure

```
tests/
├── __init__.py                 # Package init
├── conftest.py                 # Pytest configuration and fixtures
├── test_validation.py          # Validation module tests
├── test_utils.py              # Utils module tests
└── README.md                   # This file
```

## Test Coverage

Current test coverage by module:

- `validation.py`: ~95% (all core functions)
- `utils.py`: ~85% (utility functions)

Target: >80% overall coverage

## Writing New Tests

### Test File Naming

- Test files must start with `test_`
- Test classes must start with `Test`
- Test functions must start with `test_`

### Example Test

```python
import pytest
from module import function_to_test

class TestMyFunction:
    """Tests for my_function"""

    def test_valid_input(self):
        result = function_to_test("valid")
        assert result == "expected"

    def test_invalid_input_raises_error(self):
        with pytest.raises(ValueError):
            function_to_test("invalid")

    def test_with_fixture(self, sample_data):
        result = function_to_test(sample_data)
        assert result is not None
```

### Using Fixtures

Fixtures are defined in `conftest.py` and are automatically available in all tests:

```python
def test_with_server_metrics(sample_server_metrics):
    # sample_server_metrics is automatically provided
    assert sample_server_metrics['server_name'] == 'TestServer1'
```

## Available Fixtures

- `sample_server_metrics` - Single server metrics dict
- `sample_historical_data` - List of historical metrics
- `sample_user_data` - List of user activity data
- `multiple_servers_metrics` - List of metrics for 5 servers
- `warning_server_metrics` - Metrics that trigger warnings
- `critical_server_metrics` - Metrics that trigger critical alerts
- `offline_server_metrics` - Metrics for offline server
- `empty_metrics` - Empty metrics dict
- `mock_api_response_success` - Successful API response
- `mock_api_response_error` - Error API response

## Test Markers

Mark tests with custom markers:

```python
@pytest.mark.unit
def test_simple_function():
    pass

@pytest.mark.integration
def test_api_call():
    pass

@pytest.mark.slow
def test_expensive_operation():
    pass
```

Run specific markers:

```bash
# Run only unit tests
pytest -m unit

# Run everything except slow tests
pytest -m "not slow"

# Run integration tests only
pytest -m integration
```

## Continuous Integration

Tests should pass before merging code. Run the full test suite:

```bash
# Run all tests with coverage
pytest --cov=. --cov-report=term-missing --cov-fail-under=80 -v

# This will:
# - Run all tests verbosely (-v)
# - Generate coverage report (--cov)
# - Show missing lines (--cov-report=term-missing)
# - Fail if coverage < 80% (--cov-fail-under=80)
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running pytest from the Frontend directory:

```bash
cd /home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend
pytest
```

### Module Not Found

Ensure the parent directory is in the Python path. This is handled automatically by `conftest.py`, but you can also do:

```bash
export PYTHONPATH=/home/ayassin/Developer/ServerDashboardContainer/srcs/Frontend:$PYTHONPATH
pytest
```

## Test Coverage Goals

| Module | Current | Target |
|--------|---------|--------|
| validation.py | 95% | 95% |
| utils.py | 85% | 90% |
| api_client.py | 0% | 70% |
| data_processing.py | 0% | 80% |
| components.py | 0% | 60% |

## Future Tests Needed

1. **API Client Tests** (`test_api_client.py`)
   - Test retry logic
   - Mock HTTP requests

2. **Data Processing Tests** (`test_data_processing.py`)
   - Test DataFrame operations
   - Test aggregations
   - Test anomaly detection

3. **Components Tests** (`test_components.py`)
   - Test component generation
   - Test error handling in components

4. **Integration Tests**
   - End-to-end API flows
   - Dashboard rendering

## Best Practices

1. **One assertion per test** (when possible)
2. **Use descriptive test names** - test name should describe what is being tested
3. **Test edge cases** - None, empty, invalid inputs
4. **Use fixtures** - Don't repeat test data setup
5. **Mock external dependencies** - Tests should not depend on API/database
6. **Keep tests fast** - Mark slow tests with `@pytest.mark.slow`
7. **Test both success and failure paths**

## Running Specific Test Suites

```bash
# Run only validation tests
pytest tests/test_validation.py -v

# Run only utils tests
pytest tests/test_utils.py -v

# Run all unit tests
pytest tests/ -m unit -v

# Run with coverage for specific module
pytest tests/test_validation.py --cov=validation --cov-report=term-missing
```

## Debugging Tests

```bash
# Run with print statements visible
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests only
pytest --lf

# Run with Python debugger on failure
pytest --pdb

# Increase verbosity
pytest -vv
```

## Performance Testing

```bash
# Show slowest 10 tests
pytest --durations=10

# Profile test execution time
pytest --durations=0
```

---

**Last Updated:** 2025-10-01
**Test Framework:** pytest 7.x+
**Python Version:** 3.8+
