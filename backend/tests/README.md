# Test Suite (`backend/tests`)

This directory contains the automated test suite for the backend.

## Files

-   **`conftest.py`**: Shared Pytest fixtures (Mock data, sample HTML).
-   **`fixtures.py`**: Additional specialized fixtures.
-   **`test_scrapers.py`**: Tests for Camera and Senate parsers.
-   **`test_pipeline.py`**: Integration tests for the data pipeline.
-   **`test_utils.py`**: Unit tests for utility functions.
-   **`test_rosters.py`**: Tests for roster loading and validation.
-   **`test_orchestrator.py`**: Tests for the Analytics Orchestrator.
-   **Analyzers**: Specific tests for each analysis module:
    -   `test_topics.py`, `test_rhetoric.py`, `test_sentiment.py`
    -   `test_identity.py`, `test_relations.py`, `test_temporal.py`
    -   `test_alliances.py`, `test_factions.py`, `test_speaker.py`

## How to Run Tests

### Run All Tests
```bash
pytest backend/tests
```

### Run Fast Tests Only
(Excludes slow integration tests using markers)
```bash
pytest backend/tests -m "not slow"
```

### Run Specific Test File
```bash
pytest backend/tests/test_scrapers.py -v
```

## Writing Tests
-   **Mock Network Calls**: Never make real HTTP requests in tests (use `unittest.mock`).
-   **Use Fixtures**: Use `conftest.py` fixtures for common data (e.g., `sample_speeches_df`).
-   **performance**: Avoid importing heavy libraries (torch, sklearn) at the top level if not needed.
