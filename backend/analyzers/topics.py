"""
Topic Analyzer - Extract and label cluster topics using TF-IDF

This module provides functions to extract meaningful topic labels
from clusters of political speeches.
"""

import logging
import re
from collections import Counter
from typing import Optional

import numpy as np
import pandas as pd

# Import stopwords from centralized config
from backend.config import STOP_WORDS

logger = logging.getLogger(__name__)

# Lazy loading for spacy
_nlp = None

def get_spacy_model():
    """Load Italian spacy model lazily."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            try:
                _nlp = spacy.load("it_core_news_sm")
            except OSError:
                logger.warning("Spacy model 'it_core_news_sm' not found. Downloading...")
                from spacy.cli import download
                download("it_core_news_sm")
                _nlp = spacy.load("it_core_news_sm")
            logger.info("Loaded Spacy model for POS tagging")
        except ImportError:
            logger.warning("Spacy not installed. Using simple tokenization.")
            _nlp = False
        except Exception as e:
            logger.warning("Failed to load Spacy: %s", e)
            _nlp = False
    return _nlp

def tokenize(text: str, use_pos: bool = True) -> list[str]:
    """
    Tokenize text using Spacy POS tagging (if available) or fallback.
    
    Args:
        text: Input text
        use_pos: If True, keep only Nouns/Adjectives using Spacy
    """
    nlp = get_spacy_model()
    
    # Advanced Tokenization (keep meaningful words only)
    if use_pos and nlp:
        doc = nlp(text.lower())
        # Keep Nouns (NOUN), Proper Nouns (PROPN), Adjectives (ADJ)
        # Filter out stopwords and short words
        tokens = [
            token.text for token in doc 
            if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] 
            and not token.is_stop 
            and len(token.text) > 2
        ]
        return tokens

    # Fallback: Simple tokenization
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    # Convert STOP_WORDS to lowercase for comparison
    stop_lower = {w.lower() for w in STOP_WORDS}
    return [t for t in tokens if len(t) > 2 and t not in stop_lower]


def compute_tfidf(documents: list[str]) -> tuple[dict, list[dict]]:
    """
    Compute TF-IDF scores for a collection of documents.
    
    Returns:
        vocab: dict mapping word to document frequency
        tfidf_docs: list of dicts with word->tfidf score per document
    """
    # Tokenize all documents (try using POS tagging)
    logger.info("Tokenizing %d documents (POS tagging enabled if available)...", len(documents))
    tokenized = [tokenize(doc) for doc in documents]
    
    # Document frequency
    df = Counter()
    for tokens in tokenized:
        unique_tokens = set(tokens)
        for token in unique_tokens:
            df[token] += 1
    
    n_docs = len(documents)
    
    # Compute TF-IDF per document
    tfidf_docs = []
    for tokens in tokenized:
        tf = Counter(tokens)
        tfidf = {}
        for word, count in tf.items():
            idf = np.log(n_docs / (df[word] + 1)) + 1
            tfidf[word] = count * idf
        tfidf_docs.append(tfidf)
    
    return df, tfidf_docs


def extract_cluster_topics(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    cluster_col: str = 'cluster',
    top_n: int = 5
) -> dict[int, list[str]]:
    """
    Extract top keywords for each cluster using TF-IDF.
    
    Args:
        df: DataFrame with text and cluster columns
        text_col: Name of the text column
        cluster_col: Name of the cluster column
        top_n: Number of top keywords to extract
    
    Returns:
        Dict mapping cluster_id -> list of top keywords
    """
    cluster_topics = {}
    
    for cluster_id in df[cluster_col].unique():
        cluster_texts = df[df[cluster_col] == cluster_id][text_col].tolist()
        
        if not cluster_texts:
            cluster_topics[cluster_id] = []
            continue
        
        # Combine all texts in cluster as one document
        combined = ' '.join(cluster_texts)
        
        # Get all other texts
        other_texts = df[df[cluster_col] != cluster_id][text_col].tolist()
        other_combined = ' '.join(other_texts) if other_texts else ""
        
        # Compute TF-IDF comparing cluster vs rest
        _, tfidf = compute_tfidf([combined, other_combined])
        
        cluster_tfidf = tfidf[0]
        other_tfidf = tfidf[1] if len(tfidf) > 1 else {}
        
        # Get words that are distinctive to this cluster
        distinctive = {}
        for word, score in cluster_tfidf.items():
            other_score = other_tfidf.get(word, 0)
            # Higher score means more distinctive to this cluster
            distinctive[word] = score - other_score * 0.5
        
        # Sort and get top keywords
        sorted_words = sorted(distinctive.items(), key=lambda x: -x[1])
        cluster_topics[cluster_id] = [w for w, _ in sorted_words[:top_n]]
    
    return cluster_topics


def label_cluster(keywords: list[str]) -> str:
    """Generate a human-readable label from keywords."""
    if not keywords:
        return "Vario"
    
    # Capitalize first word, join with &
    if len(keywords) >= 2:
        return f"{keywords[0].capitalize()} & {keywords[1].capitalize()}"
    return keywords[0].capitalize()


def get_cluster_labels(df: pd.DataFrame) -> dict[int, str]:
    """
    Get human-readable labels for all clusters.
    
    Returns dict mapping cluster_id -> label string
    """
    topics = extract_cluster_topics(df)
    return {cid: label_cluster(keywords) for cid, keywords in topics.items()}
