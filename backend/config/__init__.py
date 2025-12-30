"""
Configuration package.

Centralizes all settings, data, and configuration parameters.
Backward compatible with original config.py.
"""

# Import all settings
from .settings import *

# Import data sets
from .stopwords import STOP_WORDS
from .topic_clusters import TOPIC_CLUSTERS
from .party_normalization import (
    PARTY_NORMALIZATION,
    RIGHT_PARTIES,
    LEFT_PARTIES,
    CENTER_PARTIES,
    CLASSIFY_GOVERNO_AS_RIGHT
)
from .analysis_keywords import (
    POPULIST_KEYWORDS,
    ANTI_ESTABLISHMENT_KEYWORDS,
    INSTITUTIONAL_KEYWORDS,
    EMOTIONAL_KEYWORDS,
    SOVEREIGNIST_KEYWORDS,
    PROGRESSIVE_KEYWORDS,
    CRISIS_KEYWORDS,
    POSITIVE_SENTIMENT_KEYWORDS,
    NEGATIVE_SENTIMENT_KEYWORDS,
    POLARIZATION_PRONOUNS,
    ADVERSATIVE_TERMS,
    US_THEM_PATTERNS
)

# NOTE: roles.py is not imported here by default in the old config.py, 
# but we can make it available if needed. 
# For now, code imports config_roles separately, so users should assume separate modules or import explicitly.
# But since we're refactoring, let's keep it separate to avoid namespace pollution if not needed.
