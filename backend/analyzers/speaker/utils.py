"""
Constants and utilities for speaker analysis.
"""
import re

# Self-reference patterns (Italian)
SELF_REFERENCE_WORDS = {
    'io', 'mio', 'mia', 'miei', 'mie', 
    'me', 'mi',
    'personalmente'
}

# Negation patterns
NEGATION_WORDS = {
    'non', 'no', 'mai', 'nessuno', 'nulla', 'niente', 
    'neanche', 'nemmeno', 'neppure', 'senza'
}

# Temporal orientation markers
FUTURE_MARKERS = {
    'sarà', 'saranno', 'saremo', 'sarete',
    'faremo', 'faranno', 'farete',
    'vogliamo', 'vogliono', 'vorremo',
    'proponiamo', 'proporremo',
    'futuro', 'domani', 'prossimo', 'prossima', 'prossimi', 'prossime',
    'sviluppo', 'crescita', 'obiettivo', 'obiettivi', 'progetto', 'progetti'
}

PAST_MARKERS = {
    'era', 'erano', 'eravamo',
    'fu', 'furono', 'fummo',
    'abbiamo fatto', 'hanno fatto',
    'passato', 'ieri', 'precedente', 'precedenti',
    'storia', 'storico', 'tradizione', 'tradizionale'
}

# Numeric data patterns
NUMERIC_PATTERNS = [
    r'\d+%',  # percentages
    r'€\s?\d+', r'\d+\s?euro',  # currency
    r'\d+\s?(milioni|miliardi)',  # large numbers
    r'\d{4}',  # years
    r'\d+[\.,]\d+',  # decimal numbers
]
NUMERIC_REGEX = re.compile('|'.join(NUMERIC_PATTERNS), re.IGNORECASE)


def tokenize_simple(text: str) -> list[str]:
    """Simple tokenization: lowercase, split on whitespace."""
    return text.lower().split()


def count_sentences(text: str) -> int:
    """Count sentences based on punctuation."""
    # Split on sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)
    return max(1, len([s for s in sentences if s.strip()]))


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def count_pattern_matches(text: str, words_set: set) -> int:
    """Count occurrences of words from a set in text."""
    text_lower = text.lower()
    return sum(1 for word in text_lower.split() if word in words_set)


def count_questions(text: str) -> int:
    """Count question marks in text."""
    return text.count('?')
