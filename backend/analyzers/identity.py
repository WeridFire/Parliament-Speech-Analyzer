"""
Identity Analyzer - Analyze the political identity and DNA of politicians/parties.

This module provides:
- Thematic Fingerprint (radar chart data)
- Generalism Index (entropy-based monotematic vs generalist score)
- Distinctive Keywords (TF-IDF per party)
"""

import logging
import re
from collections import Counter
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from backend.config import STOP_WORDS

logger = logging.getLogger(__name__)

# Try to load spaCy for advanced NLP
_nlp = None
_spacy_available = False

def _load_spacy():
    """Lazy load spaCy Italian model with only needed components."""
    global _nlp, _spacy_available
    if _nlp is not None:
        return _nlp
    
    try:
        import spacy
        try:
            # Only load tokenizer, tagger, and lemmatizer - disable NER, parser etc.
            _nlp = spacy.load("it_core_news_sm", disable=["ner", "parser"])
            _nlp.max_length = 150000  # Increase max length for large texts
            _spacy_available = True
            logger.info("Loaded spaCy Italian model (optimized) for keyword extraction")
        except OSError:
            logger.warning("spaCy Italian model not found. Run: python -m spacy download it_core_news_sm")
            _spacy_available = False
    except ImportError:
        logger.warning("spaCy not installed. Using basic tokenization.")
        _spacy_available = False
    
    return _nlp


# Additional low-quality words to filter (contractions, fragments, common non-distinctive terms)
KEYWORD_BLACKLIST = {
    # Contrazioni e frammenti
    'dell', 'all', 'nell', 'dall', 'sull', 'coll', 'quell', 'quest',
    'un', 'una', 'uno', 'ogni', 'alcun', 'qualch',
    # Parole troppo generiche
    'cosa', 'cose', 'fatto', 'fatti', 'modo', 'modi', 'tipo', 'tipi',
    'volta', 'volte', 'parte', 'parti', 'punto', 'punti',
    'anno', 'anni', 'mese', 'mesi', 'giorno', 'giorni',
    'momento', 'tempo', 'tempi', 'periodo', 'periodi',
    'caso', 'casi', 'esempio', 'esempi', 'senso', 'sensi',
    'base', 'basi', 'livello', 'livelli', 'numero', 'numeri',
    # Verbi generici nelle loro forme
    'fare', 'dire', 'andare', 'venire', 'vedere', 'sapere',
    'potere', 'volere', 'dovere', 'stare', 'dare', 'prendere',
    'mettere', 'trovare', 'portare', 'passare', 'lasciare',
    'parlare', 'pensare', 'credere', 'sentire', 'chiamare',
    # Aggettivi troppo comuni
    'grande', 'grandi', 'piccolo', 'piccoli', 'nuovo', 'nuovi',
    'primo', 'primi', 'ultimo', 'ultimi', 'alto', 'alti',
    'basso', 'bassi', 'lungo', 'lunghi', 'vero', 'veri',
    'importante', 'importanti', 'necessario', 'necessari',
    'possibile', 'possibili', 'diverso', 'diversi',
    # Parlamentari aggiuntivi
    'proposta', 'proposte', 'richiesta', 'richieste',
    'situazione', 'situazioni', 'condizione', 'condizioni',
    'intervento', 'interventi', 'azione', 'azioni',
    'decisione', 'decisioni', 'scelta', 'scelte',
}

# POS tags to keep (nouns, proper nouns, verbs, adjectives)
ALLOWED_POS = {'NOUN', 'PROPN', 'VERB', 'ADJ'}


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
        # Fallback to basic tokenization
        return tokenize_basic(text)
    
    # Process with spaCy (limit text length for performance)
    doc = nlp(text[:100000])
    
    stop_lower = {w.lower() for w in STOP_WORDS}
    tokens = []
    
    for token in doc:
        # Skip if not content word
        if token.pos_ not in ALLOWED_POS:
            continue
        
        # Use lemma (base form)
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
        # Skip words that look like verb conjugations patterns
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
        if len(t) < 4:  # Increased from 3 to 4
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


def compute_thematic_fingerprint(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_centroids: np.ndarray,
    cluster_labels: dict,
    group_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Compute thematic fingerprint (radar chart data) for each politician/party.
    
    Calculates mean cosine similarity between speaker's embeddings and each cluster centroid.
    
    Args:
        df: DataFrame with speeches
        embeddings: Speech embeddings array
        cluster_centroids: Array of cluster centroid vectors (n_clusters x embedding_dim)
        cluster_labels: Dict mapping cluster_id -> label string
        group_col: Column to group by ('deputy' or 'group')
        party_col: Column containing party info
    
    Returns:
        Dict with fingerprints per speaker/party:
        {
            'by_deputy': {deputy: {cluster_id: similarity, ...}, ...},
            'by_party': {party: {cluster_id: similarity, ...}, ...}
        }
    """
    result = {
        'by_deputy': {},
        'by_party': {},
        'cluster_labels': cluster_labels
    }
    
    n_clusters = len(cluster_centroids)
    
    # Per-deputy fingerprint
    for deputy in df['deputy'].unique():
        mask = df['deputy'] == deputy
        if mask.sum() == 0:
            continue
            
        deputy_embeddings = embeddings[mask]
        avg_embedding = np.mean(deputy_embeddings, axis=0).reshape(1, -1)
        
        # Similarity to each cluster centroid
        similarities = cosine_similarity(avg_embedding, cluster_centroids)[0]
        
        result['by_deputy'][deputy] = {
            int(i): round(float(similarities[i]), 4)
            for i in range(n_clusters)
        }
    
    # Per-party fingerprint
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
            
        mask = df[party_col] == party
        if mask.sum() == 0:
            continue
            
        party_embeddings = embeddings[mask]
        avg_embedding = np.mean(party_embeddings, axis=0).reshape(1, -1)
        
        similarities = cosine_similarity(avg_embedding, cluster_centroids)[0]
        
        result['by_party'][party] = {
            int(i): round(float(similarities[i]), 4)
            for i in range(n_clusters)
        }
    
    logger.info("Computed thematic fingerprints for %d deputies and %d parties", 
                len(result['by_deputy']), len(result['by_party']))
    
    return result


def compute_generalism_index(
    df: pd.DataFrame,
    cluster_col: str = 'cluster',
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Compute generalism index based on topic entropy.
    
    Shannon entropy of topic distribution, normalized to 0-100:
    - 100 = perfectly generalist (equal distribution across all topics)
    - 0 = monotematic (speaks only about one topic)
    
    Returns:
        {
            'by_deputy': {deputy: {score, dominant_topic, n_topics}, ...},
            'by_party': {party: {score, dominant_topic, n_topics}, ...}
        }
    """
    result = {
        'by_deputy': {},
        'by_party': {}
    }
    
    n_clusters = df[cluster_col].nunique()
    max_entropy = np.log2(n_clusters) if n_clusters > 1 else 1
    
    # Per-deputy
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        if len(speaker_df) < 2:
            continue
            
        topic_counts = speaker_df[cluster_col].value_counts()
        proportions = topic_counts.values / topic_counts.sum()
        
        # Shannon entropy
        entropy = -np.sum(proportions * np.log2(proportions + 1e-10))
        normalized_score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        
        dominant_topic = int(topic_counts.idxmax())
        n_topics_used = len(topic_counts)
        
        result['by_deputy'][speaker] = {
            'score': round(float(normalized_score), 1),
            'dominant_topic': dominant_topic,
            'n_topics': n_topics_used,
            'n_speeches': len(speaker_df),
            'classification': 'generalista' if normalized_score > 70 else ('specialista' if normalized_score < 30 else 'bilanciato')
        }
    
    # Per-party
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
            
        party_df = df[df[party_col] == party]
        if len(party_df) < 2:
            continue
            
        topic_counts = party_df[cluster_col].value_counts()
        proportions = topic_counts.values / topic_counts.sum()
        
        entropy = -np.sum(proportions * np.log2(proportions + 1e-10))
        normalized_score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        
        dominant_topic = int(topic_counts.idxmax())
        
        result['by_party'][party] = {
            'score': round(float(normalized_score), 1),
            'dominant_topic': dominant_topic,
            'n_topics': len(topic_counts),
            'n_speeches': len(party_df),
            'classification': 'generalista' if normalized_score > 70 else ('specialista' if normalized_score < 30 else 'bilanciato')
        }
    
    logger.info("Computed generalism index for %d deputies and %d parties",
                len(result['by_deputy']), len(result['by_party']))
    
    return result


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
            # TF: normalized term frequency
            tf_score = count / n_tokens
            # IDF: inverse document frequency
            idf = np.log(n_docs / (df_counts[word] + 1)) + 1
            tfidf_scores[word] = tf_score * idf
        
        # Sort and get top distinctive terms
        sorted_terms = sorted(tfidf_scores.items(), key=lambda x: -x[1])
        result[party] = [term for term, score in sorted_terms[:top_n]]
    
    logger.info("Extracted distinctive keywords for %d parties", len(result))
    
    return result
