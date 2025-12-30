"""
Topic Sentiment - Aspect-based sentiment analysis per topic cluster.
"""

import logging
from collections import defaultdict

import pandas as pd

from backend.config import POSITIVE_SENTIMENT_KEYWORDS, NEGATIVE_SENTIMENT_KEYWORDS
from .utils import tokenize_simple, count_keywords

logger = logging.getLogger(__name__)


def compute_topic_sentiment(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    cluster_col: str = 'cluster',
    cluster_labels: dict = None,
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Compute aspect-based sentiment analysis per topic cluster.
    
    For each speaker and each topic, measures whether they speak
    positively or negatively about that topic.
    
    Args:
        df: DataFrame with speeches
        text_col: Column with cleaned text
        cluster_col: Column with cluster assignments
        cluster_labels: Dict mapping cluster_id -> label
        speaker_col: Column with speaker names
        party_col: Column with party names
    
    Returns:
        {
            'by_speaker': {speaker: {cluster_id: {sentiment_score, classification}, ...}, ...},
            'by_party': {party: {cluster_id: {sentiment_score, classification}, ...}, ...},
            'by_cluster': {cluster_id: {avg_sentiment, positive_pct, negative_pct}, ...}
        }
    """
    positive_words = {w.lower() for w in POSITIVE_SENTIMENT_KEYWORDS}
    negative_words = {w.lower() for w in NEGATIVE_SENTIMENT_KEYWORDS}
    
    result = {
        'by_speaker': defaultdict(dict),
        'by_party': defaultdict(dict),
        'by_cluster': {}
    }
    
    labels = cluster_labels or {}
    
    # Compute per-speech sentiment first
    sentiments = []
    for _, row in df.iterrows():
        text = str(row[text_col]).lower()
        tokens = tokenize_simple(text)
        
        pos_count = count_keywords(tokens, positive_words)
        neg_count = count_keywords(tokens, negative_words)
        total = pos_count + neg_count
        
        if total > 0:
            sentiment = (pos_count - neg_count) / total
        else:
            sentiment = 0
        
        sentiments.append({
            'speaker': row[speaker_col],
            'party': row[party_col],
            'cluster': int(row[cluster_col]),
            'sentiment': sentiment,
            'pos_count': pos_count,
            'neg_count': neg_count
        })
    
    sentiment_df = pd.DataFrame(sentiments)
    
    # Aggregate by speaker and cluster
    for speaker in df[speaker_col].unique():
        speaker_data = sentiment_df[sentiment_df['speaker'] == speaker]
        
        for cluster in speaker_data['cluster'].unique():
            cluster_data = speaker_data[speaker_data['cluster'] == cluster]
            avg_sentiment = cluster_data['sentiment'].mean()
            
            classification = _classify_sentiment(avg_sentiment)
            
            result['by_speaker'][speaker][cluster] = {
                'sentiment_score': round(avg_sentiment, 3),
                'classification': classification,
                'n_speeches': len(cluster_data),
                'cluster_label': labels.get(cluster, f"Cluster {cluster}")
            }
    
    # Aggregate by party and cluster
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
            
        party_data = sentiment_df[sentiment_df['party'] == party]
        
        for cluster in party_data['cluster'].unique():
            cluster_data = party_data[party_data['cluster'] == cluster]
            avg_sentiment = cluster_data['sentiment'].mean()
            
            classification = _classify_sentiment(avg_sentiment)
            
            result['by_party'][party][cluster] = {
                'sentiment_score': round(avg_sentiment, 3),
                'classification': classification,
                'n_speeches': len(cluster_data),
                'cluster_label': labels.get(cluster, f"Cluster {cluster}")
            }
    
    # Aggregate by cluster (global)
    for cluster in df[cluster_col].unique():
        cluster_data = sentiment_df[sentiment_df['cluster'] == cluster]
        avg_sentiment = cluster_data['sentiment'].mean()
        
        positive_count = len(cluster_data[cluster_data['sentiment'] > 0.1])
        negative_count = len(cluster_data[cluster_data['sentiment'] < -0.1])
        total = len(cluster_data)
        
        result['by_cluster'][int(cluster)] = {
            'avg_sentiment': round(avg_sentiment, 3),
            'positive_pct': round((positive_count / total) * 100, 1) if total > 0 else 0,
            'negative_pct': round((negative_count / total) * 100, 1) if total > 0 else 0,
            'neutral_pct': round(((total - positive_count - negative_count) / total) * 100, 1) if total > 0 else 0,
            'label': labels.get(int(cluster), f"Cluster {cluster}")
        }
    
    # Convert defaultdicts
    result['by_speaker'] = dict(result['by_speaker'])
    result['by_party'] = dict(result['by_party'])
    
    logger.info(
        "Computed topic sentiment for %d speakers and %d parties",
        len(result['by_speaker']), len(result['by_party'])
    )
    
    return result


def _classify_sentiment(score: float) -> str:
    """Classify sentiment score into category."""
    if score > 0.1:
        return 'positivo'
    elif score < -0.1:
        return 'negativo'
    else:
        return 'neutro'
