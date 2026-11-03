"""
Tests for corpus preparation: group normalisation, the chair filter and the
per-speech features.
"""

import pandas as pd
import pytest

from backend.config import normalize_party, party_bloc
from backend.core import prepare_speeches
from backend.core.features import add_speech_features, gulpease

BODY = ' '.join(['parola'] * 40)


class TestNormalizeParty:

    @pytest.mark.parametrize('label, expected', [
        ('FORZA ITALIA - BERLUSCONI PRESIDENTE - PPE', 'Forza Italia'),
        ('FI-BP-PPE', 'Forza Italia'),
        ('MOVIMENTO 5 STELLE', 'MoVimento 5 Stelle'),
        ('M5S', 'MoVimento 5 Stelle'),
        ('PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA', 'Partito Democratico'),
        ('PD-IDP', 'Partito Democratico'),
        ("LSP-PSd'Az", 'Lega'),
        ('Misto-AVS', 'Alleanza Verdi e Sinistra'),
        ('MISTO-+EUROPA', '+Europa'),
        ('MISTO', 'Misto'),
        ('ITALIA VIVA-IL CENTRO-RENEW EUROPE', 'Italia Viva'),
        ("Cd'I-NM (UDC-CI-NcI-IaC)-MAIE", 'Noi Moderati'),
        ('Gruppo Nuovo', 'Gruppo Nuovo'),
    ])
    def test_labels_from_both_chambers(self, label, expected):
        assert normalize_party(label) == expected

    def test_blocs(self):
        assert party_bloc('Forza Italia') == 'maggioranza'
        assert party_bloc('Governo') == 'maggioranza'
        assert party_bloc('Azione') == 'opposizione'
        assert party_bloc('Misto') == 'altro'


class TestPrepareSpeeches:

    def frame(self, **overrides):
        row = {
            'deputy': 'Tajani Antonio [FORZA ITALIA - BERLUSCONI PRESIDENTE - PPE]',
            'speaker_base': 'Tajani Antonio',
            'group': 'FORZA ITALIA - BERLUSCONI PRESIDENTE - PPE',
            'text': BODY,
            'role': '',
            'role_category': '',
        }
        row.update(overrides)
        return pd.DataFrame([row])

    def test_forza_italia_is_not_mistaken_for_the_chair(self):
        """Its group label contains "PRESIDENTE"; every FI speech used to be dropped."""
        df = prepare_speeches(self.frame())

        assert len(df) == 1
        assert df.loc[0, 'group'] == 'Forza Italia'
        assert df.loc[0, 'deputy'] == 'Tajani Antonio [Forza Italia]'
        assert df.loc[0, 'bloc'] == 'maggioranza'

    def test_the_chair_is_dropped_by_role(self):
        assert prepare_speeches(self.frame(role='presidente', role_category='presidenza')).empty

    def test_short_speeches_are_dropped(self):
        assert prepare_speeches(self.frame(text='troppo breve')).empty

    def test_original_text_is_kept_for_display(self):
        df = prepare_speeches(self.frame(text='Grazie, Presidente. ' + BODY.upper()))

        assert df.loc[0, 'raw_text'].startswith('Grazie, Presidente.')
        assert df.loc[0, 'cleaned_text'] == df.loc[0, 'cleaned_text'].lower()


class TestSpeechFeatures:

    def test_gulpease_bounds(self):
        assert gulpease(0, 0, 0) == 0
        assert 0 <= gulpease(10, 1, 60) <= 100

    def test_features_are_added(self):
        df = add_speech_features(pd.DataFrame([{
            'deputy': 'x',
            'raw_text': 'Perché? Il 20% di noi contro loro. Lo ha detto Meloni.',
            'notes': ['Applausi dei deputati del gruppo Lega-Salvini Premier'],
        }]))
        row = df.iloc[0]

        assert row['questions'] == 1
        assert row['numerics'] == 1
        assert row['polarization'] > 0
        assert row['mentions'] == ['meloni']
        assert row['note_events'] == [['applausi', ['Lega']]]
