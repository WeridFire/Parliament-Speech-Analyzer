# Analyzers subpackage - semantic and political analysis

# Original modules
from .topics import get_cluster_labels, extract_cluster_topics
from .factions import compute_senator_conformity, find_party_factions, get_all_factions
from .alliances import find_transversal_clusters, find_unusual_pairs, find_left_right_alliances
from .rhetoric import add_rhetoric_scores, classify_rhetorical_style

# New analytics modules
from .identity import (
    compute_thematic_fingerprint,
    compute_generalism_index,
    compute_distinctive_keywords
)
from .relations import (
    compute_party_affinity_matrix,
    compute_party_cohesion,
    compute_thematic_overlap,
    find_closest_cross_party_pairs,
    compute_party_centroids
)
from .temporal import (
    compute_topic_trends,
    compute_semantic_drift,
    compute_crisis_index,
    find_topic_surfing
)
from .sentiment import (
    compute_topic_sentiment,
    compute_readability_scores,
    compute_polarization_scores,
    compute_gulpease_score
)
from .analytics import PoliticalAnalytics
