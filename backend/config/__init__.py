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
    ALTRO,
    CANONICAL_PARTIES,
    MAGGIORANZA,
    NOTE_GROUP_RES,
    OPPOSIZIONE,
    PARTY_BLOC,
    normalize_party,
    party_bloc,
)
from .analysis_keywords import (
    POLARIZATION_PRONOUNS,
    ADVERSATIVE_TERMS,
    US_THEM_PATTERNS,
    SELF_REFERENCE_WORDS,
    NEGATION_WORDS,
    NUMERIC_PATTERNS,
)
from .figures import FIGURES, FIGURE_GROUP_LABELS

# NOTE: roles.py is not imported here by default in the old config.py,
# but we can make it available if needed.
# For now, code imports config_roles separately, so users should assume separate modules or import explicitly.
# But since we're refactoring, let's keep it separate to avoid namespace pollution if not needed.
