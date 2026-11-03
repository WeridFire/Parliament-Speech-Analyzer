"""
Public figures tracked by the mentions analysis ("chi nomina chi").

A curated list rather than every member of parliament: the previous mention
network matched every speaker's surname against every speech, which at the
Camera found nothing at all (it required surnames in capitals, and the register
stores "Cognome Nome") and would otherwise have counted "Speranza", "Fontana" or
"Costa" every time the common word appeared.

Patterns are matched case-sensitively against the original text, so "Conte" the
leader is found and "il conte" the noun is not. `group` is the kind of figure,
not their party: a coarse label that does not go stale when a portfolio changes
hands.
"""

GOVERNO = 'governo'
OPPOSIZIONE = 'opposizione'
ISTITUZIONI = 'istituzioni'
ESTERI = 'esteri'

FIGURE_GROUP_LABELS = {
    GOVERNO: 'Governo e maggioranza',
    OPPOSIZIONE: 'Leader di opposizione',
    ISTITUZIONI: 'Istituzioni',
    ESTERI: 'Leader stranieri',
}

FIGURES = [
    # Government and majority leaders
    {'id': 'meloni', 'name': 'Giorgia Meloni', 'group': GOVERNO, 'party': "Fratelli d'Italia", 'patterns': [r'\bMeloni\b']},
    {'id': 'salvini', 'name': 'Matteo Salvini', 'group': GOVERNO, 'party': 'Lega', 'patterns': [r'\bSalvini\b']},
    {'id': 'tajani', 'name': 'Antonio Tajani', 'group': GOVERNO, 'party': 'Forza Italia', 'patterns': [r'\bTajani\b']},
    {'id': 'giorgetti', 'name': 'Giancarlo Giorgetti', 'group': GOVERNO, 'party': 'Lega', 'patterns': [r'\bGiorgetti\b']},
    {'id': 'nordio', 'name': 'Carlo Nordio', 'group': GOVERNO, 'party': '', 'patterns': [r'\bNordio\b']},
    {'id': 'piantedosi', 'name': 'Matteo Piantedosi', 'group': GOVERNO, 'party': '', 'patterns': [r'\bPiantedosi\b']},
    {'id': 'crosetto', 'name': 'Guido Crosetto', 'group': GOVERNO, 'party': "Fratelli d'Italia", 'patterns': [r'\bCrosetto\b']},
    {'id': 'valditara', 'name': 'Giuseppe Valditara', 'group': GOVERNO, 'party': 'Lega', 'patterns': [r'\bValditara\b']},
    {'id': 'urso', 'name': 'Adolfo Urso', 'group': GOVERNO, 'party': "Fratelli d'Italia", 'patterns': [r'\bUrso\b']},
    {'id': 'lollobrigida', 'name': 'Francesco Lollobrigida', 'group': GOVERNO, 'party': "Fratelli d'Italia", 'patterns': [r'\bLollobrigida\b']},
    {'id': 'schillaci', 'name': 'Orazio Schillaci', 'group': GOVERNO, 'party': '', 'patterns': [r'\bSchillaci\b']},
    {'id': 'pichetto', 'name': 'Gilberto Pichetto Fratin', 'short': 'Pichetto Fratin', 'group': GOVERNO, 'party': 'Forza Italia', 'patterns': [r'\bPichetto\b']},
    {'id': 'santanche', 'name': 'Daniela Santanchè', 'group': GOVERNO, 'party': "Fratelli d'Italia", 'patterns': [r'\bSantanch[eèé]\b']},
    {'id': 'bernini', 'name': 'Anna Maria Bernini', 'group': GOVERNO, 'party': 'Forza Italia', 'patterns': [r'\bBernini\b']},
    {'id': 'calderone', 'name': 'Marina Calderone', 'group': GOVERNO, 'party': '', 'patterns': [r'\bCalderone\b']},
    {'id': 'roccella', 'name': 'Eugenia Roccella', 'group': GOVERNO, 'party': "Fratelli d'Italia", 'patterns': [r'\bRoccella\b']},
    {'id': 'musumeci', 'name': 'Nello Musumeci', 'group': GOVERNO, 'party': "Fratelli d'Italia", 'patterns': [r'\bMusumeci\b']},
    {'id': 'casellati', 'name': 'Maria Elisabetta Alberti Casellati', 'group': GOVERNO, 'party': 'Forza Italia', 'patterns': [r'\bCasellati\b']},
    {'id': 'lupi', 'name': 'Maurizio Lupi', 'group': GOVERNO, 'party': 'Noi Moderati', 'patterns': [r'\bLupi\b']},

    # Opposition leaders
    {'id': 'schlein', 'name': 'Elly Schlein', 'group': OPPOSIZIONE, 'party': 'Partito Democratico', 'patterns': [r'\bSchlein\b']},
    {'id': 'conte', 'name': 'Giuseppe Conte', 'group': OPPOSIZIONE, 'party': 'MoVimento 5 Stelle', 'patterns': [r'\bConte\b']},
    {'id': 'calenda', 'name': 'Carlo Calenda', 'group': OPPOSIZIONE, 'party': 'Azione', 'patterns': [r'\bCalenda\b']},
    {'id': 'renzi', 'name': 'Matteo Renzi', 'group': OPPOSIZIONE, 'party': 'Italia Viva', 'patterns': [r'\bRenzi\b']},
    {'id': 'fratoianni', 'name': 'Nicola Fratoianni', 'group': OPPOSIZIONE, 'party': 'Alleanza Verdi e Sinistra', 'patterns': [r'\bFratoianni\b']},
    {'id': 'bonelli', 'name': 'Angelo Bonelli', 'group': OPPOSIZIONE, 'party': 'Alleanza Verdi e Sinistra', 'patterns': [r'\bBonelli\b']},
    {'id': 'magi', 'name': 'Riccardo Magi', 'group': OPPOSIZIONE, 'party': '+Europa', 'patterns': [r'\bMagi\b(?! Re)']},

    # Institutions
    {'id': 'mattarella', 'name': 'Sergio Mattarella', 'group': ISTITUZIONI, 'party': '', 'patterns': [r'\bMattarella\b']},

    # Foreign leaders
    {'id': 'trump', 'name': 'Donald Trump', 'group': ESTERI, 'party': '', 'patterns': [r'\bTrump\b']},
    {'id': 'putin', 'name': 'Vladimir Putin', 'group': ESTERI, 'party': '', 'patterns': [r'\bPutin\b']},
    {'id': 'zelensky', 'name': 'Volodymyr Zelensky', 'group': ESTERI, 'party': '', 'patterns': [r'\bZelensk(?:y|yj|yy|i)\b']},
    {'id': 'netanyahu', 'name': 'Benjamin Netanyahu', 'group': ESTERI, 'party': '', 'patterns': [r'\bNetanyahu\b']},
    {'id': 'von_der_leyen', 'name': 'Ursula von der Leyen', 'short': 'von der Leyen', 'group': ESTERI, 'party': '', 'patterns': [r'\b[Vv]on der Leyen\b']},
]
