"""
Alliances Analyzer Package - Cross-party themes and unusual alliances.
"""
from .analyzer import AlliancesAnalyzer
from .transversal import (
    compute_cluster_party_composition,
    find_transversal_clusters,
    find_unusual_pairs,
    find_left_right_alliances
)

__all__ = [
    'AlliancesAnalyzer',
    'compute_cluster_party_composition',
    'find_transversal_clusters',
    'find_unusual_pairs',
    'find_left_right_alliances',
]
