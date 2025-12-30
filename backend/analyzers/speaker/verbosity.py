"""
Verbosity and Linguistic Metrics - Text-based statistics.
"""
import logging

import pandas as pd

from .utils import (
    SELF_REFERENCE_WORDS, NEGATION_WORDS, FUTURE_MARKERS, PAST_MARKERS,
    NUMERIC_REGEX, count_sentences, count_words, count_pattern_matches, count_questions
)

logger = logging.getLogger(__name__)


def compute_text_metrics_batch(texts: list[str]) -> dict:
    """
    Compute all text-based metrics in a single pass.
    
    Returns dict with lists (same length as input texts):
    - word_count, sentence_count, words_per_sentence
    - question_count, self_ref_count, negation_count
    - future_count, past_count, numeric_count
    """
    results = {
        'word_count': [],
        'sentence_count': [],
        'words_per_sentence': [],
        'question_count': [],
        'self_ref_count': [],
        'negation_count': [],
        'future_count': [],
        'past_count': [],
        'numeric_count': [],
    }
    
    for text in texts:
        text = str(text)
        
        words = count_words(text)
        sentences = count_sentences(text)
        wps = words / sentences if sentences > 0 else 0
        
        results['word_count'].append(words)
        results['sentence_count'].append(sentences)
        results['words_per_sentence'].append(wps)
        results['question_count'].append(count_questions(text))
        results['self_ref_count'].append(count_pattern_matches(text, SELF_REFERENCE_WORDS))
        results['negation_count'].append(count_pattern_matches(text, NEGATION_WORDS))
        results['future_count'].append(count_pattern_matches(text, FUTURE_MARKERS))
        results['past_count'].append(count_pattern_matches(text, PAST_MARKERS))
        results['numeric_count'].append(len(NUMERIC_REGEX.findall(text)))
    
    return results


def aggregate_speaker_metrics(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    text_col: str = 'cleaned_text'
) -> dict:
    """
    Compute all text-based speaker statistics in one pass.
    
    Returns:
        {
            speaker_name: {
                'verbosity': {...},
                'linguistic': {...},
                'n_speeches': int
            },
            ...
        }
    """
    # First, compute metrics for all texts
    texts = df[text_col].tolist()
    batch_metrics = compute_text_metrics_batch(texts)
    
    # Add to DataFrame for aggregation
    df = df.copy()
    for key, values in batch_metrics.items():
        df[f'_m_{key}'] = values
    
    result = {}
    
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        n_speeches = len(speaker_df)
        
        if n_speeches < 1:
            continue
        
        total_words = speaker_df['_m_word_count'].sum()
        
        # Verbosity metrics
        verbosity = {
            'avg_words_per_speech': round(speaker_df['_m_word_count'].mean(), 1),
            'avg_sentences_per_speech': round(speaker_df['_m_sentence_count'].mean(), 1),
            'avg_words_per_sentence': round(speaker_df['_m_words_per_sentence'].mean(), 1),
            'total_words': int(total_words),
        }
        
        # Linguistic metrics (normalized per 1k words)
        if total_words > 0:
            linguistic = {
                'question_rate': round((speaker_df['_m_question_count'].sum() / total_words) * 1000, 2),
                'self_reference_rate': round((speaker_df['_m_self_ref_count'].sum() / total_words) * 1000, 2),
                'negation_rate': round((speaker_df['_m_negation_count'].sum() / total_words) * 1000, 2),
                'data_citation_rate': round((speaker_df['_m_numeric_count'].sum() / total_words) * 1000, 2),
            }
            
            # Temporal orientation
            future = speaker_df['_m_future_count'].sum()
            past = speaker_df['_m_past_count'].sum()
            total_temporal = future + past
            
            if total_temporal > 0:
                orientation_ratio = (future - past) / total_temporal
                linguistic['temporal_orientation'] = round(orientation_ratio, 3)
                linguistic['orientation_label'] = 'futuro' if orientation_ratio > 0.2 else ('passato' if orientation_ratio < -0.2 else 'neutro')
            else:
                linguistic['temporal_orientation'] = 0
                linguistic['orientation_label'] = 'neutro'
        else:
            linguistic = {
                'question_rate': 0, 'self_reference_rate': 0, 'negation_rate': 0,
                'data_citation_rate': 0, 'temporal_orientation': 0, 'orientation_label': 'n/a'
            }
        
        result[speaker] = {
            'verbosity': verbosity,
            'linguistic': linguistic,
            'n_speeches': n_speeches
        }
    
    logger.info("Computed text metrics for %d speakers", len(result))
    return result
