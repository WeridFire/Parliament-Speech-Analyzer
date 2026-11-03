"""
Tests for Topics Analyzer (who carries each topic).
"""

import pandas as pd
import pytest

from backend.analyzers.topics import TopicsAnalyzer, cluster_keywords, compute_topic_owners
from backend.core.features import build_term_matrix


class TestTopicsAnalyzer:

    def test_analyzer_registration(self):
        from backend.analyzers import AnalyzerRegistry

        assert 'topics' in AnalyzerRegistry.names()

    def test_analyzer_compute(self, analyzer_kwargs, mock_cluster_labels):
        result = TopicsAnalyzer(**analyzer_kwargs).compute()

        assert set(result['by_topic']) <= set(mock_cluster_labels)


class TestTopicOwners:

    @pytest.fixture
    def frame(self):
        rows = (
            [{'deputy': 'Rossi', 'group': 'A', 'cluster': 0}] * 8
            + [{'deputy': 'Rossi', 'group': 'A', 'cluster': 1}] * 2
            + [{'deputy': 'Bianchi', 'group': 'B', 'cluster': 0}] * 4
            + [{'deputy': 'Bianchi', 'group': 'B', 'cluster': 1}] * 16
            + [{'deputy': 'Verdi', 'group': 'B', 'cluster': -1}] * 5
        )
        return pd.DataFrame(rows)

    def test_spokespeople_are_ranked_by_speeches_on_the_topic(self, frame):
        result = compute_topic_owners(frame, {0: 'Zero', 1: 'Uno'})
        speakers = result[0]['top_speakers']

        assert [s['speaker'] for s in speakers] == ['Rossi', 'Bianchi']
        assert speakers[0]['focus'] == 80.0

    def test_lift_compares_the_topic_with_the_group_size(self, frame):
        result = compute_topic_owners(frame, {0: 'Zero', 1: 'Uno'})
        party_a = next(p for p in result[0]['parties'] if p['party'] == 'A')

        # A: 8 of 12 topic-0 speeches (66.7%) against 10 of 30 overall (33.3%).
        assert party_a['lift'] == pytest.approx(2.0, abs=0.01)

    def test_unclassified_speeches_are_left_out(self, frame):
        result = compute_topic_owners(frame, {0: 'Zero', 1: 'Uno', -1: 'Non classificato'})

        assert -1 not in result
        assert result[0]['n'] + result[1]['n'] == 30


class TestClusterKeywords:

    def test_labels_come_from_each_clusters_own_words(self):
        docs = ['sanita ospedale'] * 10 + ['scuola docente'] * 10
        terms, vocabulary = build_term_matrix(docs, min_df=1)
        frame = pd.DataFrame({'cluster': [0] * 10 + [1] * 10})

        keywords = cluster_keywords(frame, terms, vocabulary)

        assert set(keywords[0]) == {'sanita', 'ospedale'}
        assert set(keywords[1]) == {'scuola', 'docente'}
