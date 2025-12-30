"""
Rhetoric Patterns - Populist, anti-establishment, emotional markers.
"""
import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)

# Rhetorical pattern keywords (Italian)
POPULIST_MARKERS = {
    'élite', 'elite', 'casta', 'popolo', 'gente', 'cittadini', 'traditi',
    'sistema', 'establishment', 'palazzo', 'potere', 'potenti', 'oligarchia',
    'banche', 'banchieri', 'lobby', 'burocrati', 'tecnocrati', 'privilegiati'
}

ANTI_ESTABLISHMENT_MARKERS = {
    'vergogna', 'scandalo', 'corruzione', 'corrotti', 'ladri', 'rubato',
    'fallimento', 'fallito', 'disastro', 'disastroso', 'inaccettabile',
    'intollerabile', 'responsabili', 'colpevoli', 'immorale', 'indegno'
}

EMOTIONAL_INTENSIFIERS = {
    'assolutamente', 'completamente', 'totalmente', 'incredibile', 'incredibilmente',
    'gravissimo', 'gravissima', 'urgente', 'urgentissimo', 'drammatico',
    'drammaticamente', 'straordinario', 'eccezionale', 'storico', 'epocale',
    'fondamentale', 'cruciale', 'vitale', 'essenziale', 'indispensabile'
}

INSTITUTIONAL_MARKERS = {
    'proposta', 'emendamento', 'normativa', 'legislazione', 'procedura',
    'regolamento', 'commissione', 'relazione', 'parere', 'valutazione',
    'analisi', 'studio', 'dati', 'statistiche', 'documento', 'articolo',
    'comma', 'decreto', 'disposizione', 'provvedimento', 'iter'
}


def _tokenize_simple(text: str) -> list[str]:
    """Simple tokenization for rhetoric analysis."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.split()


def _count_markers(tokens: list[str], markers: set[str]) -> int:
    """Count how many marker words appear in tokens."""
    return sum(1 for t in tokens if t in markers)


def compute_rhetoric_scores(text: str) -> dict[str, float]:
    """
    Compute rhetoric style scores for a single text.
    
    Returns:
        - populist: 0-1 score
        - anti_establishment: 0-1 score
        - emotional: 0-1 score
        - institutional: 0-1 score
    """
    tokens = _tokenize_simple(text)
    n_tokens = len(tokens) if tokens else 1
    
    return {
        'populist': _count_markers(tokens, POPULIST_MARKERS) / n_tokens * 100,
        'anti_establishment': _count_markers(tokens, ANTI_ESTABLISHMENT_MARKERS) / n_tokens * 100,
        'emotional': _count_markers(tokens, EMOTIONAL_INTENSIFIERS) / n_tokens * 100,
        'institutional': _count_markers(tokens, INSTITUTIONAL_MARKERS) / n_tokens * 100,
    }


def add_rhetoric_scores(df: pd.DataFrame, text_col: str = 'cleaned_text') -> pd.DataFrame:
    """Add rhetoric score columns to DataFrame."""
    scores = df[text_col].apply(compute_rhetoric_scores)
    
    df = df.copy()
    df['populist'] = scores.apply(lambda x: x['populist'])
    df['anti_establishment'] = scores.apply(lambda x: x['anti_establishment'])
    df['emotional'] = scores.apply(lambda x: x['emotional'])
    df['institutional'] = scores.apply(lambda x: x['institutional'])
    
    return df


def classify_rhetorical_style(row: pd.Series) -> str:
    """Classify a speech into a rhetorical category."""
    scores = {
        'populist': row.get('populist', 0),
        'anti_establishment': row.get('anti_establishment', 0),
        'emotional': row.get('emotional', 0),
        'institutional': row.get('institutional', 0)
    }
    
    max_score = max(scores.values())
    if max_score < 0.2:
        return 'neutrale'
    
    return max(scores, key=scores.get)
