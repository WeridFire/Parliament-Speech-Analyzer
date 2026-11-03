"""
Tests for Speaker Analyzer.

Tests:
- Profiles aggregated from per-speech features
- Vocabulary richness (MATTR)
- Rankings
"""

import pandas as pd
import pytest

from backend.analyzers.speaker import SpeakerAnalyzer, compute_speaker_profiles, mattr
from backend.core.features import add_speech_features


class TestSpeakerAnalyzer:

    def test_analyzer_registration(self):
        from backend.analyzers import AnalyzerRegistry

        assert 'speaker' in AnalyzerRegistry.names()

    def test_analyzer_compute(self, mock_data, analyzer_kwargs):
        result = SpeakerAnalyzer(**analyzer_kwargs).compute()

        assert set(result) == {'by_speaker', 'rankings'}
        assert set(result['by_speaker']) <= set(mock_data.df['deputy'])

    def test_rankings_are_pairs_in_descending_order(self, analyzer_kwargs):
        rankings = SpeakerAnalyzer(**analyzer_kwargs).compute()['rankings']

        for entries in rankings.values():
            values = [value for _, value in entries]
            assert values == sorted(values, reverse=True)


class TestProfiles:

    @pytest.fixture
    def frame(self):
        rows = []
        for i in range(6):
            rows.append({
                'deputy': 'Rossi', 'group': 'Partito Democratico', 'cluster': i % 2,
                'date': f'2025-0{1 + i % 3}-10',
                'raw_text': 'Io non sono d\'accordo? Il 15% delle famiglie paga 3,5 miliardi.',
                'notes': ['Applausi dei deputati del gruppo Lega-Salvini Premier'] if i == 0 else [],
            })
        return add_speech_features(pd.DataFrame(rows))

    def test_counts_and_activity(self, frame):
        profile = compute_speaker_profiles(frame, {0: 'A', 1: 'B'})['Rossi']

        assert profile['n_speeches'] == 6
        assert profile['active_months'] == 3
        assert profile['total_months'] == 3
        assert profile['bloc'] == 'opposizione'

    def test_rates_are_per_thousand_words(self, frame):
        profile = compute_speaker_profiles(frame, {0: 'A', 1: 'B'})['Rossi']
        words = profile['verbosity']['total_words']

        assert profile['linguistic']['question_rate'] == pytest.approx(6 / words * 1000, abs=0.01)
        assert profile['linguistic']['data_citation_rate'] > 0

    def test_top_topics_and_reactions(self, frame):
        profile = compute_speaker_profiles(frame, {0: 'A', 1: 'B'})['Rossi']

        assert [t['share'] for t in profile['top_topics']] == [50.0, 50.0]
        assert profile['reactions']['applauded_by_others'] == 1


class TestVocabularyRichness:

    def test_mattr_does_not_fall_with_length(self):
        """The TTR bug: the same style, said for longer, looked poorer."""
        words = [f'w{i % 300}' for i in range(600)]

        assert mattr(words * 4, window=200) == pytest.approx(mattr(words, window=200), abs=0.02)

    def test_mattr_rewards_variety(self):
        repetitive = ['la', 'legge'] * 600
        varied = [f'parola{i}' for i in range(1200)]

        assert mattr(varied) > mattr(repetitive)
