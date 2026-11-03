"""
Tests for Relations Analyzer.

Tests:
- Party Affinity Matrix
- Party Cohesion
- Cross-Party Pairs
"""

import numpy as np
import pandas as pd
import pytest

from backend.analyzers.relations import (
    RelationsAnalyzer,
    compute_party_affinity_matrix,
    compute_party_cohesion,
    find_closest_cross_party_pairs,
    mean_pairwise_similarity,
)
from backend.analyzers.relations import cohesion as cohesion_module
from backend.analyzers.relations import pairs as pairs_module


class TestRelationsAnalyzer:

    def test_analyzer_registration(self):
        from backend.analyzers import AnalyzerRegistry

        assert 'relations' in AnalyzerRegistry.names()

    def test_analyzer_compute(self, analyzer_kwargs):
        result = RelationsAnalyzer(**analyzer_kwargs).compute()

        assert {'affinity_matrix', 'party_cohesion', 'cross_party_pairs'} <= set(result)


@pytest.fixture
def two_camps():
    """Two parties per camp; each camp's speeches point roughly the same way."""
    rng = np.random.default_rng(0)
    rows, vectors = [], []
    for party, direction in (('A', 0), ('B', 0), ('C', 1), ('D', 1)):
        for i in range(40):
            base = np.zeros(8)
            base[direction] = 1.0
            vectors.append(base + rng.normal(scale=0.3, size=8))
            rows.append({'group': party, 'deputy': f'{party}{i % 4}'})
    return pd.DataFrame(rows), np.array(vectors)


class TestAffinityMatrix:

    def test_matrix_is_symmetric_with_unit_diagonal(self, two_camps):
        df, emb = two_camps
        result = compute_party_affinity_matrix(df, emb)
        matrix = np.array(result['matrix'])

        assert np.allclose(matrix, matrix.T)
        assert np.allclose(np.diag(matrix), 1.0)

    def test_same_camp_is_closer_than_opposite_camp(self, two_camps):
        df, emb = two_camps
        result = compute_party_affinity_matrix(df, emb)
        index = {p: i for i, p in enumerate(result['parties'])}
        matrix = result['matrix']

        assert matrix[index['A']][index['B']] > matrix[index['A']][index['C']]

    def test_range_describes_the_off_diagonal(self, two_camps):
        df, emb = two_camps
        result = compute_party_affinity_matrix(df, emb)

        low, high = result['range']
        assert low < high < 1.0


class TestPartyCohesion:

    def test_mean_pairwise_similarity_matches_brute_force(self):
        rng = np.random.default_rng(1)
        vectors = rng.normal(size=(12, 5))
        unit = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        brute = np.mean([unit[i] @ unit[j] for i in range(12) for j in range(12) if i != j])

        assert mean_pairwise_similarity(unit) == pytest.approx(brute)

    def test_tighter_group_is_more_cohesive(self, monkeypatch):
        monkeypatch.setattr(cohesion_module, 'MIN_PARTY_SPEECHES', 2)
        rng = np.random.default_rng(2)
        tight = np.tile([1.0, 0, 0], (30, 1)) + rng.normal(scale=0.05, size=(30, 3))
        loose = rng.normal(size=(30, 3))
        df = pd.DataFrame({'group': ['T'] * 30 + ['L'] * 30, 'deputy': ['x'] * 60})

        result = compute_party_cohesion(df, np.vstack([tight, loose]))

        assert result['T']['cohesion'] > result['L']['cohesion']


class TestCrossPartyPairs:

    def test_pairs_are_cross_party_and_sorted(self, two_camps, monkeypatch):
        monkeypatch.setattr(pairs_module, 'MIN_SPEAKER_SPEECHES', 5)
        df, emb = two_camps
        pairs = find_closest_cross_party_pairs(df, emb)

        assert pairs
        assert all(p['party1'] != p['party2'] for p in pairs)
        sims = [p['similarity'] for p in pairs]
        assert sims == sorted(sims, reverse=True)

    def test_thin_speakers_are_excluded(self, mock_df, mock_embeddings):
        # Mock speakers have 5 speeches each, below the minimum.
        assert find_closest_cross_party_pairs(mock_df, mock_embeddings) == []
