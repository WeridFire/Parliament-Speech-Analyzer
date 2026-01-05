"""
General infrastructure and data settings.
"""

# =============================================================================
# DATA FETCHING
# =============================================================================

# How many months back to fetch speeches (applies to both Camera and Senato)
MONTHS_BACK = 13

# Data source: 'senate', 'camera', or 'both'
DATA_SOURCE = 'both'

# Legislature number (19 = XIX Legislature, 2022-present)
LEGISLATURE = 19

# Minimum word count for a speech to be included
MIN_WORDS = 30

# Minimum number of speeches for a deputy to be displayed in frontend
MIN_SPEECHES_DISPLAY = 1

# Maximum age (in days) for cached data before automatic refresh
CACHE_MAX_AGE_DAYS = 31


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
