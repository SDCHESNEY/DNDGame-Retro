# Test Suite

This directory contains the test suite for the LLM Dungeon Master project.

## Test Files

### Phase 1 Tests
- `conftest.py` - Shared test fixtures and configuration
- `test_api.py` - Tests for FastAPI REST endpoints and WebSocket (14 tests + 4 Phase 2)
- `test_config.py` - Tests for configuration management (7 tests)
- `test_llm_provider.py` - Tests for LLM provider abstraction (10 tests)
- `test_models.py` - Tests for database models (8 tests)
- `test_prompts.py` - Tests for prompt templates (7 tests)

### Phase 2 Tests (NEW)
- `test_dm_service.py` - Tests for DM service and LLM integration (20 tests)
  - Basic functionality (4 tests)
  - Rate limiting (3 tests)
  - Token tracking (3 tests)
  - Retry logic (2 tests)
  - Streaming responses (2 tests)
  - Integration scenarios (2 tests)

## Running Tests

```bash
# Run all tests
pytest test/

# Run with verbose output
pytest test/ -v

# Run specific test file
pytest test/test_api.py
pytest test/test_dm_service.py

# Run with coverage
pytest test/ --cov=llm_dungeon_master

# Run Phase 2 tests only
pytest test/test_dm_service.py -v
```

## Test Statistics

**Total Tests:** 66
- Phase 1: 46 tests
- Phase 2: 20 tests

**All tests passing:** ✅ 66/66

**Execution Time:** ~45 seconds

## Test Coverage

### Phase 1 Coverage
- **Infrastructure**: Database setup, configuration, models
- **API Endpoints**: REST API and WebSocket endpoints
- **LLM Integration**: Provider abstraction and mock responses
- **Prompts**: Template formatting and content

### Phase 2 Coverage (NEW)
- **DM Service**: Session management, action processing, roll handling
- **Rate Limiting**: Per-session request throttling
- **Token Tracking**: Usage monitoring and limits
- **Retry Logic**: Exponential backoff on failures
- **Streaming**: Real-time response generation
- **Error Handling**: Rate limits, token limits, API failures

## Test Approach

All tests use:
- **In-memory SQLite databases** - No external database required
- **Mock LLM providers** - No API keys or costs
- **Isolated fixtures** - Each test runs independently
- **Fast execution** - Average <1 second per test

## Phase 2 Test Highlights

### DMService Tests
The new `test_dm_service.py` validates:

1. **Core Operations**
   - Starting sessions with DM opening messages
   - Processing player actions with context
   - Handling dice rolls with DM responses
   - Managing conversation history

2. **Protection Mechanisms**
   - Rate limiting enforcement (20 req/min)
   - Token limit enforcement (100k per session)
   - Timestamp cleanup for rate limits
   - Per-session isolation

3. **Reliability**
   - Retry logic with exponential backoff
   - Graceful failure handling
   - Streaming with error handling

4. **Integration Scenarios**
   - Complete game session workflows
   - Multiple players in same session
   - Token usage tracking over time

## Debugging Failed Tests

If tests fail, use these commands:

```bash
# Show detailed error output
pytest test/ -v --tb=long

# Show only failures
pytest test/ -v --tb=short -x

# Run specific failing test
pytest test/test_dm_service.py::TestRateLimiting::test_rate_limit_enforcement -v
```

## Adding New Tests

When adding tests:
1. Use fixtures from `conftest.py`
2. Follow existing test patterns
3. Use descriptive test names
4. Add docstrings explaining what's tested
5. Test both success and error cases

Example:
```python
@pytest.mark.asyncio
async def test_my_feature(dm_service, session, sample_session):
    """Test that my feature works correctly."""
    result = await dm_service.my_method(session, sample_session.id)
    assert result is not None
```

## Continuous Integration

Tests are designed to run in CI/CD:
- No external dependencies
- Fast execution
- Deterministic results
- Clear failure messages
