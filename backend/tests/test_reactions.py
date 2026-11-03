"""
Tests for the Reactions Analyzer (applause and protests from stage directions).
"""

import pandas as pd
import pytest

from backend.analyzers.reactions import ReactionsAnalyzer, compute_reactions
from backend.analyzers.reactions import applause as applause_module
from backend.core.features import parse_note, parse_notes


class TestNoteParsing:

    @pytest.mark.parametrize('note, expected', [
        ("Applausi dei deputati del gruppo Partito Democratico-Italia Democratica e Progressista",
         ('applausi', ('Partito Democratico',))),
        ("Applausi dei deputati dei gruppi MoVimento 5 Stelle e Alleanza Verdi e Sinistra",
         ('applausi', ('MoVimento 5 Stelle', 'Alleanza Verdi e Sinistra'))),
        ("Applausi dal Gruppo PD-IDP", ('applausi', ('Partito Democratico',))),
        ("Applausi dai Gruppi FdI e LSP-PSd'Az", ('applausi', ("Fratelli d'Italia", 'Lega'))),
        ("Proteste dei deputati del gruppo Lega-Salvini Premier", ('proteste', ('Lega',))),
        ("Commenti di deputati del gruppo Fratelli d'Italia", ('commenti', ("Fratelli d'Italia",))),
        ("Applausi", ('applausi', ())),
        ("testo corretto", None),
    ])
    def test_stage_directions(self, note, expected):
        result = parse_note(note)
        if expected is None:
            assert result is None
        else:
            assert result[0] == expected[0]
            assert set(result[1]) == set(expected[1])

    def test_misto_subgroups_are_not_generic_misto(self):
        _, groups = parse_note("Applausi dei deputati del gruppo Misto-+Europa")

        assert groups == ('+Europa',)

    def test_missing_notes(self):
        assert parse_notes(None) == []
        assert parse_notes(float('nan')) == []


@pytest.fixture
def frame(monkeypatch):
    monkeypatch.setattr(applause_module, 'MIN_PARTY_SPEECHES', 1)
    pd_speech = ('Partito Democratico', 'opposizione')
    fdi_speech = ("Fratelli d'Italia", 'maggioranza')
    rows = [
        # A PD speech applauded by PD and, across the aisle, by FdI
        {'deputy': 'Rossi', 'group': pd_speech[0], 'bloc': pd_speech[1],
         'note_events': [['applausi', ['Partito Democratico']], ['applausi', ["Fratelli d'Italia"]]]},
        # A PD speech applauded twice by PD: one speech, counted once
        {'deputy': 'Rossi', 'group': pd_speech[0], 'bloc': pd_speech[1],
         'note_events': [['applausi', ['Partito Democratico']], ['applausi', ['Partito Democratico']]]},
        # An FdI speech the PD protested
        {'deputy': 'Neri', 'group': fdi_speech[0], 'bloc': fdi_speech[1],
         'note_events': [['proteste', ['Partito Democratico']]]},
        {'deputy': 'Neri', 'group': fdi_speech[0], 'bloc': fdi_speech[1], 'note_events': []},
    ]
    return pd.DataFrame(rows)


class TestReactions:

    def test_matrices_count_speeches_not_events(self, frame):
        result = compute_reactions(frame)
        index = {p: i for i, p in enumerate(result['parties'])}
        pd_i, fdi_i = index['Partito Democratico'], index["Fratelli d'Italia"]

        assert result['applause'][pd_i][pd_i] == 2
        assert result['applause'][fdi_i][pd_i] == 1
        assert result['dissent'][pd_i][fdi_i] == 1

    def test_cross_applause_rate_is_per_100_speeches_of_the_speakers_group(self, frame):
        [cross] = compute_reactions(frame)['cross_applause']

        assert (cross['from'], cross['to']) == ("Fratelli d'Italia", 'Partito Democratico')
        assert cross['rate'] == 50.0

    def test_bloc_applause(self, frame):
        blocs = compute_reactions(frame)['bloc_applause']

        assert blocs['opposizione']['applauded_by_other_bloc'] == 1
        assert blocs['maggioranza']['applauded_by_other_bloc'] == 0

    def test_speakers_applauded_and_contested_by_others(self, frame):
        result = compute_reactions(frame)

        assert result['top_cross_applauded'][0]['speaker'] == 'Rossi'
        assert result['top_cross_applauded'][0]['n'] == 1
        assert result['top_contested'][0]['speaker'] == 'Neri'

    def test_analyzer_skips_a_slice_without_stage_directions(self, analyzer_kwargs):
        assert ReactionsAnalyzer(**analyzer_kwargs).compute() == {}


class TestSenatoStyleNotes:
    """The Senato records reactions without naming the group."""

    def test_compound_directions_are_split(self):
        assert parse_notes(['Applausi. Commenti']) == [['applausi', []], ['commenti', []]]
        assert parse_notes(['Applausi.Commenti']) == [['applausi', []], ['commenti', []]]

    def test_received_rates_need_no_attribution(self, monkeypatch):
        monkeypatch.setattr(applause_module, 'MIN_PARTY_SPEECHES', 1)
        df = pd.DataFrame([
            {'deputy': 'a', 'group': 'Partito Democratico', 'note_events': [['applausi', []]]},
            {'deputy': 'a', 'group': 'Partito Democratico', 'note_events': []},
            {'deputy': 'b', 'group': 'Lega', 'note_events': [['commenti', []]]},
        ])
        result = compute_reactions(df)

        assert result['received']['Partito Democratico'] == {'applause': 50.0, 'dissent': 0.0}
        assert result['received']['Lega'] == {'applause': 0.0, 'dissent': 100.0}
        assert result['coverage']['attributed'] is False
