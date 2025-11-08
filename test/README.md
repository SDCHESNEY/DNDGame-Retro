# Test Suite for LLM Dungeon Master

This directory contains comprehensive tests for Phase 1: Core MVP functionality.

## Test Structure

```
test/
├── conftest.py              # Test configuration and fixtures
├── test_api.py             # FastAPI endpoint tests (14 tests)
├── test_config.py          # Configuration management tests (7 tests)
├── test_llm_provider.py    # LLM provider tests (10 tests)
├── test_models.py          # Database model tests (8 tests)
└── test_prompts.py         # Prompt template tests (7 tests)
```

## Running Tests

### Run All Tests
```bash
python -m pytest test/ -v
```

### Run Specific Test File
```bash
python -m pytest test/test_api.py -v
```

### Run Tests by Pattern
```bash
# Run all provider tests
python -m pytest test/ -k "provider" -v

# Run all model tests
python -m pytest test/ -k "model" -v
```

### Run with Coverage (requires pytest-cov)
```bash
pip install pytest-cov
python -m pytest test/ --cov=llm_dungeon_master --cov-report=html
```

### Quiet Mode (Summary Only)
```bash
python -m pytest test/ -q
```

## Test Categories

### API Tests (`test_api.py`)
Tests all REST API endpoints:
- Session management (create, list, get)
- Player management (create, list)
- Character management (create, list, filter)
- Message handling (create, list, types)
- Error responses (404, validation)

### Configuration Tests (`test_config.py`)
Tests configuration and settings:
- Default values
- Environment variable loading
- CORS configuration
- Database URL parsing
- Provider validation

### LLM Provider Tests (`test_llm_provider.py`)
Tests AI provider abstraction:
- Mock provider responses
- OpenAI provider initialization
- Streaming functionality
- Error handling
- Provider factory

### Model Tests (`test_models.py`)
Tests database models:
- CRUD operations
- Relationships
- Default values
- Timestamps
- Data integrity

### Prompt Tests (`test_prompts.py`)
Tests DM prompt templates:
- System messages
- Session start prompts
- Combat prompts
- Roll formatting
- Template validation

## Fixtures

Defined in `conftest.py`:

- **engine** - In-memory SQLite database engine
- **session** - Database session for tests
- **client** - FastAPI test client
- **sample_player** - Pre-created player for tests
- **sample_session** - Pre-created game session
- **sample_character** - Pre-created character

## Current Test Results

✅ **46 tests passing**  
✅ **0 tests failing**  
✅ **100% success rate**

See [PHASE1_TEST_RESULTS.md](../docs/PHASE1_TEST_RESULTS.md) for detailed results.

## Adding New Tests

1. Create a new test file: `test_<feature>.py`
2. Import necessary fixtures from `conftest.py`
3. Write test functions starting with `test_`
4. Use async/await for async operations with `@pytest.mark.asyncio`
5. Run tests to verify

Example:
```python
def test_my_feature(session):
    """Test description."""
    # Arrange
    data = create_test_data()
    
    # Act
    result = perform_action(data)
    
    # Assert
    assert result.is_valid()
```

## Dependencies

- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `fastapi.testclient` - API testing
- `sqlmodel` - Database testing

Install with:
```bash
uv pip install pytest pytest-asyncio
```

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    python -m pytest test/ -v --tb=short
```

## Notes

- Tests use in-memory SQLite database (no data persistence)
- Each test is isolated and independent
- Tests clean up after themselves
- Mock provider used by default (no API costs)
