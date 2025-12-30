"""
Topic Extraction - TF-IDF keyword extraction from clusters.
"""
import logging
import re
from collections import Counter
from typing import Optional

import numpy as np
import pandas as pd

from backend.config import STOP_WORDS

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
        _nlp = spacy.load("it_core_news_sm", disable=["ner", "parser"])
        _nlp.max_length = 150000
        _spacy_available = True
        logger.info("Loaded spaCy Italian model for POS tagging")
        return _nlp
    except (ImportError, OSError):
        _spacy_available = False
        logger.info("spaCy Italian model not available, using basic tokenization")
        return None


def tokenize(text: str, use_pos: bool = True) -> list[str]:
    """
    Tokenize text, optionally using POS filtering.
    
    Args:
        text: Input text
        use_pos: If True, keep only Nouns/Adjectives
    """
    nlp = _get_spacy()
    stop_lower = {w.lower() for w in STOP_WORDS}
    
    if nlp is None or not use_pos:
        # Basic tokenization
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if len(t) >= 4 and t not in stop_lower and t.isalpha()]
    
    # POS-filtered tokenization
    doc = nlp(text[:50000])
    tokens = []
    
    for token in doc:
        if token.pos_ not in ('NOUN', 'ADJ', 'PROPN'):
            continue
        
        lemma = token.lemma_.lower()
        
        if len(lemma) < 4:
            continue
        if lemma in stop_lower:
            continue
        if not lemma.isalpha():
            continue
        
        tokens.append(lemma)
    
    return tokens


def tokenize_batch(texts: list[str], batch_size: int = 500, use_pos: bool = True) -> list[str]:
    """Tokenize a batch of texts efficiently."""
    nlp = _get_spacy()
    
    if nlp is None or not use_pos:
        all_tokens = []
        for text in texts:
            all_tokens.extend(tokenize(text, use_pos=False))
        return all_tokens
    
    stop_lower = {w.lower() for w in STOP_WORDS}
    all_tokens = []
    
    # Truncate texts to avoid Spacy max_length limits (e.g., 100k chars)
    # This is safe for keyword extraction as we only need a sample of terms
    safe_texts = [t[:100000] for t in texts]
    
    for doc in nlp.pipe(safe_texts, batch_size=batch_size):
        for token in doc:
            if token.pos_ not in ('NOUN', 'ADJ', 'PROPN'):
                continue
            lemma = token.lemma_.lower()
            if len(lemma) >= 4 and lemma not in stop_lower and lemma.isalpha():
                all_tokens.append(lemma)
    
    return all_tokens


def extract_cluster_topics(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    cluster_col: str = 'cluster',
    top_n: int = 5,
    max_docs_per_cluster: int = 500
) -> dict:
    """
    Extract top keywords for each cluster using TF-IDF.
    
    Returns:
        Dict mapping cluster_id -> list of top keywords
    """
    clusters = df[cluster_col].unique()
    
    # Tokenize all texts per cluster
    cluster_tokens = {}
    for cluster in clusters:
        cluster_df = df[df[cluster_col] == cluster]
        
        # Limit documents for performance
        if len(cluster_df) > max_docs_per_cluster:
            cluster_df = cluster_df.sample(max_docs_per_cluster, random_state=42)
        
        texts = cluster_df[text_col].tolist()
        cluster_tokens[cluster] = tokenize_batch(texts)
    
    # Compute document frequency
    df_counts = Counter()
    for cluster, tokens in cluster_tokens.items():
        unique_tokens = set(tokens)
        for token in unique_tokens:
            df_counts[token] += 1
    
    n_clusters = len(clusters)
    
    # Compute TF-IDF per cluster
    result = {}
    for cluster, tokens in cluster_tokens.items():
        tf = Counter(tokens)
        n_tokens = len(tokens) if tokens else 1
        
        tfidf_scores = {}
        for word, count in tf.items():
            tf_score = count / n_tokens
            idf = np.log(n_clusters / (df_counts[word] + 1)) + 1
            tfidf_scores[word] = tf_score * idf
        
        # Get top keywords
        sorted_terms = sorted(tfidf_scores.items(), key=lambda x: -x[1])
        result[int(cluster)] = [term for term, score in sorted_terms[:top_n]]
    
    logger.info("Extracted topics for %d clusters", len(result))
    return result
