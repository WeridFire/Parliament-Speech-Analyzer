"""
Alignment invariants between speeches, embeddings and topic scores.

Every metric in this project is computed by masking a DataFrame and using the
result to slice a parallel numpy array. Those two structures are only correct
together, and when they drift apart nothing raises - the numbers just quietly
become wrong. These tests pin the invariant at the public seams (period
analytics, deputy aggregation, semantic drift) so a refactor of the plumbing
underneath cannot silently break it.

The technique: build *traceable* arrays where row i carries the value i in its
first column. Any subset can then be checked against its DataFrame's `row_id`
column - if the slicing is off by even one row, the comparison fails loudly.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from backend.analyzers.period_orchestrator import compute_analytics_by_period
from backend.analyzers.temporal.drift import compute_semantic_drift
from backend.core.aggregation import compute_deputies_by_period


N_ROWS = 60
EMBEDDING_DIM = 8
N_TOPICS = 3


# =============================================================================
# TRACEABLE FIXTURES
# =============================================================================

@pytest.fixture
def traceable_df() -> pd.DataFrame:
    """
    60 speeches over two years, each row tagged with its own position.

    Dates are interleaved on purpose: a naive `sort_values('date')` reorders the
    frame, which is exactly the situation that breaks label-vs-position slicing.
    """
    rows = []
    for i in range(N_ROWS):
        # Year and party are deliberately independent: every party must appear in
        # both years, or period-over-period metrics have nothing to compare.
        year = 2023 if i < N_ROWS // 2 else 2024
        month = (i % 6) + 1
        rows.append({
            'row_id': i,
            'deputy': f'Deputy_{i % 6}',
            'group': 'Party_A' if i % 2 == 0 else 'Party_B',
            'cluster': i % N_TOPICS,
            'cleaned_text': f'Contenuto del discorso numero {i} con parole sufficienti.',
            'date': f'{year}-{month:02d}-{(i % 27) + 1:02d}',
            'x': float(i),
            'y': float(-i),
            'source': 'camera',
        })
    return pd.DataFrame(rows)


@pytest.fixture
def traceable_embeddings() -> np.ndarray:
    """embeddings[i][0] == i, so any slice reveals which rows it came from."""
    emb = np.zeros((N_ROWS, EMBEDDING_DIM), dtype=np.float64)
    emb[:, 0] = np.arange(N_ROWS)
    emb[:, 1] = 1.0  # keep vectors non-degenerate for cosine/norm maths
    return emb


@pytest.fixture
def traceable_topic_scores() -> np.ndarray:
    """topic_scores[i][0] == i, same trick for the topic-affinity matrix."""
    scores = np.zeros((N_ROWS, N_TOPICS), dtype=np.float64)
    scores[:, 0] = np.arange(N_ROWS)
    return scores


@pytest.fixture
def cluster_labels() -> dict:
    return {0: 'Topic A', 1: 'Topic B', 2: 'Topic C'}


@pytest.fixture
def cluster_centroids() -> np.ndarray:
    centroids = np.zeros((N_TOPICS, EMBEDDING_DIM))
    centroids[:, 1] = 1.0
    return centroids


def capture_orchestrator_calls():
    """
    Patch AnalyticsOrchestrator and record the (df, embeddings) pairs it is
    handed, so we can assert alignment on every period subset.
    """
    captured = []

    class RecordingOrchestrator:
        # Mirrors the real orchestrator's reporting surface so the period
        # orchestrator can collect a run report from it.
        def __init__(self, df, embeddings=None, **kwargs):
            captured.append((df, embeddings))
            self.failures = {}
            self.skipped = {}

        def run_all(self):
            return {'stub': {}}

    return captured, RecordingOrchestrator


# =============================================================================
# PERIOD ANALYTICS
# =============================================================================

class TestPeriodAnalyticsAlignment:
    """compute_analytics_by_period must hand each analyzer matching rows."""

    def test_every_period_subset_is_aligned(
        self, traceable_df, traceable_embeddings, cluster_labels, cluster_centroids
    ):
        captured, recorder = capture_orchestrator_calls()

        with patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator', recorder):
            compute_analytics_by_period(
                df=traceable_df,
                embeddings=traceable_embeddings,
                cluster_labels=cluster_labels,
                cluster_centroids=cluster_centroids,
                compute_by_period=True,
            )

        assert captured, "orchestrator was never invoked"

        for df, embeddings in captured:
            expected = df['row_id'].to_numpy(dtype=float)
            actual = embeddings[:, 0]
            assert np.array_equal(actual, expected), (
                f"embedding rows {actual[:5]}... do not match speeches {expected[:5]}..."
            )

    def test_global_subset_covers_every_row(
        self, traceable_df, traceable_embeddings, cluster_labels, cluster_centroids
    ):
        captured, recorder = capture_orchestrator_calls()

        with patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator', recorder):
            compute_analytics_by_period(
                df=traceable_df,
                embeddings=traceable_embeddings,
                cluster_labels=cluster_labels,
                cluster_centroids=cluster_centroids,
                compute_by_period=False,
            )

        global_df, global_embeddings = captured[0]
        assert len(global_df) == N_ROWS
        assert np.array_equal(global_embeddings[:, 0], np.arange(N_ROWS, dtype=float))

    def test_reordered_index_stays_aligned(
        self, traceable_df, traceable_embeddings, cluster_labels, cluster_centroids
    ):
        """
        Sorting by date without resetting the index is an ordinary thing to do and
        must not corrupt the analytics.
        """
        reordered = traceable_df.sort_values('date')
        embeddings = traceable_embeddings[reordered.index.to_numpy()]

        captured, recorder = capture_orchestrator_calls()

        with patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator', recorder):
            compute_analytics_by_period(
                df=reordered,
                embeddings=embeddings,
                cluster_labels=cluster_labels,
                cluster_centroids=cluster_centroids,
                compute_by_period=True,
            )

        for df, subset_embeddings in captured:
            assert np.array_equal(subset_embeddings[:, 0], df['row_id'].to_numpy(dtype=float))


# =============================================================================
# DEPUTY AGGREGATION
# =============================================================================

class TestDeputyAggregationAlignment:
    """Deputy topic scores are averaged from sliced rows - same invariant."""

    def test_global_topic_scores_match_source_rows(
        self, traceable_df, traceable_topic_scores, cluster_labels
    ):
        result = compute_deputies_by_period(
            df=traceable_df,
            topic_scores=traceable_topic_scores,
            cluster_labels=cluster_labels,
            rebel_scores={},
        )

        expected_by_deputy = traceable_df.groupby('deputy')['row_id'].mean().round(3).to_dict()

        assert result['global'], "no deputies aggregated"
        for deputy in result['global']:
            assert deputy['topic_scores'][0] == pytest.approx(
                expected_by_deputy[deputy['deputy']], abs=1e-3
            ), f"{deputy['deputy']}: topic scores came from the wrong rows"

    def test_per_year_topic_scores_match_source_rows(
        self, traceable_df, traceable_topic_scores, cluster_labels
    ):
        result = compute_deputies_by_period(
            df=traceable_df,
            topic_scores=traceable_topic_scores,
            cluster_labels=cluster_labels,
            rebel_scores={},
        )

        df = traceable_df.copy()
        df['_year'] = df['date'].str.slice(0, 4)

        for year, deputies in result['by_year'].items():
            expected = df[df['_year'] == year].groupby('deputy')['row_id'].mean().to_dict()
            for deputy in deputies:
                assert deputy['topic_scores'][0] == pytest.approx(
                    expected[deputy['deputy']], abs=1e-3
                ), f"{year}/{deputy['deputy']}: topic scores came from the wrong rows"

    def test_period_buckets_partition_the_speeches(
        self, traceable_df, traceable_topic_scores, cluster_labels
    ):
        """Every speech lands in exactly one year bucket - no drops, no doubles."""
        result = compute_deputies_by_period(
            df=traceable_df,
            topic_scores=traceable_topic_scores,
            cluster_labels=cluster_labels,
            rebel_scores={},
        )

        total_by_year = sum(
            d['n_speeches'] for deputies in result['by_year'].values() for d in deputies
        )
        assert total_by_year == N_ROWS


# =============================================================================
# SEMANTIC DRIFT
# =============================================================================

class TestSemanticDriftAlignment:
    """drift.py resolves labels via get_loc - lock that in before refactoring."""

    def test_drift_uses_the_right_embedding_rows(
        self, traceable_df, traceable_embeddings
    ):
        result = compute_semantic_drift(
            df=traceable_df,
            embeddings=traceable_embeddings,
            party_col='group',
            date_col='date',
        )

        assert result, "expected drift for both parties"

        for party, data in result.items():
            party_rows = traceable_df[traceable_df['group'] == party]
            centroids = {}
            for year, group in party_rows.groupby(party_rows['date'].str.slice(0, 4)):
                if len(group) >= 5:
                    centroids[year] = traceable_embeddings[group['row_id'].to_numpy(), 0].mean()

            years = sorted(centroids)
            expected_total = sum(
                abs(centroids[b] - centroids[a]) for a, b in zip(years, years[1:])
            )
            assert data['total_drift'] == pytest.approx(expected_total, rel=1e-3)
