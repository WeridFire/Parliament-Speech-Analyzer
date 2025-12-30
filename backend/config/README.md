# Configuration Module (`backend/config`)

This package contains all configuration constants and static data for the application.

## Files

-   **`__init__.py`**: Exports key constants for easy access (e.g., `from backend.config import LEGISLATURE`).
-   **`settings.py`**: General settings (Legislature ID, Date ranges, Scraper limits).
-   **`roles.py`**: Government roles definitions and regex patterns.
-   **`stopwords.py`**: List of Italian stopwords for text analysis.
-   **`topic_clusters.py`**: Pre-defined semantic topics for clustering.
-   **`party_normalization.py`**: Mappings to normalize party names across sources.
-   **`analysis_keywords.py`**: Keywords for specific analyses (Sentiment, Crisis, Rhetoric).

## How to Modify

### Adding a New Setting
1.  Add the constant to `settings.py`.
2.  (Optional) Export it in `__init__.py` if it's widely used.

### Updating Stopwords
1.  Edit `stopwords.py`.
2.  The set `STOP_WORDS` is automatically exported.

### Adding a Minister/Role
1.  Edit `roles.py`.
2.  Add the role to `GOVERNMENT_ROLES`.
3.  The regex pattern `build_role_pattern()` will automatically include it.

## Scalability
-   Keep specific domains in separate files (e.g., don't put URL configs in `roles.py`).
-   Use `__init__.py` to provide a clean public API for the package.
