"""
Sentiment Rankings - Party-Topic matrix and speaker rankings.
"""

import logging
from collections import defaultdict

import pandas as pd

from backend.config import POSITIVE_SENTIMENT_KEYWORDS, NEGATIVE_SENTIMENT_KEYWORDS
from .utils import tokenize_simple, count_keywords

logger = logging.getLogger(__name__)


def compute_party_topic_sentiment(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    cluster_col: str = 'cluster',
    cluster_labels: dict = None,
    party_col: str = 'group'
) -> dict:
    """
    Compute sentiment matrix: Party × Topic.
    
    Returns a matrix suitable for heatmap visualization.
    
    Args:
        df: DataFrame with speeches
        text_col: Column with cleaned text
        cluster_col: Column with cluster assignments
        cluster_labels: Dict mapping cluster_id -> label
        party_col: Column with party names
    
    Returns:
        {
            'parties': [party1, party2, ...],
            'topics': [topic1, topic2, ...],
            'matrix': [[score, score, ...], ...]  # parties × topics
        }
    """
    positive_words = {w.lower() for w in POSITIVE_SENTIMENT_KEYWORDS}
    negative_words = {w.lower() for w in NEGATIVE_SENTIMENT_KEYWORDS}
    labels = cluster_labels or {}
    
    parties = sorted([p for p in df[party_col].unique() if p != 'Unknown Group'])
    clusters = sorted(df[cluster_col].unique())
    
    # Compute sentiment per party-topic pair
    matrix = []
    for party in parties:
        row = []
        for cluster in clusters:
            mask = (df[party_col] == party) & (df[cluster_col] == cluster)
            party_cluster_df = df[mask]
            
            if len(party_cluster_df) == 0:
                row.append(0)
                continue
            
            sentiments = []
            for _, speech in party_cluster_df.iterrows():
                text = str(speech[text_col]).lower()
                tokens = tokenize_simple(text)
                pos = count_keywords(tokens, positive_words)
                neg = count_keywords(tokens, negative_words)
                total = pos + neg
                sentiment = (pos - neg) / total if total > 0 else 0
                sentiments.append(sentiment)
            
            avg = sum(sentiments) / len(sentiments) if sentiments else 0
            row.append(round(avg, 3))
        matrix.append(row)
    
    topic_labels = [labels.get(c, f"Topic {c}") for c in clusters]
    
    logger.info(
        "Computed party-topic sentiment matrix: %d parties × %d topics",
        len(parties), len(clusters)
    )
    
    return {
        'parties': parties,
        'topics': topic_labels,
        'topic_ids': [int(c) for c in clusters],
        'matrix': matrix
    }


def compute_sentiment_rankings(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    cluster_col: str = 'cluster',
    cluster_labels: dict = None,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
    top_n: int = 10
) -> dict:
    """
    Compute most positive and most negative speakers per topic.
    
    Args:
        df: DataFrame with speeches
        text_col: Column with cleaned text
        cluster_col: Column with cluster assignments
        cluster_labels: Dict mapping cluster_id -> label
        speaker_col: Column with speaker names
        party_col: Column with party names
        top_n: Number of speakers to include in each ranking
    
    Returns:
        {
            topic_id: {
                'label': str,
                'most_positive': [{speaker, party, score, n_speeches}, ...],
                'most_negative': [{speaker, party, score, n_speeches}, ...]
            }
        }
    """
    positive_words = {w.lower() for w in POSITIVE_SENTIMENT_KEYWORDS}
    negative_words = {w.lower() for w in NEGATIVE_SENTIMENT_KEYWORDS}
    labels = cluster_labels or {}
    
    result = {}
    
    for cluster in df[cluster_col].unique():
        cluster_df = df[df[cluster_col] == cluster]
        speaker_sentiments = defaultdict(list)
        speaker_parties = {}
        
        for _, speech in cluster_df.iterrows():
            speaker = speech[speaker_col]
            party = speech[party_col]
            text = str(speech[text_col]).lower()
            tokens = tokenize_simple(text)
            pos = count_keywords(tokens, positive_words)
            neg = count_keywords(tokens, negative_words)
            total = pos + neg
            sentiment = (pos - neg) / total if total > 0 else 0
            
            speaker_sentiments[speaker].append(sentiment)
            speaker_parties[speaker] = party
        
        # Compute averages
        speaker_scores = []
        for speaker, sentiments in speaker_sentiments.items():
            avg = sum(sentiments) / len(sentiments)
            speaker_scores.append({
                'speaker': speaker,
                'party': speaker_parties[speaker],
                'score': round(avg, 3),
                'n_speeches': len(sentiments)
            })
        
        # Sort and pick top/bottom
        speaker_scores.sort(key=lambda x: -x['score'])
        
        result[int(cluster)] = {
            'label': labels.get(int(cluster), f"Topic {cluster}"),
            'most_positive': speaker_scores[:top_n],
            'most_negative': speaker_scores[-top_n:][::-1]
        }
    
    logger.info("Computed sentiment rankings for %d topics", len(result))
    
    return result
