# Core Module (`backend/core`)

This package contains shared business logic and core algorithms used across the application.

## Files

-   **`cache.py`**: Manages caching of heavy artifacts (Embeddings, DataFrames).
-   **`clustering.py`**: Logic for K-Means clustering and label generation.
-   **`aggregation.py`**: Functions to aggregate data for analytics (e.g., grouping by party/date).
-   **`__init__.py`**: Exports core functions.

## Key Functionalities

### Caching
-   **`CacheManager`**: Handles loading/saving of pickle files.
-   Ensures expensive computations (embeddings) are reused between runs.

### Clustering
-   **`perform_clustering`**: Wraps Scikit-Learn K-Means.
-   **`generate_cluster_labels`**: Uses TF-IDF/LLM to name clusters.
-   **Lazy Loading**: Heavy imports (SentenceTransformer, sklearn) are lazy-loaded to speed up startup/testing.

## Scalability
-   Logic here should be **pure** and **stateless** where possible.
-   Avoid UI-specific or scraping-specific code here.
-   If a new algorithm is needed, creates a new module (e.g., `backend/core/prediction.py`).
