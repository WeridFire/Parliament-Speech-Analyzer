"""
Analyzers Package - Political discourse analysis toolkit.

This package provides a modular, configurable system for analyzing political speeches.

Core Components:
- BaseAnalyzer: Abstract base class for all analyzers
- AnalyzerRegistry: Auto-discovery of analyzer classes
- AnalyticsOrchestrator: Run all enabled analyzers

Available Analyzers:
- identity: topic profile, generalism index, distinctive keywords
- topics: who carries each topic (spokespeople, group lift, vocabulary)
- blocs: majority vs opposition (issue ownership, vocabulary)
- relations: party affinity, cohesion, cross-party pairs
- reactions: applause and protests between groups
- mentions: which groups name which public figures
- temporal: monthly topic shares and bloc activity
- speaker: per-politician statistics
- language: readability and polarization

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
from .config_loader import load_config, DEFAULT_CONFIG
from .orchestrator import AnalyticsOrchestrator, run_analytics

# Import analyzer packages to trigger registration
from . import identity
from . import topics
from . import blocs
from . import relations
from . import reactions
from . import mentions
from . import temporal
from . import speaker
from . import language

from .identity import (
    compute_topic_profile,
    compute_generalism_index,
    compute_distinctive_keywords,
)
from .topics import compute_topic_owners, cluster_keywords
from .blocs import compute_issue_ownership, compute_bloc_keywords, compute_bloc_summary
from .relations import (
    compute_party_affinity_matrix,
    compute_party_cohesion,
    find_closest_cross_party_pairs,
)
from .reactions import compute_reactions
from .mentions import compute_mentions
from .temporal import compute_topic_trends
from .speaker import compute_speaker_profiles, compute_vocabulary_richness
from .language import compute_readability_scores, compute_polarization_scores

__all__ = [
    # Core
    'BaseAnalyzer',
    'AnalyzerRegistry',
    'analyzer',
    'load_config',
    'DEFAULT_CONFIG',
    'AnalyticsOrchestrator',
    'run_analytics',

    'compute_topic_profile',
    'compute_generalism_index',
    'compute_distinctive_keywords',
    'compute_topic_owners',
    'cluster_keywords',
    'compute_issue_ownership',
    'compute_bloc_keywords',
    'compute_bloc_summary',
    'compute_party_affinity_matrix',
    'compute_party_cohesion',
    'find_closest_cross_party_pairs',
    'compute_reactions',
    'compute_mentions',
    'compute_topic_trends',
    'compute_speaker_profiles',
    'compute_vocabulary_richness',
    'compute_readability_scores',
    'compute_polarization_scores',
]
