# 🏛️ Italian Parliament Speech Analyzer

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/WeridFire/Parliament-Speech-Analyzer/main/colab_notebook.ipynb)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Semantic analysis of Italian Parliament speeches to discover hidden coalitions, political patterns, and discourse dynamics.

## 🎯 Features

### Analytics Dashboard
- **Thematic Fingerprint** - Radar chart showing each politician's topic focus
- **Generalism Index** - Entropy-based score distinguishing specialists vs generalists
- **Distinctive Keywords** - WordCloud of party-specific vocabulary using TF-IDF + spaCy
- **Party Affinity Matrix** - Semantic similarity heatmap between parties
- **Crisis ECG** - Temporal tracking of alarm/crisis language
- **Topic Sentiment** - Sentiment analysis per topic (keyword-based or transformer)
- **Readability Score** - Gulpease index for Italian text complexity
- **Polarization Score** - "Us vs Them" language detection

### Visualization
- Interactive 2D semantic map of speeches
- Filter by party, deputy, topic cluster
- Time-based period selection (yearly/monthly)
- Rebel analysis (deputies deviating from party line)

---

## 🚀 Quick Start

### Option 1: Google Colab (Recommended for first run)

Click the Colab badge above or open `colab_notebook.ipynb` to run the entire pipeline on Google's free GPU.

### Option 2: Local Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/politics.git
cd politics

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Optional: Install spaCy Italian model for better keywords
python -m spacy download it_core_news_sm

# Optional: Install transformer sentiment (more accurate, slower)
pip install transformers torch
```

---

## 📊 Usage

### 1. Generate Data

```bash
# Standard run (uses cached data if available)
python backend/export_data.py --source both

# Force refresh from parliament websites
python backend/export_data.py --source both --refetch

# Use transformer-based sentiment (more accurate, slower)
python backend/export_data.py --source both --transformer-sentiment
```

### 2. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## ⚙️ CLI Options

| Flag | Description |
|------|-------------|
| `--source [senate\|camera\|both]` | Data source selection |
| `--refetch` | Force re-scraping from parliament websites |
| `--reembed` | Force regeneration of embeddings |
| `--clusters N` | Number of K-Means clusters (if not using semantic topics) |
| `--transformer-sentiment` | Use transformer model for sentiment (requires `transformers` + `torch`) |

---

## 🗂️ Project Structure

```
politics/
├── requirements.txt          # Python dependencies
├── colab_notebook.ipynb      # Google Colab notebook
├── backend/
│   ├── config.py             # Centralized configuration
│   ├── pipeline.py           # Reusable NLP functions
│   ├── export_data.py        # Main entry point
│   ├── scrapers/             # Parliament website scrapers
│   │   ├── senate.py         # senato.it
│   │   └── camera.py         # camera.it
│   ├── analyzers/            # Analytics modules
│   │   ├── identity.py       # Fingerprints, generalism, keywords
│   │   ├── relations.py      # Affinity, cohesion, overlap
│   │   ├── temporal.py       # Trends, drift, crisis index
│   │   ├── sentiment.py      # Keyword-based sentiment
│   │   ├── transformer_sentiment.py  # Transformer sentiment
│   │   └── analytics.py      # Unified interface
│   └── .cache/               # Cached data (gitignored)
├── frontend/                 # React + Vite web app
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Analytics/    # Dashboard tabs
│   │   │   └── UI/           # Reusable UI components
│   │   └── contexts/         # State management
│   └── public/               # Generated JSON data
└── output/                   # Generated reports
```

---

## ⚙️ Configuration

Edit `backend/config.py` to customize:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FETCH_LIMIT` | 10000 | Max speeches to scrape |
| `SESSIONS_TO_FETCH` | 300 | Number of sessions to analyze |
| `MIN_WORDS` | 30 | Minimum words per speech |
| `MONTHS_BACK` | 12 | Time window for analysis |
| `TOPIC_CLUSTERS` | {...} | Custom semantic topics |
| `CRISIS_KEYWORDS` | {...} | 85+ crisis/alarm terms |

---

## 🔬 Methodology

### Embeddings
Speeches are converted to 384-dimensional vectors using `paraphrase-multilingual-MiniLM-L12-v2` (Sentence Transformers).

### Clustering
Either automatic K-Means or semantic assignment to predefined topics based on cosine similarity.

### Sentiment Analysis
- **Keyword-based** (default): Fast, uses curated positive/negative word lists
- **Transformer-based** (optional): Uses `MilaNLProc/feel-it-italian-sentiment` for higher accuracy

### Key Metrics
- **Generalism Index**: Shannon entropy of topic distribution (0-100)
- **Party Affinity**: Cosine similarity between party embedding centroids
- **Crisis Index**: Frequency of crisis keywords over time

---

## 📈 Performance

| Operation | Time (CPU) | Time (GPU) |
|-----------|-----------|------------|
| Scraping (both sources) | ~10-15 min | N/A |
| Embedding generation | ~5 min | ~1 min |
| Standard analytics | ~30 sec | ~30 sec |
| Transformer sentiment | ~25 min | ~2 min |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit (`git commit -m 'Add new feature'`)
4. Push (`git push origin feature/new-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- [Sentence Transformers](https://www.sbert.net/) for multilingual embeddings
- [spaCy](https://spacy.io/) for Italian NLP
- [feel-it](https://github.com/MilaNLProc/feel-it) for Italian sentiment model
- Italian Parliament ([senato.it](https://senato.it), [camera.it](https://camera.it)) for open data
