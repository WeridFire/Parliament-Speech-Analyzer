# Italian Parliament Speech Analyzer

A comprehensive NLP-powered analysis platform for Italian parliamentary discourse. This system automatically scrapes, processes, and analyzes speeches from both the **Camera dei Deputati** (Chamber of Deputies) and the **Senato della Repubblica** (Senate), providing insights into political communication patterns.

> [!NOTE]
> **Frontend Development**: The frontend web application is currently under active development.

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
├── backend/               # Python backend (data processing & analysis)
│   ├── analyzers/         # Modular analysis engine
│   ├── config/            # Configuration files
│   ├── core/              # Shared logic (caching, aggregation)
│   ├── scrapers/          # Web scrapers for Camera & Senato
│   ├── utils/             # Utility functions
│   ├── export_data.py     # Main pipeline entry point
│   └── pipeline.py        # NLP pipeline components
├── frontend/              # React web application (in development)
├── output/                # Generated analysis data
└── colab_notebook.ipynb   # Google Colab execution notebook
```

---

## Backend Features

### Data Collection

The backend includes robust web scrapers for both houses of the Italian Parliament:

| Source | Description |
|--------|-------------|
| **Camera dei Deputati** | Scrapes stenographic reports from camera.it |
| **Senato della Repubblica** | Scrapes stenographic reports from senato.it |

**Key Capabilities:**
- Configurable time range (default: 13 months back)
- Automatic speaker and party identification
- Role detection (minister, president, deputy, senator)
- CloudScraper integration for bypassing CloudFront protection
- Robust retry logic with exponential backoff

---

### Analysis Pipeline

The main data processing pipeline (`export_data.py`) orchestrates the following workflow:

1. **Data Fetching** — Retrieves parliamentary speeches from configured sources
2. **Text Cleaning** — Normalizes and preprocesses speech content
3. **Embedding Generation** — Generates semantic embeddings using multilingual transformer models
4. **Clustering** — Groups speeches into thematic clusters via K-Means
5. **Analysis** — Runs all registered analyzers on the processed data
6. **Export** — Outputs structured JSON for frontend consumption

**Command-Line Options:**
```bash
python backend/export_data.py [OPTIONS]

--refetch                 # Force re-download of all speeches
--reembed                 # Force regeneration of embeddings
--transformer-sentiment   # Use transformer-based sentiment analysis
--cloudscraper            # Enable CloudScraper for anti-bot protection
--source [camera|senate|both]  # Select data source
--clusters N              # Override number of topic clusters
```

---

### Analytics Modules

The system employs a modular, registry-based architecture for analytics. Each analyzer is independently configurable and cacheable.

#### 1. Identity Analyzer
Analyzes political identity and thematic DNA.

| Feature | Description |
|---------|-------------|
| **Thematic Fingerprint** | Radar chart showing topic distribution per party/speaker |
| **Generalism Index** | Entropy-based measure of topic specialization |
| **Distinctive Keywords** | TF-IDF extracted keywords unique to each party |

#### 2. Sentiment Analyzer
Qualitative analysis of political communication.

| Feature | Description |
|---------|-------------|
| **Topic Sentiment** | Aspect-based sentiment analysis per cluster |
| **Readability Scores** | Gulpease index for Italian text complexity |
| **Polarization Scores** | "Us vs Them" rhetoric detection |
| **Sentiment Rankings** | Party and speaker sentiment comparisons |
| **Transformer Sentiment** | Optional deep learning-based sentiment (HuggingFace) |

#### 3. Temporal Analyzer
Tracks discourse evolution over time.

| Feature | Description |
|---------|-------------|
| **Topic Trends** | Monthly distribution of thematic focus |
| **Semantic Drift** | Party position shifts in embedding space |
| **Crisis Index** | Frequency of alarm-related terminology |
| **Topic Surfing** | Detection of rapid topic focus changes |

#### 4. Relations Analyzer
Analyzes inter-party relationships.

| Feature | Description |
|---------|-------------|
| **Affinity Matrix** | Semantic similarity between parties |
| **Party Cohesion** | Internal coherence of party discourse |
| **Thematic Overlap** | Shared topic focus between parties |
| **Cross-Party Pairs** | Identification of closest speakers across parties |

#### 5. Rhetoric Analyzer
Detects speech style and rhetoric patterns.

| Feature | Description |
|---------|-------------|
| **Populist Markers** | Detection of populist rhetoric elements |
| **Anti-Establishment Markers** | Identification of anti-elite discourse |
| **Emotional Intensifiers** | Measurement of emotional language usage |
| **Rhetorical Style Classification** | Categorization of communication style |

#### 6. Topics Analyzer
Thematic clustering and topic labeling.

| Feature | Description |
|---------|-------------|
| **Cluster Extraction** | Semantic grouping of speeches |
| **Topic Labeling** | Automatic or predefined cluster naming |
| **Keyword Extraction** | POS-tagged keyword filtering (nouns, adjectives) |

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
# Fresh data fetch with transformer sentiment
python backend/export_data.py --refetch --transformer-sentiment

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
| `MONTHS_BACK` | 13 | Months of historical data to fetch |
| `DATA_SOURCE` | `'both'` | Data source: `'camera'`, `'senate'`, or `'both'` |
| `LEGISLATURE` | 19 | Legislature number (XIX = 2022-present) |
| `MIN_WORDS` | 30 | Minimum word count for speech inclusion |
| `MIN_SPEECHES_DISPLAY` | 1 | Minimum speeches for frontend display |
| `N_CLUSTERS` | 12 | Number of semantic clusters |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Sentence embedding model |
| `REDUCTION_METHOD` | `'pca'` | Dimensionality reduction: `'pca'` or `'tsne'` |

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
