"""
General infrastructure and data settings.
"""

# =============================================================================
# DATA FETCHING
# =============================================================================

# How many months back to fetch speeches (applies to both Camera and Senato)
# How many months back to fetch speeches (applies to both Camera and Senato)
MONTHS_BACK = 15

# Data source: 'senate', 'camera', or 'both'
DATA_SOURCE = 'both'

# Legislature number (19 = XIX Legislature, 2022-present)
LEGISLATURE = 19

# Minimum word count for a speech to be included
MIN_WORDS = 30

# Minimum number of speeches for a deputy to be displayed in frontend.
# At 1, a single intervention produced a map position and a "dominant topic"
# indistinguishable from a member with hundreds of speeches. The frontend was
# already filtering at 5 client-side; the backend now agrees.
MIN_SPEECHES_DISPLAY = 5

# Characters of speech text carried in the payload for display purposes.
# The full text stays one click away behind the speech's own `url`.
DISPLAY_TEXT_CHARS = 600

# Maximum age (in days) for cached data before automatic refresh
CACHE_MAX_AGE_DAYS = 31


# =============================================================================
# ANALYSIS
# =============================================================================

# Number of semantic clusters for K-Means (used if TOPIC_CLUSTERS is None)
N_CLUSTERS = 12

# Topic assignment is a nearest-neighbour match against topic descriptions, so
# without a floor every speech is forced into a topic - including procedural
# remarks that are about nothing. Below this cosine similarity a speech is left
# unclassified instead of being attributed to the least-bad match.
TOPIC_MIN_SIMILARITY = 0.20
UNCLASSIFIED_CLUSTER = -1
UNCLASSIFIED_LABEL = "Non classificato"

# Embedding model (multilingual)
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Dimensionality reduction method: 'pca' or 'tsne'
REDUCTION_METHOD = "pca"

# Compute analytics for each time period (by_year, by_month)
# Set to False for faster export (global-only analytics)
COMPUTE_ANALYTICS_BY_PERIOD = True

# t-SNE perplexity (only used if REDUCTION_METHOD = 'tsne')
TSNE_PERPLEXITY = 30


# =============================================================================
# OUTPUT
# =============================================================================

# Output directory for generated files
OUTPUT_DIR = "output"

# Webapp data file
WEBAPP_DATA_FILE = "webapp/data.json"
