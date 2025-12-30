# Utils (`backend/utils`)

General utility functions used throughout the application.

## Files

-   **`text.py`**: Text processing utilities (cleaning, normalization).
-   **`retry.py`**: Decorators for retrying failed operations (network calls).
-   **`logger.py`**: Logging configuration (if applicable).

## Usage

### Retry Decorator
```python
from backend.utils import retry

@retry(max_attempts=3, delay=1.0)
def fetch_data():
    ...
```

### Text Cleaning
```python
from backend.utils.text import clean_text

cleaned = clean_text("  some dirty   text ")
```
