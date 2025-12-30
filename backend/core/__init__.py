"""
Core functionality package.

Contains core components for caching, clustering logic, and data aggregation.
"""

from .cache import (
    load_cached_speeches,
    save_speeches_cache,
    load_cached_embeddings,
    save_embeddings_cache
)

from .clustering import (
    assign_topics_by_semantics,
    compute_rebel_scores
)

from .aggregation import (
    compute_deputies_data,
    compute_deputies_by_period,
    compute_source_output
)
