"""
General infrastructure and data settings.
"""

# =============================================================================
# DATA FETCHING
# =============================================================================

# Maximum number of speeches to fetch
FETCH_LIMIT = 20

# Number of sessions to scrape per source
SESSIONS_TO_FETCH = 5

# Data source: 'senate', 'camera', or 'both'
DATA_SOURCE = 'both'

# How many months back to look for camera.it sessions
MONTHS_BACK = 12

# Legislature number (19 = XIX Legislature, 2022-present)
LEGISLATURE = 19

# Minimum word count for a speech to be included
MIN_WORDS = 30

# Minimum number of speeches for a deputy to be displayed in frontend
MIN_SPEECHES_DISPLAY = 5

# Maximum age (in days) for cached data before automatic refresh
CACHE_MAX_AGE_DAYS = 7


# =============================================================================
# ANALYSIS
# =============================================================================

# Number of semantic clusters for K-Means (used if TOPIC_CLUSTERS is None)
N_CLUSTERS = 12

# Embedding model (multilingual)
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Dimensionality reduction method: 'pca' or 'tsne'
REDUCTION_METHOD = "pca"

# t-SNE perplexity (only used if REDUCTION_METHOD = 'tsne')
TSNE_PERPLEXITY = 30


# =============================================================================
# OUTPUT
# =============================================================================

# Output directory for generated files
OUTPUT_DIR = "output"

# Webapp data file
WEBAPP_DATA_FILE = "webapp/data.json"
