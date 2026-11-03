"""
Tests for the Blocs Analyzer (majority vs opposition).
"""

import pandas as pd
import pytest

from backend.analyzers.blocs import BlocsAnalyzer, compute_bloc_summary, compute_issue_ownership


@pytest.fixture
def frame():
    # The opposition speaks three times as much; topic 0 is a larger share of
    # the majority's own speeches, topic 2 is evenly attended.
    rows = (
        [{'group': "Fratelli d'Italia", 'cluster': 0, 'deputy': 'm'}] * 50
        + [{'group': "Fratelli d'Italia", 'cluster': 2, 'deputy': 'm'}] * 50
        + [{'group': 'Partito Democratico', 'cluster': 0, 'deputy': 'o'}] * 60
        + [{'group': 'Partito Democratico', 'cluster': 1, 'deputy': 'o'}] * 90
        + [{'group': 'Partito Democratico', 'cluster': 2, 'deputy': 'o'}] * 150
    )
    return pd.DataFrame(rows)


LABELS = {0: 'Fisco', 1: 'Scuola', 2: 'Esteri'}


class TestIssueOwnership:

    def test_ownership_uses_attention_not_volume(self, frame):
        """By raw counts the opposition 'owns' topic 0 (60 vs 50); by attention it does not."""
        entries = {e['topic']: e for e in compute_issue_ownership(frame, LABELS)}

        assert entries[0]['maggioranza'] == 50.0
        assert entries[0]['opposizione'] == 20.0
        assert entries[0]['owner'] == 'maggioranza'

    def test_balanced_topic_is_shared(self, frame):
        entries = {e['topic']: e for e in compute_issue_ownership(frame, LABELS)}

        assert entries[2]['owner'] == 'condiviso'

    def test_topic_one_side_never_touches_is_not_classified(self, frame):
        entries = {e['topic']: e for e in compute_issue_ownership(frame, LABELS)}

        assert entries[1]['ratio'] is None

    def test_sorted_from_majority_to_opposition(self, frame):
        ratios = [e['ratio'] for e in compute_issue_ownership(frame, LABELS) if e['ratio'] is not None]

        assert ratios == sorted(ratios, reverse=True)


class TestSummary:

    def test_shares_and_speakers(self, frame):
        summary = compute_bloc_summary(frame.assign(n_words=100))

        assert summary['maggioranza']['n_speeches'] == 100
        assert summary['opposizione']['share'] == 75.0
        assert summary['opposizione']['n_speakers'] == 1


class TestBlocsAnalyzer:

    def test_analyzer_compute(self, analyzer_kwargs):
        result = BlocsAnalyzer(**analyzer_kwargs).compute()

        assert {'summary', 'ownership', 'keywords'} <= set(result)
