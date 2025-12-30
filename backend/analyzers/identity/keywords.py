"""
Distinctive Keywords - Extract TF-IDF keywords per party.

Tokenization utilities and TF-IDF computation for distinctive term extraction.
"""

import logging
import re
from collections import Counter
from typing import Optional

import numpy as np
import pandas as pd

from backend.config import STOP_WORDS

logger = logging.getLogger(__name__)

# Lazy-loaded spaCy model
_nlp = None
_spacy_available = False


# Additional low-quality words to filter
KEYWORD_BLACKLIST = {
    # Contractions and fragments
    'dell', 'all', 'nell', 'dall', 'sull', 'coll', 'quell', 'quest',
    'un', 'una', 'uno', 'ogni', 'alcun', 'qualch',
    # Generic words
    'cosa', 'cose', 'fatto', 'fatti', 'modo', 'modi', 'tipo', 'tipi',
    'volta', 'volte', 'parte', 'parti', 'punto', 'punti',
    'anno', 'anni', 'mese', 'mesi', 'giorno', 'giorni',
    'momento', 'tempo', 'tempi', 'periodo', 'periodi',
    'caso', 'casi', 'esempio', 'esempi', 'senso', 'sensi',
    'base', 'basi', 'livello', 'livelli', 'numero', 'numeri',
    # Generic verbs
    'fare', 'dire', 'andare', 'venire', 'vedere', 'sapere',
    'potere', 'volere', 'dovere', 'stare', 'dare', 'prendere',
    'mettere', 'trovare', 'portare', 'passare', 'lasciare',
    'parlare', 'pensare', 'credere', 'sentire', 'chiamare',
    # Generic adjectives
    'grande', 'grandi', 'piccolo', 'piccoli', 'nuovo', 'nuovi',
    'primo', 'primi', 'ultimo', 'ultimi', 'alto', 'alti',
    'basso', 'bassi', 'lungo', 'lunghi', 'vero', 'veri',
    'importante', 'importanti', 'necessario', 'necessari',
    'possibile', 'possibili', 'diverso', 'diversi',
    # Parliamentary common terms
    'proposta', 'proposte', 'richiesta', 'richieste',
    'situazione', 'situazioni', 'condizione', 'condizioni',
    'intervento', 'interventi', 'azione', 'azioni',
    'decisione', 'decisioni', 'scelta', 'scelte',
}

# POS tags to keep (nouns, proper nouns, verbs, adjectives)
ALLOWED_POS = {'NOUN', 'PROPN', 'VERB', 'ADJ'}


def _load_spacy():
    """Lazy load spaCy Italian model with only needed components."""
    global _nlp, _spacy_available
    
    if _nlp is not None:
        return _nlp
    
    try:
        import spacy
        try:
            # Only load tokenizer, tagger, and lemmatizer
            _nlp = spacy.load("it_core_news_sm", disable=["ner", "parser"])
            _nlp.max_length = 150000
            _spacy_available = True
            logger.info("Loaded spaCy Italian model for keyword extraction")
        except OSError:
            logger.warning("spaCy Italian model not found. Run: python -m spacy download it_core_news_sm")
            _spacy_available = False
    except ImportError:
        logger.warning("spaCy not installed. Using basic tokenization.")
        _spacy_available = False
    
    return _nlp


def tokenize_advanced(text: str) -> list[str]:
    """
    Advanced tokenization using spaCy for lemmatization and POS filtering.
    
    Returns only meaningful content words:
    - Lemmatized (base forms)
    - Only nouns, verbs, adjectives
    - Min 4 characters
    - Not in stopwords or blacklist
    """
    nlp = _load_spacy()
    
    if nlp is None or not _spacy_available:
        return tokenize_basic(text)
    
    # Process with spaCy (limit text length)
    doc = nlp(text[:100000])
    
    stop_lower = {w.lower() for w in STOP_WORDS}
    tokens = []
    
    for token in doc:
        if token.pos_ not in ALLOWED_POS:
            continue
        
        lemma = token.lemma_.lower()
        
        # Quality filters
        if len(lemma) < 4:
            continue
        if lemma in stop_lower:
            continue
        if lemma in KEYWORD_BLACKLIST:
            continue
        if not lemma.isalpha():
            continue
        # Skip verb conjugation patterns
        if lemma.endswith(('ando', 'endo', 'ato', 'ito', 'uto')) and len(lemma) < 7:
            continue
            
        tokens.append(lemma)
    
    return tokens


def tokenize_basic(text: str) -> list[str]:
    """Basic tokenization fallback: lowercase, remove punctuation, filter stopwords."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    stop_lower = {w.lower() for w in STOP_WORDS}
    
    result = []
    for t in tokens:
        if len(t) < 4:
            continue
        if t in stop_lower:
            continue
        if t in KEYWORD_BLACKLIST:
            continue
        if not t.isalpha():
            continue
        result.append(t)
    
    return result


def tokenize(text: str) -> list[str]:
    """Main tokenize function - uses advanced if available, basic otherwise."""
    return tokenize_advanced(text)


def compute_distinctive_keywords(
    df: pd.DataFrame,
    party_col: str = 'group',
    text_col: str = 'cleaned_text',
    top_n: int = 50
) -> dict:
    """
    Extract distinctive keywords for each party using TF-IDF.
    
    Treats each party's combined speeches as a single document,
    extracts terms that distinguish each party from others.
    
    Args:
        df: DataFrame with speeches
        party_col: Column with party names
        text_col: Column with cleaned text
        top_n: Number of top keywords to return per party
    
    Returns:
        {party: [keyword1, keyword2, ...], ...}
    """
    parties = [p for p in df[party_col].unique() if p != 'Unknown Group']
    
    if len(parties) < 2:
        logger.warning("Need at least 2 parties for distinctive keyword analysis")
        return {}
    
    # Create one document per party
    party_docs = {}
    for party in parties:
        party_texts = df[df[party_col] == party][text_col].tolist()
        party_docs[party] = ' '.join(party_texts)
    
    # Tokenize all party documents
    tokenized = {party: tokenize(doc) for party, doc in party_docs.items()}
    
    # Document frequency across parties
    df_counts = Counter()
    for party, tokens in tokenized.items():
        unique_tokens = set(tokens)
        for token in unique_tokens:
            df_counts[token] += 1
    
    n_docs = len(parties)
    
    # Compute TF-IDF per party
    result = {}
    for party, tokens in tokenized.items():
        tf = Counter(tokens)
        n_tokens = len(tokens) if tokens else 1
        
        tfidf_scores = {}
        for word, count in tf.items():
            tf_score = count / n_tokens
            idf = np.log(n_docs / (df_counts[word] + 1)) + 1
            tfidf_scores[word] = tf_score * idf
        
        # Sort and get top distinctive terms
        sorted_terms = sorted(tfidf_scores.items(), key=lambda x: -x[1])
        result[party] = [term for term, score in sorted_terms[:top_n]]
    
    logger.info("Extracted distinctive keywords for %d parties", len(result))
    
    return result
