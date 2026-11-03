"""
Tests for Identity Analyzer.

Tests:
- Topic Profile
- Generalism Index
- Distinctive Keywords (log-odds)
"""

import numpy as np
import pandas as pd
import pytest

from backend.analyzers.common import distinctive_terms, log_odds_z
from backend.analyzers.identity import (
    IdentityAnalyzer,
    compute_distinctive_keywords,
    compute_generalism_index,
    compute_topic_profile,
)
from backend.analyzers.identity import generalism as generalism_module
from backend.analyzers.identity import profile as profile_module
from backend.core.features import build_term_matrix


def labels(n):
    return {i: f'Tema {i}' for i in range(n)}


class TestIdentityAnalyzer:

    def test_analyzer_registration(self):
        from backend.analyzers import AnalyzerRegistry

        assert 'identity' in AnalyzerRegistry.names()

    def test_analyzer_compute(self, analyzer_kwargs):
        result = IdentityAnalyzer(**analyzer_kwargs).compute()

        assert {'topic_profile', 'generalism_index', 'distinctive_keywords'} <= set(result)

    def test_keywords_are_skipped_without_a_term_matrix(self, analyzer_kwargs):
        kwargs = {**analyzer_kwargs, 'terms': None}
        result = IdentityAnalyzer(**kwargs).compute()

        assert 'distinctive_keywords' not in result


class TestTopicProfile:

    @pytest.fixture
    def frame(self):
        # Party A: 30 speeches all on topic 0; Party B: 30 split evenly.
        rows = [{'group': 'A', 'cluster': 0} for _ in range(30)]
        rows += [{'group': 'B', 'cluster': i % 3} for i in range(30)]
        rows += [{'group': 'B', 'cluster': -1}]  # unclassified never counts
        return pd.DataFrame(rows)

    def test_shares_sum_to_100(self, frame, monkeypatch):
        monkeypatch.setattr(profile_module, 'MIN_PARTY_SPEECHES', 1)
        result = compute_topic_profile(frame, labels(3))

        for party in result['by_party'].values():
            assert sum(party['shares'].values()) == pytest.approx(100, abs=0.1)

    def test_lift_is_share_over_chamber_share(self, frame):
        result = compute_topic_profile(frame, labels(3))

        # Chamber: topic 0 = 40 / 60 speeches. Party A: 100% topic 0.
        assert result['chamber'][0] == pytest.approx(66.67, abs=0.01)
        assert result['by_party']['A']['lift'][0] == pytest.approx(1.5, abs=0.01)
        assert result['by_party']['A']['lift'][1] == 0

    def test_small_parties_are_left_out(self, frame):
        frame = pd.concat([frame, pd.DataFrame([{'group': 'C', 'cluster': 0}] * 3)])
        result = compute_topic_profile(frame, labels(3))

        assert 'C' not in result['by_party']


class TestGeneralismIndex:

    def test_single_topic_scores_zero_and_even_spread_scores_100(self, monkeypatch):
        monkeypatch.setattr(generalism_module, 'MIN_SPEAKER_SPEECHES', 1)
        rows = [{'deputy': 'mono', 'group': 'A', 'cluster': 0} for _ in range(8)]
        rows += [{'deputy': 'wide', 'group': 'A', 'cluster': i % 4} for i in range(8)]
        result = compute_generalism_index(pd.DataFrame(rows), labels(4))

        assert result['by_deputy']['mono']['score'] == 0
        assert result['by_deputy']['wide']['score'] == pytest.approx(100)

    def test_denominator_is_the_configured_topics(self, monkeypatch):
        """Two topics out of four configured is not "perfectly generalist"."""
        monkeypatch.setattr(generalism_module, 'MIN_SPEAKER_SPEECHES', 1)
        rows = [{'deputy': 'half', 'group': 'A', 'cluster': i % 2} for i in range(8)]
        result = compute_generalism_index(pd.DataFrame(rows), labels(4))

        assert result['by_deputy']['half']['score'] == pytest.approx(50)

    def test_thin_samples_are_not_scored(self, mock_df, mock_cluster_labels):
        # Mock speakers have 5 speeches each, below the minimum.
        result = compute_generalism_index(mock_df, mock_cluster_labels)

        assert result['by_deputy'] == {}


class TestDistinctiveKeywords:

    @pytest.fixture
    def corpus(self):
        docs = ['pensioni lavoro'] * 40 + ['migranti confini'] * 40 + ['lavoro confini'] * 20
        df = pd.DataFrame({'group': ['A'] * 40 + ['B'] * 40 + ['A'] * 10 + ['B'] * 10})
        terms, vocabulary = build_term_matrix(docs, min_df=1)
        return df, terms, vocabulary

    def test_each_party_gets_its_own_words(self, corpus):
        df, terms, vocabulary = corpus
        result = compute_distinctive_keywords(df, terms, vocabulary)

        assert result['A'][0]['term'] == 'pensioni'
        assert result['B'][0]['term'] == 'migranti'

    def test_shared_words_are_not_distinctive(self, corpus):
        df, terms, vocabulary = corpus
        result = compute_distinctive_keywords(df, terms, vocabulary)

        top_a = {w['term'] for w in result['A'][:1]}
        assert 'lavoro' not in top_a or 'confini' not in top_a

    def test_one_speech_cannot_make_a_word_distinctive(self):
        docs = ['carla carla carla carla carla carla'] + ['lavoro'] * 59
        terms, vocabulary = build_term_matrix(docs, min_df=1)
        mask = np.zeros(60, dtype=bool)
        mask[:30] = True

        words = {w['term'] for w in distinctive_terms(terms, vocabulary, mask)}

        assert 'carla' not in words

    def test_log_odds_sign(self):
        z = log_odds_z(np.array([10, 1]), np.array([1, 10]), prior=np.array([11, 11]))

        assert z[0] > 0 > z[1]

    def test_unused_terms_score_zero_without_warnings(self):
        with np.errstate(all='raise'):
            z = log_odds_z(np.array([5, 0]), np.array([5, 0]), prior=np.array([10, 0]))

        assert z[1] == 0
