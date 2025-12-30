"""
Named Entity Focus - Optional NER-based entity extraction.

Requires spaCy with Italian model (it_core_news_sm or larger).
"""
import logging
from collections import defaultdict

import pandas as pd

logger = logging.getLogger(__name__)

# Lazy loaded spaCy
_nlp = None
_spacy_available = None


def _get_spacy():
    """Lazy load spaCy Italian model."""
    global _nlp, _spacy_available
    
    if _spacy_available is not None:
        return _nlp if _spacy_available else None
    
    try:
        import spacy
        _nlp = spacy.load("it_core_news_sm")
        _spacy_available = True
        logger.info("Loaded spaCy Italian model for NER")
        return _nlp
    except (ImportError, OSError):
        _spacy_available = False
        logger.info("spaCy Italian model not available for NER")
        return None


def compute_entity_focus(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    text_col: str = 'cleaned_text'
) -> dict:
    """
    Compute named entity focus for each speaker.
    
    Requires spaCy Italian model.
    
    Returns:
    - top_persons: most mentioned people
    - top_orgs: most mentioned organizations
    - top_locations: most mentioned locations
    """
    nlp = _get_spacy()
    
    if nlp is None:
        return {'error': 'spaCy Italian model not available'}
    
    result = {}
    
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        
        if len(speaker_df) < 3:
            continue
        
        entity_counts = {
            'PER': defaultdict(int),
            'ORG': defaultdict(int),
            'LOC': defaultdict(int),
            'GPE': defaultdict(int),
        }
        
        # Process texts
        texts = speaker_df[text_col].tolist()
        
        for text in texts:
            # Limit text length for performance
            doc = nlp(str(text)[:10000])
            
            for ent in doc.ents:
                if ent.label_ in entity_counts:
                    entity_counts[ent.label_][ent.text.strip()] += 1
        
        # Combine LOC and GPE
        for name, count in entity_counts['GPE'].items():
            entity_counts['LOC'][name] += count
        
        # Get top entities
        top_persons = sorted(entity_counts['PER'].items(), key=lambda x: -x[1])[:10]
        top_orgs = sorted(entity_counts['ORG'].items(), key=lambda x: -x[1])[:10]
        top_locations = sorted(entity_counts['LOC'].items(), key=lambda x: -x[1])[:10]
        
        result[speaker] = {
            'top_persons': [{'name': n, 'count': c} for n, c in top_persons],
            'top_organizations': [{'name': n, 'count': c} for n, c in top_orgs],
            'top_locations': [{'name': n, 'count': c} for n, c in top_locations],
            'n_speeches': len(speaker_df)
        }
    
    logger.info("Computed entity focus for %d speakers", len(result))
    return result
