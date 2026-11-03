"""
Parliamentary groups: one canonical name per group, and the bloc it sits in.

The same group is labelled three different ways depending on where the label
comes from: "PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA" in the
Camera register, "PD-IDP" next to a senator's name, "Partito Democratico-Italia
Democratica e Progressista" in a stage direction. The previous exact-match table
covered the short codes only, so every long Camera label passed through as-is:
"M5S" and "MOVIMENTO 5 STELLE" were two parties, and no Camera group was ever
recognised as majority or opposition - the coalition analyses compared nothing
with nothing.

Labels are now reduced to a key (no case, accents or punctuation) and matched by
prefix, most specific rule first.
"""

import re
import unicodedata

# Blocs. Governo is counted with the majority: ministers speak for it.
MAGGIORANZA = 'maggioranza'
OPPOSIZIONE = 'opposizione'
ALTRO = 'altro'

# (canonical name, bloc, key prefixes). Order matters: the Misto sub-groups
# must be tried before bare Misto, or they collapse into it.
GROUPS = [
    ("Fratelli d'Italia", MAGGIORANZA, (r'FRATELLIDITALIA', r'FDI')),
    ("Lega", MAGGIORANZA, (r'LEGA', r'LSP')),
    ("Forza Italia", MAGGIORANZA, (r'FORZAITALIA', r'FIBPPPE', r'FIPPE', r'FI$')),
    ("Noi Moderati", MAGGIORANZA, (r'NOIMODERATI', r'CDINM', r'CIVICIDITALIA', r'NM')),
    ("Governo", MAGGIORANZA, (r'GOVERNO$',)),
    ("Partito Democratico", OPPOSIZIONE, (r'PARTITODEMOCRATICO', r'PD')),
    ("MoVimento 5 Stelle", OPPOSIZIONE, (r'MOVIMENTO5STELLE', r'M5S')),
    ("Alleanza Verdi e Sinistra", OPPOSIZIONE, (r'ALLEANZAVERDI', r'AVS', r'MISTOAVS')),
    # The joint Azione-Italia Viva group split in 2024. Members whose old
    # membership the register still reports as open went to Azione, which is
    # why the joint label folds into it rather than into Italia Viva.
    ("Azione", OPPOSIZIONE, (r'AZIONE', r'AZPERRE', r'MISTOAZ')),
    ("Italia Viva", OPPOSIZIONE, (r'ITALIAVIVA', r'IVC', r'IV$')),
    ("+Europa", OPPOSIZIONE, (r'MISTOEUROPA', r'MISTOPIUEUROPA', r'PIUEUROPA', r'EUROPA$')),
    ("Minoranze Linguistiche", ALTRO, (r'MISTOMINORANZE', r'MISTOMINLING')),
    ("Per le Autonomie", ALTRO, (r'AUTSVP', r'PERLEAUTONOMIE', r'AUT$')),
    ("Misto", ALTRO, (r'MISTO',)),
]

_RULES = [
    (re.compile('^(?:' + '|'.join(prefixes) + ')'), name)
    for name, _bloc, prefixes in GROUPS
]
PARTY_BLOC = {name: bloc for name, bloc, _prefixes in GROUPS}
CANONICAL_PARTIES = [name for name, _bloc, _prefixes in GROUPS]


def label_key(label: str) -> str:
    """Squash case, accents and punctuation: "Lega - Salvini Premier" -> "LEGASALVINIPREMIER"."""
    text = unicodedata.normalize('NFD', str(label))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return re.sub(r'[^A-Z0-9+]', '', text.upper()).replace('+', 'PIU')


def normalize_party(label) -> str:
    """
    Canonical group name for any label either chamber emits.

    An unrecognised label is returned trimmed rather than guessed at, so a new
    group shows up under its own name instead of borrowing another's.
    """
    if label is None:
        return ''
    text = str(label).strip()
    if not text:
        return ''

    key = label_key(text)
    for pattern, name in _RULES:
        if pattern.match(key):
            return name
    return text


def party_bloc(party: str) -> str:
    """'maggioranza', 'opposizione' or 'altro' for a canonical group name."""
    return PARTY_BLOC.get(party, ALTRO)


# Group names as stage directions print them - "Applausi dei deputati del
# gruppo Lega-Salvini Premier", "Applausi dal Gruppo PD-IDP" - matched against
# the original text. Misto sub-groups are listed so that "Misto-AVS" is read as
# AVS and not as the generic Misto.
NOTE_GROUP_PATTERNS = {
    "Fratelli d'Italia": (r"Fratelli d['’]Italia", r"\bFdI\b"),
    "Lega": (r"\bLega\b", r"\bLSP\b"),
    "Forza Italia": (r"Forza Italia", r"\bFI-BP-PPE\b", r"\bFI\b"),
    "Noi Moderati": (r"Noi Moderati", r"Cd['’]I-NM", r"\bNM\b"),
    "Partito Democratico": (r"Partito Democratico", r"\bPD-IDP\b", r"\bPD\b"),
    "MoVimento 5 Stelle": (r"Movimento 5 Stelle", r"\bM5S\b"),
    "Alleanza Verdi e Sinistra": (r"Alleanza Verdi e Sinistra", r"\bAVS\b"),
    "Azione": (r"\bAzione\b", r"\bAz-PER-RE\b", r"\bAz-RE\b"),
    "Italia Viva": (r"Italia Viva", r"\bIV-C-RE\b"),
    "+Europa": (r"\+Europa",),
    "Minoranze Linguistiche": (r"Minoranze Linguistiche",),
    "Per le Autonomie": (r"\bAut \(SVP", r"Per le Autonomie"),
    "Misto": (r"\bMisto\b(?!\s*-)",),
}

NOTE_GROUP_RES = {
    name: re.compile('|'.join(patterns), re.IGNORECASE)
    for name, patterns in NOTE_GROUP_PATTERNS.items()
}
