# Scrapers (`backend/scrapers`)

This package handles fetching and parsing data from parliamentary websites (Camera.it, Senato.it).

## Files

-   **`camera.py`**: Scraper for Camera dei Deputati (Resoconti Stenografici).
-   **`senate.py`**: Scraper for Senato della Repubblica (Resoconti Stenografici).
-   **`utils.py`**: Shared logic (HTTP client, Participant validation, `Speech` dataclass).
-   **`rosters.py`**: Fetches official lists of MPs for validation (Wikidata/sparql).

## Architecture

The scrapers follow a unified design:
1.  **Session List**: Fetch available sessions (HTML parsing).
2.  **Speech Extraction**: Parse each session's stenographic report.
3.  **Validation**: Match speaker names against `rosters.py` to ensure high data quality (discard unknown speakers).
4.  **Enrichment**: Add party, role (Government/President), and profile URLs.

## Shared Utilities (`utils.py`)
To prevent code duplication, `utils.py` provides:
-   `get_http_client(use_cloudscraper=...)`: Unified HTTP client factory.
-   `validate_participant(...)`: Centralized Logic to check names against rosters.
-   `Speech`: Standardized Data Class for speech objects.

## How to Add a New Scraper
1.  Create `backend/scrapers/new_source.py`.
2.  Import `Speech`, `get_http_client` from `.utils`.
3.  Implement `fetch_speeches(limit, ...)` matching the signature of other scrapers.
4.  Use `validate_participant` to clean speaker names.

## Testing
-   Run `pytest backend/tests/test_scrapers.py`.
-   Scrapers are **mocked** in tests to avoid network calls.
