# Italian Parliament Speech Analyzer

A comprehensive NLP-powered analysis platform for Italian parliamentary discourse. This system automatically scrapes, processes, and analyzes speeches from both the **Camera dei Deputati** (Chamber of Deputies) and the **Senato della Repubblica** (Senate), providing insights into political communication patterns.

> [!NOTE]
> **Frontend Development**: The frontend web application is currently under active development.

> [!NOTE]
> **Data**: Camera dei Deputati May 2025 – June 2026 (the open data publishes no
> sittings after 17 June 2026), Senato August 2025 – October 2026.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Backend Features](#backend-features)
  - [Data Collection](#data-collection)
  - [Analysis Pipeline](#analysis-pipeline)
  - [Analytics Modules](#analytics-modules)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Tech Stack](#tech-stack)

---

## Overview

The Italian Parliament Speech Analyzer is designed to provide quantitative and qualitative insights into parliamentary discourse. It enables researchers, journalists, and citizens to understand how political parties and individual parliamentarians communicate, what topics they prioritize, and how their discourse evolves over time.

---

## Architecture

```
politics/
├── backend/
│   ├── analyzers/         # Modular analysis engine (registry + orchestrator)
│   ├── config/            # Settings, lexicons, topic definitions
│   ├── core/              # SpeechDataset, cache, clustering, artifact writer
│   ├── ingestion/         # Open-data discovery + crawlers + roster matching
│   ├── tools/             # Baseline capture, schema dump, payload migration
│   ├── utils/             # Text, dates, retry, HTTP
│   ├── export_data.py     # Main pipeline entry point
│   └── pipeline.py        # Embeddings, reduction, clustering
├── frontend/              # React web application
│   └── public/data/       # Generated payload (manifest + chunks)
├── docs/JSON_SCHEMA.md    # Payload contract (generated)
└── colab_notebook.ipynb   # Google Colab execution notebook
```

---

## Backend Features

### Data Collection

Sittings and member registers come from the **official open data** (SPARQL);
only the stenographic text itself is fetched from the chambers' websites.

| Source | Discovery | Text |
|--------|-----------|------|
| **Camera dei Deputati** | `dati.camera.it` — `ocd:seduta` | camera.it stenographic reports |
| **Senato della Repubblica** | `dati.senato.it` — `osr:SedutaAssemblea` | senato.it stenographic reports |

**Key Capabilities:**
- Configurable time range (default: 15 months back)
- Complete sitting index from open data — no listing pages to paginate or miss
- Member registers from open data, matched by an indexed name resolver that
  records how each attribution was reached
- Per-sitting caching, so an interrupted run resumes almost free
- Anti-bot challenges are detected and reported, never mistaken for "no data"

**Check coverage before a full run:**

```bash
python -m backend.ingestion.verify --source both --months 15
```

It prints, per chamber, how many sittings officially exist against how many were
fetched, parsed, blocked or failed, and exits non-zero when a chamber is blocked.

> [!NOTE]
> `senato.it` serves a CloudFront JavaScript challenge to automated clients.
> Install Playwright (`pip install playwright && playwright install chromium`)
> to enable the browser transport. The browser keeps one context for the whole
> run, so the challenge is solved once and later documents load in under a
> second. Senato document ids are read from the yearly chronological listing:
> the open-data sitting id is *not* the id of the stenographic report.

---

### Analysis Pipeline

The main data processing pipeline (`export_data.py`) orchestrates the following workflow:

1. **Data Fetching** — Retrieves parliamentary speeches from configured sources
2. **Text Cleaning** — Drops the chair (by role), short and unattributed speeches;
   normalises group labels from both chambers to one canonical name and bloc
3. **Embedding Generation** — Multilingual sentence embeddings, cached per text
4. **Topic Assignment** — Nearest configured topic in the *centred* embedding
   space (or K-Means when no topics are configured)
5. **Per-speech Features** — Every speech is read once: word and sentence counts,
   Gulpease, linguistic markers, stage directions (applause, protests), mentions
   of public figures, content-word lemmas (cached per text)
6. **Analysis** — Analyzers aggregate those columns for the whole period and for
   every year and month
7. **Export** — Outputs structured JSON for frontend consumption

A run over an unchanged corpus takes about 30 seconds for both chambers; only
new speeches are embedded and lemmatised. Each stage's duration is logged.

**Command-Line Options:**
```bash
python backend/export_data.py [OPTIONS]

--refetch                 # Force re-download of all speeches
--offline                 # Build the corpus from cached sittings only (no network)
--output-dir PATH         # Where to write the payload (default: frontend/public/data)
--reembed                 # Force regeneration of embeddings
--cloudscraper            # Route requests through cloudscraper
--source [camera|senate|both]  # Select data source
--clusters N              # Number of K-Means clusters (ignored when TOPIC_CLUSTERS is set)
--max-cache-age N         # Ignore cached speeches older than N days
--strict                  # Exit non-zero if any analyzer failed
```

Embeddings and lemmas are cached per text (keyed by a content digest and the
model), so a new sitting costs only its own speeches and a stale vector can
never be reused for a different text.

**Output** goes to `frontend/public/data/` as a manifest plus per-resource
chunks — see [docs/JSON_SCHEMA.md](docs/JSON_SCHEMA.md).

---

### Analytics Modules

The system employs a modular, registry-based architecture for analytics. Each
analyzer is independently configurable and declares the sample size it needs;
on a thin month it declines and the frontend shows the global figure instead,
saying so.

| Analyzer | What it measures |
|----------|------------------|
| **identity** | Share of each group's speeches per topic and its lift over the chamber; generalism (topic entropy, ≥20 speeches); distinctive vocabulary (weighted log-odds with an informative prior) |
| **topics** | Per topic: the members who intervene on it most, each group's involvement relative to its size, the words that characterise it |
| **blocs** | Majority (with the government) vs opposition: issue ownership measured on each side's share of attention, and the words that separate them |
| **relations** | Party affinity, internal homogeneity and closest cross-party pairs, in the centred embedding space |
| **reactions** | Applause and protests between groups, from the stage directions of the report (group attribution exists at the Camera only) |
| **mentions** | How often each group names a curated list of leaders, ministers and foreign heads of government |
| **temporal** | Monthly topic shares and monthly activity per bloc (global only) |
| **speaker** | Per-member activity, verbosity, linguistic rates, MATTR vocabulary richness, main topics and reactions drawn |
| **language** | Gulpease readability and "us vs them" polarization |

Removed after the audit, because they measured something other than what they
claimed: lexicon sentiment, populist/anti-establishment rhetoric, crisis index,
semantic drift, topic surfing, consistency index, factions, alliances (a
duplicate of the cross-party pairs) and thematic divergence.

---

## Installation

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/Parliament-Speech-Analyzer.git
cd Parliament-Speech-Analyzer

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r backend/requirements.txt

# Download SpaCy Italian language model
python -m spacy download it_core_news_sm
```

---

## Usage

### Run Full Pipeline
```bash
python backend/export_data.py
```

### Run with Options
```bash
# Fresh data fetch
python backend/export_data.py --refetch

# Rebuild from cached sittings when the open-data endpoints are down
python backend/export_data.py --offline

# Camera only, with CloudScraper
python backend/export_data.py --source camera --cloudscraper
```

### Google Colab
Open `colab_notebook.ipynb` for GPU-accelerated execution with all optimizations enabled.

---

## Configuration

Configuration is managed through `backend/config/settings.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MONTHS_BACK` | 15 | Months of historical data to fetch |
| `DATA_SOURCE` | `'both'` | Data source: `'camera'`, `'senate'`, or `'both'` |
| `LEGISLATURE` | 19 | Legislature number (XIX = 2022-present) |
| `MIN_WORDS` | 30 | Minimum word count for speech inclusion |
| `MIN_SPEECHES_DISPLAY` | 5 | Minimum speeches for a member to be shown |
| `N_CLUSTERS` | 12 | K-Means clusters (used only when `TOPIC_CLUSTERS` is `None`) |
| `TOPIC_MIN_SIMILARITY` | 0.20 | Below this, a speech is left unclassified rather than forced into a topic |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Sentence embedding model |
| `REDUCTION_METHOD` | `'pca'` | Dimensionality reduction: `'pca'` or `'tsne'` |
| `CACHE_MAX_AGE_DAYS` | 31 | Cached speeches older than this are re-fetched |

Analyzer features are toggled in `backend/analyzers/config.yaml`. Each analyzer
also declares the sample sizes at which its output is meaningful, so period
breakdowns skip metrics that a thin slice cannot support.

---

## Tech Stack

| Category | Technologies |
|----------|--------------|
| **Core** | Python 3.10+, Pandas, NumPy |
| **NLP** | Sentence-Transformers, SpaCy, Scikit-learn |
| **Deep Learning** | PyTorch, HuggingFace Transformers (optional) |
| **Web Scraping** | BeautifulSoup4, Requests, CloudScraper |
| **Frontend** | React, Vite (in development) |

---

## License

This project is provided for educational and research purposes.

---

*Developed for the analysis of Italian parliamentary discourse.*
