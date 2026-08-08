"""
Tests for the content-addressed artifact cache.

The behaviour that matters: embeddings can only be reused for the exact corpus
they were computed from. The previous implementation compared row counts, so a
re-scrape returning the same number of different speeches reused the wrong
vectors and silently corrupted every downstream metric.
"""

import numpy as np
import pandas as pd
import pytest

from backend.core.cache import (
    ArtifactCache,
    CacheKey,
    load_cached_embeddings,
    load_cached_speeches,
    save_embeddings_cache,
    save_speeches_cache,
)


@pytest.fixture
def cache(tmp_path, monkeypatch) -> ArtifactCache:
    """A cache rooted in a temp dir, with metadata redirected there too."""
    monkeypatch.setattr('backend.utils.cache.CACHE_DIR', tmp_path)
    return ArtifactCache(root=tmp_path)


@pytest.fixture
def frame() -> pd.DataFrame:
    return pd.DataFrame({
        'deputy': ['A', 'B', 'C'],
        'cleaned_text': ['uno', 'due', 'tre'],
        'date': ['2024-01-01', '2024-01-02', '2024-02-01'],
    })


# =============================================================================
# KEYS
# =============================================================================

class TestCacheKey:

    def test_stem_includes_truncated_digest(self):
        key = CacheKey(kind='embeddings', source='camera', digest='0123456789abcdef' * 4)
        assert key.stem == 'embeddings_camera_0123456789ab'  # DIGEST_LENGTH = 12

    def test_stem_without_digest(self):
        assert CacheKey(kind='speeches', source='senate').stem == 'speeches_senate'

    def test_different_digests_are_different_entries(self, cache):
        a = CacheKey('embeddings', 'camera', 'aaaaaaaaaaaa')
        b = CacheKey('embeddings', 'camera', 'bbbbbbbbbbbb')
        assert cache.path(a, '.npy') != cache.path(b, '.npy')


# =============================================================================
# ROUND TRIPS
# =============================================================================

class TestRoundTrip:

    def test_json_round_trip(self, cache):
        key = CacheKey('analytics', 'camera', 'deadbeef')
        cache.save_json(key, {'a': 1, 'b': [1, 2, 3]})
        assert cache.load_json(key) == {'a': 1, 'b': [1, 2, 3]}

    def test_json_handles_numpy(self, cache):
        key = CacheKey('analytics', 'camera', 'numpy')
        cache.save_json(key, {'score': np.float64(1.5), 'ids': np.array([1, 2])})
        assert cache.load_json(key) == {'score': 1.5, 'ids': [1, 2]}

    def test_array_round_trip(self, cache):
        key = CacheKey('embeddings', 'camera', 'abc')
        array = np.arange(12, dtype=float).reshape(4, 3)
        cache.save_array(key, array)
        assert np.array_equal(cache.load_array(key), array)

    def test_dataframe_round_trip(self, cache, frame):
        key = CacheKey('speeches', 'camera')
        cache.save_dataframe(key, frame)
        assert cache.load_dataframe(key).equals(frame)

    def test_missing_entry_returns_none(self, cache):
        assert cache.load_json(CacheKey('analytics', 'camera', 'nope')) is None
        assert cache.load_array(CacheKey('embeddings', 'camera', 'nope')) is None

    def test_corrupt_entry_returns_none(self, cache):
        key = CacheKey('analytics', 'camera', 'bad')
        cache.save_json(key, {'ok': True})
        cache.path(key, '.json').write_text('{not json', encoding='utf-8')
        assert cache.load_json(key) is None


# =============================================================================
# FINGERPRINT SAFETY
# =============================================================================

class TestEmbeddingsFingerprint:

    def test_matching_fingerprint_hits(self, cache):
        embeddings = np.ones((5, 3))
        save_embeddings_cache(embeddings, 'camera', 'fingerprint-one', cache=cache)

        loaded = load_cached_embeddings('camera', 'fingerprint-one', cache=cache)
        assert np.array_equal(loaded, embeddings)

    def test_different_fingerprint_misses(self, cache):
        """
        Same source, same row count, different content - must not be reused.
        This is the corruption the old length-only check allowed.
        """
        save_embeddings_cache(np.ones((5, 3)), 'camera', 'corpus-before', cache=cache)

        assert load_cached_embeddings('camera', 'corpus-after', cache=cache) is None

    def test_sources_do_not_share_entries(self, cache):
        save_embeddings_cache(np.ones((5, 3)), 'camera', 'same-fingerprint', cache=cache)
        assert load_cached_embeddings('senate', 'same-fingerprint', cache=cache) is None


# =============================================================================
# AGE
# =============================================================================

class TestStaleness:

    def test_fresh_speeches_are_returned(self, cache, frame):
        save_speeches_cache(frame, 'camera', cache=cache)
        loaded = load_cached_speeches('camera', max_age_days=30, cache=cache)
        assert loaded is not None
        assert len(loaded) == len(frame)

    def test_stale_speeches_are_ignored(self, cache, frame, monkeypatch):
        """A cache older than the budget must not be reused silently."""
        import json
        from datetime import datetime, timedelta

        save_speeches_cache(frame, 'camera', cache=cache)

        meta_file = cache.root / 'cache_meta_speeches_camera.json'
        meta = json.loads(meta_file.read_text(encoding='utf-8'))
        meta['created_at'] = (datetime.now() - timedelta(days=90)).isoformat()
        meta_file.write_text(json.dumps(meta), encoding='utf-8')

        assert load_cached_speeches('camera', max_age_days=31, cache=cache) is None

    def test_no_age_limit_always_returns(self, cache, frame):
        save_speeches_cache(frame, 'camera', cache=cache)
        assert load_cached_speeches('camera', max_age_days=None, cache=cache) is not None


# =============================================================================
# PRUNING
# =============================================================================

class TestPruning:

    def test_old_digests_are_pruned(self, cache):
        for i in range(5):
            save_embeddings_cache(np.ones((2, 2)), 'camera', f'fingerprint-{i}', cache=cache)

        remaining = list(cache.root.glob('embeddings_camera_*.npy'))
        assert len(remaining) <= 2, "content-addressed entries must not accumulate"

    def test_pruning_keeps_the_newest(self, cache):
        for i in range(4):
            save_embeddings_cache(np.full((2, 2), i), 'camera', f'fp-{i}', cache=cache)

        assert load_cached_embeddings('camera', 'fp-3', cache=cache) is not None

    def test_other_sources_survive_pruning(self, cache):
        save_embeddings_cache(np.ones((2, 2)), 'senate', 'keep-me', cache=cache)
        for i in range(4):
            save_embeddings_cache(np.ones((2, 2)), 'camera', f'fp-{i}', cache=cache)

        assert load_cached_embeddings('senate', 'keep-me', cache=cache) is not None
