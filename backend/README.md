# Backend Documentation

This directory contains the Python backend for the Political Analysis Dashboard.

## Structure

- **`analyzers/`**: Modular analysis engine (Orchestrator, Registry, Analyzers).
- **`config/`**: Configuration files (Settings, Roles, Stopwords, etc.).
- **`core/`**: Core shared logic (Caching, Aggregation, Clustering).
- **`scrapers/`**: Web scrapers for Camera and Senato.
- **`tests/`**: Test suite (Pytest).
- **`utils/`**: General utilities (Text processing, Retry logic).
- **`export_data.py`**: Main entry point for data processing pipeline.
- **`pipeline.py`**: Embedding and dimensionality reduction pipeline.

## how to Run

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Pipeline**:
    ```bash
    python export_data.py
    ```

## Development

-   **Adding Dependencies**: Add to `requirements.txt`.
-   **Testing**: Run `pytest tests/`.
