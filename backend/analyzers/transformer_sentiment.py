"""
Transformer-based Sentiment Analysis - Optional high-accuracy sentiment using pretrained models.

This module provides:
- Lazy loading of transformer models
- Batch processing for efficiency  
- GPU support when available
- Fallback to keyword-based if model unavailable

Usage:
    # Compute sentiment scores for texts
    scores = compute_transformer_sentiment(texts, batch_size=32)
    
    # Compute aggregated topic sentiment
    result = compute_topic_sentiment_transformer(df, ...)
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)

# Lazy-loaded model
_sentiment_pipeline = None
_model_loaded = False
_model_available = False

# Model configuration
SENTIMENT_MODEL = "MilaNLProc/feel-it-italian-sentiment"
MAX_TEXT_LENGTH = 512  # Transformer token limit


def _load_sentiment_model():
    """Lazy load the transformer sentiment model."""
    global _sentiment_pipeline, _model_loaded, _model_available
    
    if _model_loaded:
        return _sentiment_pipeline
    
    _model_loaded = True
    
    try:
        from transformers import pipeline
        import torch
        
        # Determine device
        device = 0 if torch.cuda.is_available() else -1
        device_name = "GPU" if device == 0 else "CPU"
        
        logger.info("Loading sentiment model (%s)...", SENTIMENT_MODEL)
        logger.info("Using device: %s", device_name)
        
        _sentiment_pipeline = pipeline(
            "text-classification",
            model=SENTIMENT_MODEL,
            device=device,
            truncation=True,
            max_length=MAX_TEXT_LENGTH
        )
        
        _model_available = True
        logger.info("Sentiment model loaded successfully")
        
    except ImportError as e:
        logger.warning("Transformers library not installed: %s", e)
        logger.warning("Install with: pip install transformers torch")
        _model_available = False
        
    except Exception as e:
        logger.warning("Failed to load sentiment model: %s", e)
        _model_available = False
    
    return _sentiment_pipeline


def is_transformer_available() -> bool:
    """Check if transformer model can be loaded."""
    _load_sentiment_model()
    return _model_available


def compute_single_sentiment(text: str) -> dict:
    """
    Compute sentiment for a single text.
    
    Returns:
        {
            'label': 'positive' | 'negative',
            'score': float,  # confidence 0-1
            'sentiment_score': float  # -1 to 1 normalized
        }
    """
    model = _load_sentiment_model()
    
    if model is None:
        return {'label': 'neutral', 'score': 0.5, 'sentiment_score': 0.0}
    
    # Truncate text to avoid token overflow
    text = text[:2000] if text else ""
    
    try:
        result = model(text)[0]
        
        # Normalize to -1 to 1 scale
        label = result['label'].lower()
        confidence = result['score']
        
        if label == 'positive':
            sentiment_score = confidence
        elif label == 'negative':
            sentiment_score = -confidence
        else:
            sentiment_score = 0.0
        
        return {
            'label': label,
            'score': confidence,
            'sentiment_score': sentiment_score
        }
        
    except Exception as e:
        logger.debug("Sentiment error for text: %s", str(e)[:100])
        return {'label': 'neutral', 'score': 0.5, 'sentiment_score': 0.0}


def compute_batch_sentiment(texts: list[str], batch_size: int = 32) -> list[dict]:
    """
    Compute sentiment for a batch of texts efficiently.
    
    Args:
        texts: List of text strings
        batch_size: Number of texts to process at once
        
    Returns:
        List of sentiment results (same order as input)
    """
    model = _load_sentiment_model()
    
    if model is None:
        return [{'label': 'neutral', 'score': 0.5, 'sentiment_score': 0.0} for _ in texts]
    
    results = []
    total = len(texts)
    
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        
        # Truncate texts
        batch = [t[:2000] if t else "" for t in batch]
        
        try:
            predictions = model(batch)
            
            for pred in predictions:
                label = pred['label'].lower()
                confidence = pred['score']
                
                if label == 'positive':
                    sentiment_score = confidence
                elif label == 'negative':
                    sentiment_score = -confidence
                else:
                    sentiment_score = 0.0
                
                results.append({
                    'label': label,
                    'score': confidence,
                    'sentiment_score': sentiment_score
                })
                
        except Exception as e:
            logger.warning("Batch sentiment error: %s", str(e)[:100])
            # Fallback for failed batch
            results.extend([{'label': 'neutral', 'score': 0.5, 'sentiment_score': 0.0} for _ in batch])
        
        # Progress logging
        if (i + batch_size) % 500 == 0 or (i + batch_size) >= total:
            logger.info("  Processed %d/%d texts (%.1f%%)", min(i + batch_size, total), total, 
                       min(i + batch_size, total) / total * 100)
    
    return results


def compute_topic_sentiment_transformer(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    cluster_col: str = 'cluster',
    cluster_labels: dict = None,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
    batch_size: int = 32
) -> dict:
    """
    Compute topic sentiment using transformer model.
    
    Same interface as keyword-based compute_topic_sentiment for drop-in replacement.
    
    Returns same structure:
        {
            'by_speaker': {...},
            'by_party': {...},
            'by_cluster': {...}
        }
    """
    logger.info("Computing topic sentiment with transformer model...")
    
    # Get all texts
    texts = df[text_col].fillna("").tolist()
    
    # Batch compute sentiments
    sentiments_raw = compute_batch_sentiment(texts, batch_size=batch_size)
    
    # Build sentiment data
    labels = cluster_labels or {}
    
    result = {
        'by_speaker': defaultdict(dict),
        'by_party': defaultdict(dict),
        'by_cluster': {}
    }
    
    # Create sentiment DataFrame for aggregation
    sentiment_records = []
    for idx, (_, row) in enumerate(df.iterrows()):
        sentiment_records.append({
            'speaker': row[speaker_col],
            'party': row[party_col],
            'cluster': int(row[cluster_col]),
            'sentiment': sentiments_raw[idx]['sentiment_score'],
            'label': sentiments_raw[idx]['label']
        })
    
    sentiment_df = pd.DataFrame(sentiment_records)
    
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
    
    logger.info("Computed transformer sentiment for %d speakers and %d parties",
                len(result['by_speaker']), len(result['by_party']))
    
    return result
