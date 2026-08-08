"""
Tests for SpeechDataset - the type that keeps speeches and their arrays aligned.

Two properties matter most:
  * narrowing is positional, so a frame whose index does not match row order
    cannot produce a misaligned slice;
  * the fingerprint reacts to content, not just row count, because that is what
    makes the embeddings cache safe to reuse.
"""

import numpy as np
import pandas as pd
import pytest

from backend.core.dataset import SpeechDataset


N_ROWS = 12
DIM = 4


@pytest.fixture
def frame() -> pd.DataFrame:
    return pd.DataFrame({
        'row_id': range(N_ROWS),
        'deputy': [f'D{i % 3}' for i in range(N_ROWS)],
        'group': ['A' if i % 2 else 'B' for i in range(N_ROWS)],
        'cleaned_text': [f'testo numero {i}' for i in range(N_ROWS)],
        'date': [f'2024-{(i % 4) + 1:02d}-1{i % 5}' for i in range(N_ROWS)],
    })


@pytest.fixture
def embeddings() -> np.ndarray:
    emb = np.zeros((N_ROWS, DIM))
    emb[:, 0] = np.arange(N_ROWS)
    return emb


@pytest.fixture
def dataset(frame, embeddings) -> SpeechDataset:
    scores = np.zeros((N_ROWS, 2))
    scores[:, 0] = np.arange(N_ROWS)
    return SpeechDataset(df=frame, embeddings=embeddings, topic_scores=scores)


# =============================================================================
# CONSTRUCTION
# =============================================================================

class TestConstruction:

    def test_rejects_mismatched_embeddings(self, frame):
        with pytest.raises(ValueError, match='parallel'):
            SpeechDataset(df=frame, embeddings=np.zeros((N_ROWS - 1, DIM)))

    def test_rejects_mismatched_topic_scores(self, frame):
        with pytest.raises(ValueError, match='parallel'):
            SpeechDataset(df=frame, topic_scores=np.zeros((N_ROWS + 3, 2)))

    def test_normalises_a_dirty_index(self, frame, embeddings):
        dirty = frame.sort_values('date')  # index no longer matches row order
        assert not isinstance(dirty.index, pd.RangeIndex) or dirty.index[0] != 0

        ds = SpeechDataset(df=dirty, embeddings=embeddings)

        assert list(ds.df.index) == list(range(N_ROWS))
        # Row order is preserved; only the labels are rebuilt.
        assert ds.df['row_id'].tolist() == dirty['row_id'].tolist()

    def test_accepts_arrays_added_later(self, frame, embeddings):
        ds = SpeechDataset(df=frame).with_arrays(embeddings=embeddings)
        assert ds.embeddings is not None
        assert len(ds) == N_ROWS


# =============================================================================
# NARROWING
# =============================================================================

class TestSubset:

    def test_boolean_series_slices_all_arrays_together(self, dataset):
        subset = dataset.subset(dataset.df['group'] == 'A')

        assert np.array_equal(subset.embeddings[:, 0], subset.df['row_id'].to_numpy())
        assert np.array_equal(subset.topic_scores[:, 0], subset.df['row_id'].to_numpy())

    def test_numpy_mask_is_equivalent(self, dataset):
        mask = (dataset.df['group'] == 'A').to_numpy()
        assert dataset.subset(mask).df.equals(dataset.subset(dataset.df['group'] == 'A').df)

    def test_positions_are_accepted(self, dataset):
        subset = dataset.take([3, 7, 1])
        assert subset.df['row_id'].tolist() == [3, 7, 1]
        assert subset.embeddings[:, 0].tolist() == [3.0, 7.0, 1.0]

    def test_wrong_length_mask_is_rejected(self, dataset):
        with pytest.raises(ValueError, match='boolean mask'):
            dataset.subset(np.array([True, False]))

    def test_subset_result_is_itself_clean(self, dataset):
        subset = dataset.subset(dataset.df['group'] == 'A')
        assert list(subset.df.index) == list(range(len(subset)))

    def test_subset_of_subset_stays_aligned(self, dataset):
        first = dataset.subset(dataset.df['row_id'] >= 4)
        second = first.subset(first.df['deputy'] == 'D0')

        assert np.array_equal(second.embeddings[:, 0], second.df['row_id'].to_numpy())

    def test_missing_arrays_stay_missing(self, frame):
        ds = SpeechDataset(df=frame)
        subset = ds.subset(ds.df['group'] == 'A')
        assert subset.embeddings is None
        assert subset.topic_scores is None


# =============================================================================
# PERIODS
# =============================================================================

class TestPeriods:

    def test_month_buckets_partition_the_rows(self, dataset):
        buckets = dict(dataset.by_period('month'))
        assert sum(len(b) for b in buckets.values()) == N_ROWS

    def test_buckets_stay_aligned(self, dataset):
        for _, bucket in dataset.by_period('month'):
            assert np.array_equal(bucket.embeddings[:, 0], bucket.df['row_id'].to_numpy())

    def test_min_speeches_filters_small_buckets(self, dataset):
        big = dict(dataset.by_period('month', min_speeches=99))
        assert big == {}

    def test_newest_first_controls_order(self, dataset):
        ascending = [k for k, _ in dataset.by_period('month')]
        descending = [k for k, _ in dataset.by_period('month', newest_first=True)]
        assert ascending == sorted(ascending)
        assert descending == sorted(ascending, reverse=True)

    def test_unparseable_dates_are_dropped_from_buckets(self, frame, embeddings):
        frame = frame.copy()
        frame.loc[0, 'date'] = 'not a date'
        ds = SpeechDataset(df=frame, embeddings=embeddings)

        bucketed = sum(len(b) for _, b in ds.by_period('month'))
        assert bucketed == N_ROWS - 1

    def test_available_periods_ordering(self, dataset):
        periods = dataset.available_periods()
        assert periods['years'] == sorted(periods['years'])
        assert periods['months'] == sorted(periods['months'], reverse=True)


# =============================================================================
# FINGERPRINT
# =============================================================================

class TestFingerprint:

    def test_same_content_same_fingerprint(self, frame):
        assert SpeechDataset(df=frame).fingerprint() == SpeechDataset(df=frame.copy()).fingerprint()

    def test_changed_text_changes_fingerprint_at_equal_row_count(self, frame):
        """
        The defect this guards: the old cache compared row counts only, so an
        edited corpus of the same size silently reused stale embeddings.
        """
        edited = frame.copy()
        edited.loc[0, 'cleaned_text'] = 'testo completamente diverso'

        assert len(edited) == len(frame)
        assert SpeechDataset(df=edited).fingerprint() != SpeechDataset(df=frame).fingerprint()

    def test_extra_parameters_participate(self, frame):
        ds = SpeechDataset(df=frame)
        assert ds.fingerprint(model='a') != ds.fingerprint(model='b')

    def test_row_order_participates(self, frame):
        reversed_frame = frame.iloc[::-1]
        assert SpeechDataset(df=reversed_frame).fingerprint() != SpeechDataset(df=frame).fingerprint()
