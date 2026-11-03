"""
Tests for the Mentions Analyzer (who mentions whom).
"""

import pandas as pd

from backend.analyzers.mentions import MentionsAnalyzer, compute_mentions
from backend.analyzers.mentions import figures as figures_module
from backend.core.features import find_mentions


class TestFindMentions:

    def test_case_sensitive_names(self):
        assert find_mentions('Il presidente Conte ha detto') == ['conte']
        assert find_mentions('il conte di Montecristo') == []

    def test_each_figure_counts_once_per_speech(self):
        assert find_mentions('Meloni, Meloni e ancora Meloni') == ['meloni']

    def test_a_figure_does_not_mention_themselves(self):
        assert find_mentions('Io, Giorgia Meloni, rispondo', speaker='Meloni Giorgia') == []

    def test_old_network_failure_mode(self):
        """Common words that are also surnames are not tracked at all."""
        assert find_mentions('Con speranza e fontana e costa') == []


class TestComputeMentions:

    def test_rates_are_per_group(self, monkeypatch):
        monkeypatch.setattr(figures_module, 'MIN_PARTY_SPEECHES', 1)
        monkeypatch.setattr(figures_module, 'MIN_FIGURE_MENTIONS', 1)
        df = pd.DataFrame([
            {'deputy': 'a', 'group': 'Partito Democratico', 'mentions': ['meloni']},
            {'deputy': 'a', 'group': 'Partito Democratico', 'mentions': []},
            {'deputy': 'b', 'group': "Fratelli d'Italia", 'mentions': ['schlein', 'meloni']},
        ])
        result = compute_mentions(df)
        figures = {f['id']: f for f in result['figures']}

        assert figures['meloni']['n'] == 2
        assert figures['meloni']['by_bloc'] == {'maggioranza': 100.0, 'opposizione': 50.0}
        assert figures['meloni']['top_speakers'][0]['speaker'] in {'a', 'b'}

        rates = dict(zip(result['matrix']['parties'], result['matrix']['rates']))
        meloni = result['matrix']['figures'].index('meloni')
        assert rates['Partito Democratico'][meloni] == 50.0

    def test_analyzer_compute(self, analyzer_kwargs):
        result = MentionsAnalyzer(**analyzer_kwargs).compute()

        assert {'figures', 'matrix'} <= set(result)
