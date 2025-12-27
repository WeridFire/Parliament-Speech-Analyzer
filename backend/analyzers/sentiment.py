"""
Sentiment Analyzer - Qualitative analysis of political communication.

This module provides:
- Topic Sentiment (aspect-based sentiment per cluster)
- Gulpease Readability Score (complexity index)
- Polarization Score ("Us vs Them" analysis)
"""

import logging
import re
from collections import defaultdict
from typing import Optional

import numpy as np
import pandas as pd

from backend.config import (
    POSITIVE_SENTIMENT_KEYWORDS,
    NEGATIVE_SENTIMENT_KEYWORDS,
    POLARIZATION_PRONOUNS,
    ADVERSATIVE_TERMS,
    US_THEM_PATTERNS,
    STOP_WORDS
)

logger = logging.getLogger(__name__)


def tokenize_simple(text: str) -> list[str]:
    """Simple tokenization for sentiment analysis."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.split()


def count_keywords(tokens: list[str], keywords: set) -> int:
    """Count how many keyword occurrences appear in tokens."""
    keywords_lower = {k.lower() for k in keywords}
    return sum(1 for t in tokens if t in keywords_lower)


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
    
    Returns:
        {
            'by_speaker': {
                speaker: {
                    cluster_id: {'sentiment_score': -1 to 1, 'classification': str},
                    ...
                },
                ...
            },
            'by_party': {
                party: {
                    cluster_id: {'sentiment_score': -1 to 1, 'classification': str},
                    ...
                },
                ...
            },
            'by_cluster': {
                cluster_id: {
                    'avg_sentiment': float,
                    'positive_pct': float,
                    'negative_pct': float
                },
                ...
            }
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
        
        # Sentiment score: -1 (negative) to +1 (positive)
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
            
            classification = 'positivo' if avg_sentiment > 0.1 else ('negativo' if avg_sentiment < -0.1 else 'neutro')
            
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
            
            classification = 'positivo' if avg_sentiment > 0.1 else ('negativo' if avg_sentiment < -0.1 else 'neutro')
            
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
    
    logger.info("Computed topic sentiment for %d speakers and %d parties",
                len(result['by_speaker']), len(result['by_party']))
    
    return result


def compute_gulpease_score(text: str) -> dict:
    """
    Compute Gulpease readability index for Italian text.
    
    Formula: 89 + (300 * sentences - 10 * letters) / words
    
    Score interpretation:
    - < 55: Difficult (university level)
    - 55-80: Medium (high school level)
    - > 80: Easy (elementary level)
    
    Returns:
        {
            'score': float,
            'classification': 'difficile' | 'medio' | 'facile',
            'n_words': int,
            'n_sentences': int,
            'n_letters': int
        }
    """
    # Clean text
    text = str(text).strip()
    
    if not text:
        return {'score': 0, 'classification': 'n/a', 'n_words': 0, 'n_sentences': 0, 'n_letters': 0}
    
    # Count words
    words = re.findall(r'\b\w+\b', text)
    n_words = len(words)
    
    if n_words == 0:
        return {'score': 0, 'classification': 'n/a', 'n_words': 0, 'n_sentences': 0, 'n_letters': 0}
    
    # Count sentences (approximate by punctuation)
    sentences = re.split(r'[.!?]+', text)
    n_sentences = len([s for s in sentences if s.strip()])
    n_sentences = max(n_sentences, 1)  # At least one sentence
    
    # Count letters (only alphabetic characters)
    n_letters = sum(1 for c in text if c.isalpha())
    
    # Gulpease formula
    score = 89 + (300 * n_sentences - 10 * n_letters) / n_words
    
    # Clamp to 0-100
    score = max(0, min(100, score))
    
    # Classification
    if score < 55:
        classification = 'difficile'
    elif score < 80:
        classification = 'medio'
    else:
        classification = 'facile'
    
    return {
        'score': round(score, 1),
        'classification': classification,
        'n_words': n_words,
        'n_sentences': n_sentences,
        'n_letters': n_letters
    }


def compute_readability_scores(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Compute readability scores for all speeches and aggregate by speaker/party.
    
    Returns:
        {
            'by_speaker': {speaker: {avg_score, classification, n_speeches}, ...},
            'by_party': {party: {avg_score, classification, n_speeches}, ...},
            'distribution': {
                'difficile': count,
                'medio': count,
                'facile': count
            }
        }
    """
    # Compute per-speech scores
    scores = df[text_col].apply(compute_gulpease_score)
    df = df.copy()
    df['gulpease'] = scores.apply(lambda x: x['score'])
    df['readability_class'] = scores.apply(lambda x: x['classification'])
    
    result = {
        'by_speaker': {},
        'by_party': {},
        'distribution': df['readability_class'].value_counts().to_dict()
    }
    
    # Aggregate by speaker
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        avg_score = speaker_df['gulpease'].mean()
        
        classification = 'difficile' if avg_score < 55 else ('medio' if avg_score < 80 else 'facile')
        
        result['by_speaker'][speaker] = {
            'avg_score': round(avg_score, 1),
            'classification': classification,
            'n_speeches': len(speaker_df)
        }
    
    # Aggregate by party
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
            
        party_df = df[df[party_col] == party]
        avg_score = party_df['gulpease'].mean()
        
        classification = 'difficile' if avg_score < 55 else ('medio' if avg_score < 80 else 'facile')
        
        result['by_party'][party] = {
            'avg_score': round(avg_score, 1),
            'classification': classification,
            'n_speeches': len(party_df)
        }
    
    logger.info("Computed readability scores for %d speakers and %d parties",
                len(result['by_speaker']), len(result['by_party']))
    
    return result


def compute_polarization_score(text: str) -> dict:
    """
    Compute polarization score based on "Us vs Them" language.
    
    Analyzes:
    - Pronoun usage (noi/loro/voi)
    - Adversative terms (contro, nemici, etc.)
    - Us-them patterns
    
    Returns:
        {
            'score': 0-100 (higher = more polarizing),
            'pronoun_count': int,
            'adversative_count': int,
            'pattern_count': int,
            'classification': 'bassa' | 'media' | 'alta'
        }
    """
    text_lower = str(text).lower()
    tokens = tokenize_simple(text_lower)
    n_words = len(tokens) if tokens else 1
    
    # Count pronouns
    pronouns_lower = {p.lower() for p in POLARIZATION_PRONOUNS}
    pronoun_count = count_keywords(tokens, pronouns_lower)
    
    # Count adversative terms
    adversative_lower = {a.lower() for a in ADVERSATIVE_TERMS}
    adversative_count = count_keywords(tokens, adversative_lower)
    
    # Count patterns
    pattern_count = sum(1 for pattern in US_THEM_PATTERNS if pattern.lower() in text_lower)
    
    # Compute score
    # Weight: pronouns * 1, adversative * 2, patterns * 3
    raw_score = (pronoun_count * 1 + adversative_count * 2 + pattern_count * 3)
    
    # Normalize by text length and scale to 0-100
    normalized_score = (raw_score / n_words) * 500  # Empirical scaling
    score = min(100, max(0, normalized_score))
    
    # Classification
    if score < 20:
        classification = 'bassa'
    elif score < 50:
        classification = 'media'
    else:
        classification = 'alta'
    
    return {
        'score': round(score, 1),
        'pronoun_count': pronoun_count,
        'adversative_count': adversative_count,
        'pattern_count': pattern_count,
        'classification': classification
    }


def compute_polarization_scores(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Compute polarization scores for all speeches and aggregate.
    
    Returns:
        {
            'by_speaker': {speaker: {avg_score, classification, ...}, ...},
            'by_party': {party: {avg_score, classification, ...}, ...},
            'top_polarizers': [{speaker, party, score}, ...],
            'least_polarizers': [{speaker, party, score}, ...]
        }
    """
    # Compute per-speech scores
    scores = df[text_col].apply(compute_polarization_score)
    df = df.copy()
    df['polarization'] = scores.apply(lambda x: x['score'])
    df['polarization_class'] = scores.apply(lambda x: x['classification'])
    
    result = {
        'by_speaker': {},
        'by_party': {},
        'top_polarizers': [],
        'least_polarizers': []
    }
    
    # Aggregate by speaker
    speaker_scores = []
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        
        if len(speaker_df) < 3:  # Minimum speeches
            continue
            
        avg_score = speaker_df['polarization'].mean()
        party = speaker_df[party_col].iloc[0]
        
        classification = 'bassa' if avg_score < 20 else ('media' if avg_score < 50 else 'alta')
        
        result['by_speaker'][speaker] = {
            'avg_score': round(avg_score, 1),
            'classification': classification,
            'n_speeches': len(speaker_df),
            'party': party
        }
        
        speaker_scores.append({
            'speaker': speaker,
            'party': party,
            'score': round(avg_score, 1)
        })
    
    # Aggregate by party
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
            
        party_df = df[df[party_col] == party]
        avg_score = party_df['polarization'].mean()
        
        classification = 'bassa' if avg_score < 20 else ('media' if avg_score < 50 else 'alta')
        
        result['by_party'][party] = {
            'avg_score': round(avg_score, 1),
            'classification': classification,
            'n_speeches': len(party_df)
        }
    
    # Top and least polarizers
    speaker_scores.sort(key=lambda x: -x['score'])
    result['top_polarizers'] = speaker_scores[:10]
    result['least_polarizers'] = speaker_scores[-10:][::-1]
    
    logger.info("Computed polarization scores for %d speakers and %d parties",
                len(result['by_speaker']), len(result['by_party']))
    
    return result
