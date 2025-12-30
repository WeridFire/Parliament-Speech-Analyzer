# Analyzers (`backend/analyzers`)

This package allows for modular, extensible political analysis.

## Architecture

The system uses an **Orchestrator-Registry** pattern:
1.  **`BaseAnalyzer`**: Abstract base class for all analyzers.
2.  **`AnalyzerRegistry`**: Central registry where analyzers register themselves.
3.  **`AnalyticsOrchestrator`**: Coordinates execution of all registered analyzers.

## Files

-   **`orchestrator.py`**: The `AnalyticsOrchestrator` class. Input: raw data; Output: full analysis dictionary.
-   **`registry.py`**: The `AnalyzerRegistry` class.
-   **`base.py`**: The `BaseAnalyzer` interface.
-   **`config.yaml`**: Configuration for enabled analyzers (not yet fully active, future proofing).

### Analyzer Implementations
-   **`topics/topics.py`**: Topic extraction and clustering.
-   **`rhetoric/rhetoric.py`**: Rhetorical style analysis.
-   **`sentiment/sentiment.py`**: Sentiment analysis.
-   **`temporal/temporal.py`**: Time-series analysis.
-   **`identity/identity.py`**: Analysis of specific speakers/parties.
-   **`relations/relations.py`**: Network/Relationship analysis.

## Deprecated Files
> [!WARNING]
> The following files are legacy and will be removed:
> - `analytics.py` (Old monolithic class)
> - `speaker_stats.py` (Old logic)
> - `alliances.py` (Old logic)

## How to Add a New Analyzer
1.  Create a new folder/module (e.g., `backend/analyzers/my_analysis/`).
2.  Inherit from `BaseAnalyzer`.
3.  Implement `analyze(self, df, ...)` and `key(self)`.
4.  Register it in `backend/analyzers/__init__.py` or via decorator.
