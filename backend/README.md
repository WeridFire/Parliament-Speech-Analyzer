# Backend Documentation

This directory contains the Python backend for the Political Analysis Dashboard.

## Structure

- **`analyzers/`**: Modular analysis engine (Orchestrator, Registry, Analyzers).
  Each analyzer declares its dependencies and the sample sizes at which its
  output is meaningful; the orchestrator honours both.
- **`config/`**: Settings, roles, stopwords, lexicons, topic definitions.
- **`core/`**: `SpeechDataset` (keeps speeches and their arrays aligned),
  fingerprinted cache, clustering, aggregation, artifact writer.
- **`ingestion/`**: Sitting discovery via open data, shared crawler, roster
  matching, transports with anti-bot challenge detection.
- **`tools/`**: Baseline capture, schema generation, payload migration.
- **`utils/`**: Text, dates, retry, HTTP.
- **`export_data.py`**: Main entry point for the pipeline.
- **`pipeline.py`**: Embeddings, dimensionality reduction, clustering.

## How to run

```bash
pip install -r requirements.txt -r ../requirements-dev.txt
python -m spacy download it_core_news_sm

python -m backend.ingestion.verify --source both   # check coverage first
python -m backend.export_data                      # full pipeline
```

## Key invariants

- **Speeches and their arrays are narrowed together.** Slice through
  `SpeechDataset.subset()`; never index a numpy array with a pandas label index.
- **Embeddings are cached by content fingerprint**, not by row count.
- **A blocked or failed fetch is reported, never returned as an empty result.**

## Development

- **Adding dependencies**: runtime in `requirements.txt`, test-only in
  `../requirements-dev.txt`.
- **Testing**: `pytest backend/tests` from the project root.
- **Regenerating the payload contract**: `python -m backend.tools.dump_schema`.
