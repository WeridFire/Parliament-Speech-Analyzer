"""
Analyzers Package - Political discourse analysis toolkit.

This package provides a modular, configurable system for analyzing political speeches.

Core Components:
- BaseAnalyzer: Abstract base class for all analyzers
- AnalyzerRegistry: Auto-discovery of analyzer classes
- CacheManager: Unified caching system
- AnalyticsOrchestrator: Run all enabled analyzers

Available Analyzers:
- identity: Thematic fingerprint, generalism index, distinctive keywords
- sentiment: Topic sentiment, readability, polarization
- temporal: Topic trends, semantic drift, crisis index
- relations: Party affinity, cohesion, thematic overlap
- speaker: Per-politician statistics (12 metrics)
- rhetoric: Populist, anti-establishment, emotional markers
- factions: Internal party divisions
- alliances: Cross-party themes
- topics: Cluster labeling

Usage:
    from backend.analyzers import AnalyticsOrchestrator, load_config
    
    orchestrator = AnalyticsOrchestrator(
        df=speeches_df,
        embeddings=embeddings,
        cluster_labels=labels,
        cluster_centroids=centroids,
        source='camera'
    )
    
    # Run all enabled analyzers
    results = orchestrator.run_all()
    
    # Or run specific analyzer
    identity = orchestrator.run('identity')
"""

# Core infrastructure
from .base import BaseAnalyzer
from .registry import AnalyzerRegistry, analyzer
from .cache import CacheManager
from .config_loader import load_config, DEFAULT_CONFIG
from .orchestrator import AnalyticsOrchestrator, run_analytics

# Import analyzer packages to trigger registration
from . import identity
from . import sentiment
from . import temporal
from . import relations
from . import speaker
from . import rhetoric
from . import factions
from . import alliances
from . import topics

# Re-export commonly used functions for backward compatibility
from .identity import (
    compute_thematic_fingerprint,
    compute_generalism_index,
    compute_distinctive_keywords,
)

from .sentiment import (
    compute_topic_sentiment,
    compute_gulpease_score,
    compute_readability_scores,
    compute_polarization_scores,
)

from .temporal import (
    compute_topic_trends,
    compute_semantic_drift,
    compute_crisis_index,
)

from .relations import (
    compute_party_affinity_matrix,
    compute_party_cohesion,
    compute_thematic_overlap,
)

from .topics import (
    extract_cluster_topics,
    get_cluster_labels,
)

from .rhetoric import (
    compute_rhetoric_scores,
)

from .factions import (
    compute_senator_conformity,
    get_all_factions,
)

from .alliances import (
    find_transversal_clusters,
    find_unusual_pairs,
)

from .speaker import (
    aggregate_speaker_metrics,
    compute_consistency_index,
    compute_topic_leadership,
    compute_intervention_patterns,
    compute_vocabulary_richness,
    compute_interaction_network,
)

__all__ = [
    # Core
    'BaseAnalyzer',
    'AnalyzerRegistry',
    'analyzer',
    'CacheManager',
    'load_config',
    'DEFAULT_CONFIG',
    'AnalyticsOrchestrator',
    'run_analytics',
    
    # Identity
    'compute_thematic_fingerprint',
    'compute_generalism_index',
    'compute_distinctive_keywords',
    
    # Sentiment
    'compute_topic_sentiment',
    'compute_gulpease_score',
    'compute_readability_scores',
    'compute_polarization_scores',
    
    # Temporal
    'compute_topic_trends',
    'compute_semantic_drift',
    'compute_crisis_index',
    
    # Relations
    'compute_party_affinity_matrix',
    'compute_party_cohesion',
    'compute_thematic_overlap',
    
    # Topics
    'extract_cluster_topics',
    'get_cluster_labels',
    
    # Rhetoric
    'compute_rhetoric_scores',
    
    # Factions
    'compute_senator_conformity',
    'get_all_factions',
    
    # Alliances
    'find_transversal_clusters',
    'find_unusual_pairs',
    
    # Speaker
    'aggregate_speaker_metrics',
    'compute_consistency_index',
    'compute_topic_leadership',
    'compute_intervention_patterns',
    'compute_vocabulary_richness',
    'compute_interaction_network',
]
