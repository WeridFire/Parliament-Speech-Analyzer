"""
Tests for Temporal Analyzer.

Tests:
- Date utilities
- Topic Trends (shares, counts, bloc activity)
"""

import pandas as pd
import pytest

from backend.analyzers.temporal import TemporalAnalyzer, add_time_columns, compute_topic_trends, parse_date


class TestTemporalAnalyzer:

    def test_analyzer_registration(self):
        from backend.analyzers import AnalyzerRegistry

        assert 'temporal' in AnalyzerRegistry.names()

    def test_only_runs_globally(self):
        assert TemporalAnalyzer.supports('global', 10)[0]
        assert not TemporalAnalyzer.supports('month', 10_000)[0]

    def test_analyzer_compute(self, analyzer_kwargs):
        result = TemporalAnalyzer(**analyzer_kwargs).compute()

        assert 'topic_trends' in result


class TestDateUtilities:

    def test_parse_formats(self):
        assert parse_date('2024-03-15').month == 3
        assert parse_date('15/03/2024').day == 15
        assert parse_date('15 marzo 2024').month == 3
        assert parse_date('not a date') is None

    def test_add_time_columns(self):
        df = add_time_columns(pd.DataFrame({'date': ['2024-03-15']}))

        assert df.loc[0, '_month'] == '2024-03'


class TestTopicTrends:

    @pytest.fixture
    def frame(self):
        rows = (
            [{'date': '2025-01-10', 'cluster': 0, 'group': "Fratelli d'Italia"}] * 30
            + [{'date': '2025-01-11', 'cluster': 1, 'group': 'Partito Democratico'}] * 10
            + [{'date': '2025-02-10', 'cluster': 1, 'group': 'Partito Democratico'}] * 5
            + [{'date': '2025-02-11', 'cluster': -1, 'group': 'Misto'}] * 5
        )
        return pd.DataFrame(rows)

    def test_shares_are_of_each_months_classified_speeches(self, frame):
        result = compute_topic_trends(frame, cluster_labels={0: 'A', 1: 'B', -1: 'Non classificato'})

        assert result['periods'] == ['2025-01', '2025-02']
        assert result['shares']['2025-01'] == {0: 75.0, 1: 25.0}
        # August-style thin months are no longer "falls": February is all topic 1.
        assert result['shares']['2025-02'] == {0: 0.0, 1: 100.0}
        assert result['totals']['2025-02'] == 5

    def test_bloc_volume_counts_every_speech(self, frame):
        result = compute_topic_trends(frame, cluster_labels={0: 'A', 1: 'B'})

        assert result['blocs']['2025-01'] == {'maggioranza': 30, 'opposizione': 10, 'altro': 0}
        assert result['blocs']['2025-02']['altro'] == 5
