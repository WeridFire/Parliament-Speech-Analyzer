"""
Alignment invariants between speeches, embeddings and topic scores.

Every metric in this project is computed by masking a DataFrame and using the
result to slice a parallel numpy array. Those two structures are only correct
together, and when they drift apart nothing raises - the numbers just quietly
become wrong. These tests pin the invariant at the public seams (period
analytics, deputy aggregation, the term matrix) so a refactor of the plumbing
underneath cannot silently break it.

The technique: build *traceable* arrays where row i carries the value i in its
first column. Any subset can then be checked against its DataFrame's `row_id`
column - if the slicing is off by even one row, the comparison fails loudly.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from scipy.sparse import csr_matrix

from backend.analyzers.period_orchestrator import compute_analytics_by_period
from backend.core.aggregation import compute_deputies_by_period
from backend.core.dataset import SpeechDataset


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
    """Deputy map positions are averaged from sliced rows - same invariant."""

    def test_global_positions_match_source_rows(self, traceable_df, cluster_labels):
        result = compute_deputies_by_period(df=traceable_df, cluster_labels=cluster_labels)

        expected_by_deputy = traceable_df.groupby('deputy')['row_id'].mean().to_dict()

        assert result['global'], "no deputies aggregated"
        for deputy in result['global']:
            assert deputy['x'] == pytest.approx(expected_by_deputy[deputy['deputy']], abs=1e-6), (
                f"{deputy['deputy']}: position came from the wrong rows"
            )

    def test_per_year_positions_match_source_rows(self, traceable_df, cluster_labels):
        result = compute_deputies_by_period(df=traceable_df, cluster_labels=cluster_labels)

        df = traceable_df.copy()
        df['_year'] = df['date'].str.slice(0, 4)

        for year, deputies in result['by_year'].items():
            expected = df[df['_year'] == year].groupby('deputy')['row_id'].mean().to_dict()
            for deputy in deputies:
                assert deputy['x'] == pytest.approx(expected[deputy['deputy']], abs=1e-6), (
                    f"{year}/{deputy['deputy']}: position came from the wrong rows"
                )

    def test_period_buckets_partition_the_speeches(self, traceable_df, cluster_labels):
        """Every speech lands in exactly one year bucket - no drops, no doubles."""
        result = compute_deputies_by_period(df=traceable_df, cluster_labels=cluster_labels)

        total_by_year = sum(
            d['n_speeches'] for deputies in result['by_year'].values() for d in deputies
        )
        assert total_by_year == N_ROWS


# =============================================================================
# TERM MATRIX
# =============================================================================

class TestTermMatrixAlignment:
    """The sparse term matrix is narrowed with the frame, like the embeddings."""

    def test_subset_keeps_term_rows_aligned(self, traceable_df):
        terms = csr_matrix(np.arange(N_ROWS, dtype=float).reshape(-1, 1))
        dataset = SpeechDataset(df=traceable_df, terms=terms)

        shuffled = dataset.take(np.random.default_rng(0).permutation(N_ROWS))
        party_b = shuffled.subset(shuffled.df['group'] == 'Party_B')

        assert np.array_equal(
            party_b.terms.toarray().ravel(), party_b.df['row_id'].to_numpy(dtype=float)
        )

    def test_mismatched_term_matrix_is_rejected(self, traceable_df):
        with pytest.raises(ValueError):
            SpeechDataset(df=traceable_df, terms=csr_matrix((N_ROWS - 1, 3)))
