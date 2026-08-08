"""
Tests for the shared scoring conventions.

The behaviour that matters is that the top of the scale stays informative. The
previous polarization formula multiplied a marker density by 500 and clamped it
to 100, so every speaker above roughly a fifth marker density collapsed onto the
same score - exactly where the metric claimed to discriminate.
"""

import pytest

from backend.analyzers.sentiment.polarization import compute_polarization_score, compute_polarization_scores
from backend.scoring import Score, percentile_ranks, rate_per_thousand, score_map
from backend.scoring.normalize import classify_by_percentile

import pandas as pd


class TestRatePerThousand:

    def test_basic_rate(self):
        assert rate_per_thousand(5, 1000) == 5.0
        assert rate_per_thousand(1, 500) == 2.0

    def test_empty_text_is_zero_not_an_error(self):
        assert rate_per_thousand(3, 0) == 0.0

    def test_is_unbounded(self):
        """No ceiling: a dense text must be able to out-score a very dense one."""
        assert rate_per_thousand(300, 1000) == 300.0
        assert rate_per_thousand(600, 1000) > rate_per_thousand(300, 1000)


class TestPercentileRanks:

    def test_spans_the_full_range(self):
        ranks = percentile_ranks({'a': 1, 'b': 2, 'c': 3})
        assert ranks['a'] == 0.0
        assert ranks['c'] == 100.0
        assert ranks['b'] == 50.0

    def test_ties_share_a_rank(self):
        """A corpus where many speakers score zero must not rank them apart."""
        ranks = percentile_ranks({'a': 0, 'b': 0, 'c': 0, 'd': 9})
        assert ranks['a'] == ranks['b'] == ranks['c']
        assert ranks['d'] == 100.0

    def test_single_value(self):
        assert percentile_ranks({'only': 5}) == {'only': 50.0}

    def test_empty(self):
        assert percentile_ranks({}) == {}

    def test_order_is_preserved_regardless_of_magnitude(self):
        """Extreme outliers change ranks, not the ordering."""
        modest = percentile_ranks({'a': 1, 'b': 2, 'c': 3})
        extreme = percentile_ranks({'a': 1, 'b': 2, 'c': 10_000})
        assert modest == extreme


class TestScoreMap:

    def test_shape(self):
        scored = score_map({'x': 4.0, 'y': 8.0}, {'x': 10, 'y': 3})
        assert scored['x'] == {'raw': 4.0, 'pct': 0.0, 'n': 10}
        assert scored['y'] == {'raw': 8.0, 'pct': 100.0, 'n': 3}

    def test_missing_counts_default_to_zero(self):
        assert score_map({'x': 1.0})['x']['n'] == 0

    def test_score_rounds_for_transport(self):
        assert Score(raw=1.23456, pct=99.98, n=2).as_dict() == {'raw': 1.23, 'pct': 100.0, 'n': 2}


class TestClassification:

    def test_buckets_by_standing(self):
        assert classify_by_percentile(90) == 'alta'
        assert classify_by_percentile(50) == 'media'
        assert classify_by_percentile(10) == 'bassa'


class TestPolarization:

    def test_markers_raise_the_rate(self):
        neutral = compute_polarization_score(
            'Il provvedimento introduce misure tecniche per il settore agricolo nazionale.'
        )
        oppositional = compute_polarization_score(
            'Noi contro di loro, sempre: loro sono i nemici del paese, noi difendiamo tutti.'
        )
        assert oppositional['rate'] > neutral['rate']

    def test_empty_text_scores_zero(self):
        assert compute_polarization_score('')['rate'] == 0.0

    def test_extreme_texts_remain_distinguishable(self):
        """The saturation bug: both of these used to score exactly 100."""
        dense = compute_polarization_score('noi loro noi loro contro nemici')
        denser = compute_polarization_score('noi contro loro ' * 20)
        assert dense['rate'] != denser['rate']

    @pytest.fixture
    def scored(self):
        rows = []
        for i in range(12):
            oppositional = i >= 8
            text = (
                'Noi contro di loro, sono i nemici del paese e noi li combattiamo sempre.'
                if oppositional
                else 'Il provvedimento introduce misure tecniche per il settore interessato.'
            )
            rows.append({
                'deputy': f'Speaker_{i % 4}',
                'group': 'Party_A' if i % 2 == 0 else 'Party_B',
                'cleaned_text': text,
            })
        return compute_polarization_scores(pd.DataFrame(rows))

    def test_emits_the_shared_score_shape(self, scored):
        for entry in scored['by_speaker'].values():
            assert {'raw', 'pct', 'n'} <= set(entry)
            assert 0 <= entry['pct'] <= 100
            assert entry['n'] >= 3

    def test_unit_is_declared(self, scored):
        assert scored['unit'] == 'markers per 1000 words'

    def test_rankings_are_ordered_by_raw_rate(self, scored):
        raws = [entry['raw'] for entry in scored['top_polarizers']]
        assert raws == sorted(raws, reverse=True)

    def test_parties_are_scored(self, scored):
        assert set(scored['by_party']) == {'Party_A', 'Party_B'}
