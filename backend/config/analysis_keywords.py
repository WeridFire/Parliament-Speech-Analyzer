"""
Lexicons for the marker-based language metrics.

What used to live here and was removed, with the reason:
  * populist / anti-establishment / emotional / institutional / sovereignist /
    progressive lists - built on words that are neutral in parliament
    ("cittadini", "sistema", "regole", "diritti"), so they measured topic, not
    rhetoric;
  * crisis lexicon - mostly topical words ("guerra", "inflazione", "vittime"),
    so an alarm index rose whenever a war was debated;
  * positive/negative sentiment lists - 25 words each, where "problema",
    "rischio" and "obiettivo" decided the tone of a speech.
"""

# =============================================================================
# POLARIZATION MARKERS ("us vs them")
# =============================================================================

POLARIZATION_PRONOUNS = {
    'noi', 'loro', 'voi', 'nostro', 'nostra', 'nostri', 'nostre',
    'vostro', 'vostra', 'vostri', 'vostre'
}

ADVERSATIVE_TERMS = {
    'contro', 'nemici', 'nemico', 'avversari', 'avversario',
    'opposti', 'opposto', 'combattere', 'combattiamo', 'sconfiggere',
    'respingere', 'respingiamo', 'bloccare', 'fermare', 'impedire',
    'difendere', 'difendiamo', 'proteggere', 'proteggiamo',
    'minacciano', 'attaccano', 'vogliono', 'pretendono'
}

US_THEM_PATTERNS = [
    'noi contro loro', 'noi e loro', 'da una parte', 'dall\'altra parte',
    'chi sta con', 'chi sta contro', 'chi vuole', 'chi non vuole'
]


# =============================================================================
# LINGUISTIC PROFILE MARKERS
# =============================================================================

SELF_REFERENCE_WORDS = {'io', 'mio', 'mia', 'miei', 'mie', 'me', 'mi', 'personalmente'}

NEGATION_WORDS = {
    'non', 'no', 'mai', 'nessuno', 'nulla', 'niente',
    'neanche', 'nemmeno', 'neppure', 'senza'
}

# Quantities a speaker cites: percentages, sums of money, large figures and
# decimals. Bare four-digit numbers are left out - they are mostly years and
# article numbers, not data.
NUMERIC_PATTERNS = [
    r'\d+(?:[.,]\d+)?\s?%',
    r'\d+(?:[.,]\d+)?\s?per cento',
    r'€\s?\d+',
    r'\d+(?:[.,]\d+)?\s?(?:euro|milioni|miliardi)',
    r'\d+[.,]\d+',
]
