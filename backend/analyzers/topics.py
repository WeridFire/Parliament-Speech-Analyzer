"""
Topic Analyzer - Extract and label cluster topics using TF-IDF

This module provides functions to extract meaningful topic labels
from clusters of political speeches.
"""

import logging
import re
import json
import hashlib
from collections import Counter
from typing import Optional
from pathlib import Path

import numpy as np
import pandas as pd

# Import stopwords from centralized config
from backend.config import STOP_WORDS

logger = logging.getLogger(__name__)

# Token cache configuration
TOKEN_CACHE_DIR = Path(__file__).parent.parent / '.cache'
TOKEN_CACHE_FILE = TOKEN_CACHE_DIR / 'tokens_cache.json'

# Lazy loading for spacy
_nlp = None
# In-memory token cache
_token_cache = None

def get_spacy_model():
    """Load Italian spacy model lazily."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            try:
                _nlp = spacy.load("it_core_news_sm")
                # Increase max_length to handle large combined speeches (default 1MB)
                _nlp.max_length = 50_000_000  # 50MB for combined texts
            except OSError:
                logger.warning("Spacy model 'it_core_news_sm' not found. Downloading...")
                from spacy.cli import download
                download("it_core_news_sm")
                _nlp = spacy.load("it_core_news_sm")
                _nlp.max_length = 50_000_000
            logger.info("Loaded Spacy model for POS tagging (max_length=50MB)")
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


def _get_token_cache() -> dict:
    """Load token cache from disk or initialize empty."""
    global _token_cache
    if _token_cache is not None:
        return _token_cache
    
    if TOKEN_CACHE_FILE.exists():
        try:
            with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
                _token_cache = json.load(f)
                logger.info("Loaded %d cached token entries", len(_token_cache))
                return _token_cache
        except Exception as e:
            logger.warning("Failed to load token cache: %s", e)
    
    _token_cache = {}
    return _token_cache


def _save_token_cache():
    """Save token cache to disk."""
    global _token_cache
    if _token_cache is None:
        return
    
    TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_token_cache, f)
        logger.info("Saved %d token cache entries", len(_token_cache))
    except Exception as e:
        logger.warning("Failed to save token cache: %s", e)


def _hash_texts(texts: list[str]) -> str:
    """Create a hash key for a list of texts."""
    combined = '|'.join(sorted(texts[:10]))  # Use first 10 for speed
    combined += f"|{len(texts)}"  # Include count for uniqueness
    return hashlib.md5(combined.encode()).hexdigest()[:16]


def tokenize_batch(texts: list[str], batch_size: int = 500, use_cache: bool = True) -> list[str]:
    """
    Tokenize a batch of texts efficiently using nlp.pipe() with caching.
    
    First run tokenizes and caches results. Subsequent runs load from cache.
    
    Args:
        texts: List of text strings to tokenize
        batch_size: Number of documents to process at once
        use_cache: Whether to use persistent cache
    
    Returns:
        List of all tokens from all texts combined
    """
    if not texts:
        return []
    
    # Check cache first
    if use_cache:
        cache = _get_token_cache()
        cache_key = _hash_texts(texts)
        if cache_key in cache:
            logger.debug("Cache hit for %d texts", len(texts))
            return cache[cache_key]
    
    nlp = get_spacy_model()
    all_tokens = []
    
    if nlp:
        # Use nlp.pipe() for efficient batch processing
        for doc in nlp.pipe(texts, batch_size=batch_size, disable=["parser", "ner"]):
            tokens = [
                token.text for token in doc
                if token.pos_ in ['NOUN', 'PROPN', 'ADJ']
                and not token.is_stop
                and len(token.text) > 2
            ]
            all_tokens.extend(tokens)
    else:
        # Fallback: simple tokenization
        stop_lower = {w.lower() for w in STOP_WORDS}
        for text in texts:
            text = text.lower()
            text = re.sub(r'[^\w\s]', ' ', text)
            tokens = [t for t in text.split() if len(t) > 2 and t not in stop_lower]
            all_tokens.extend(tokens)
    
    # Save to cache
    if use_cache:
        cache[cache_key] = all_tokens
        _save_token_cache()
    
    return all_tokens


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
    top_n: int = 5,
    max_docs_per_cluster: int = 500
) -> dict[int, list[str]]:
    """
    Extract top keywords for each cluster using TF-IDF.
    
    Uses individual document tokenization instead of combining into one large text.
    This approach:
    - Avoids memory issues with large text sizes
    - Produces better quality keywords
    - Scales to any dataset size
    
    Args:
        df: DataFrame with text and cluster columns
        text_col: Name of the text column
        cluster_col: Name of the cluster column
        top_n: Number of top keywords to extract
        max_docs_per_cluster: Max documents to sample per cluster (for performance)
    
    Returns:
        Dict mapping cluster_id -> list of top keywords
    """
    from collections import Counter
    import random
    
    cluster_topics = {}
    
    # Pre-tokenize all documents in batches (MUCH faster than individual calls)
    logger.info("Tokenizing documents in batches for TF-IDF...")
    
    for cluster_id in df[cluster_col].unique():
        cluster_texts = df[df[cluster_col] == cluster_id][text_col].tolist()
        
        if not cluster_texts:
            cluster_topics[cluster_id] = []
            continue
        
        # Sample if too many documents (for performance)
        if len(cluster_texts) > max_docs_per_cluster:
            cluster_texts = random.sample(cluster_texts, max_docs_per_cluster)
        
        # Batch tokenize cluster texts using nlp.pipe() - MUCH faster!
        cluster_tokens = Counter()
        cluster_tokens.update(tokenize_batch(cluster_texts))
        
        # Sample other texts for comparison
        other_texts = df[df[cluster_col] != cluster_id][text_col].tolist()
        if len(other_texts) > max_docs_per_cluster:
            other_texts = random.sample(other_texts, max_docs_per_cluster)
        
        other_tokens = Counter()
        other_tokens.update(tokenize_batch(other_texts))
        
        # Compute distinctive score: high in cluster, low in others
        distinctive = {}
        total_cluster = sum(cluster_tokens.values()) or 1
        total_other = sum(other_tokens.values()) or 1
        
        for word, count in cluster_tokens.items():
            # Normalized frequency in cluster
            cluster_freq = count / total_cluster
            # Normalized frequency in other clusters
            other_freq = other_tokens.get(word, 0) / total_other
            # Distinctiveness: how much more common in this cluster
            distinctive[word] = cluster_freq - other_freq * 0.5
        
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
