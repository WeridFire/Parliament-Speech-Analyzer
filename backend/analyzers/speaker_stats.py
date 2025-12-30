"""
Speaker Statistics - Comprehensive per-politician metrics.

This module calculates detailed statistics for each individual politician.
All functions are designed to be:
- Cacheable (results stored per speaker)
- Computed in batch (single pass over DataFrame when possible)
- Modular (each metric independent)

Provides:
- Verbosity metrics (word count, sentence length)
- Consistency index (embedding variance)
- Linguistic patterns (questions, negations, self-reference)
- Temporal patterns (intervention frequency)
- Leadership scores (topic dominance)
- Vocabulary richness (TTR, hapax)
- Network centrality (mention graph)
- Entity focus (NER-based targeting)
"""

import logging
import re
from collections import Counter, defaultdict
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# PATTERNS & CONSTANTS
# =============================================================================

# Self-reference patterns (first person singular)
SELF_REFERENCE_WORDS = {
    'io', 'mio', 'mia', 'miei', 'mie', 
    'me', 'mi',
    'personalmente'
}

# Negation patterns
NEGATION_WORDS = {
    'non', 'no', 'mai', 'nessuno', 'nulla', 'niente', 
    'neanche', 'nemmeno', 'neppure', 'senza'
}

# Temporal orientation markers
FUTURE_MARKERS = {
    'sarà', 'saranno', 'saremo', 'sarete',
    'faremo', 'faranno', 'farete',
    'vogliamo', 'vogliono', 'vorremo',
    'proponiamo', 'proporremo',
    'futuro', 'domani', 'prossimo', 'prossima', 'prossimi', 'prossime',
    'avanti', 'obiettivo', 'obiettivi', 'progetto', 'progetti',
    'svilupperemo', 'costruiremo', 'realizzeremo'
}

PAST_MARKERS = {
    'era', 'erano', 'eravamo',
    'faceva', 'facevano', 'facevamo',
    'vecchio', 'vecchia', 'vecchi', 'vecchie',
    'passato', 'passata', 'passati', 'passate',
    'prima', 'precedente', 'precedenti',
    'già', 'scorso', 'scorsa', 'scorsi', 'scorse',
    'ieri', 'tradizione', 'tradizioni', 'storico', 'storica'
}

# Numeric data patterns
NUMERIC_PATTERNS = [
    r'\d+\s*%',           # percentages
    r'\d+\s*€',           # euro amounts
    r'\d+\s*euro',        # "X euro"
    r'\d+\s*miliard',     # billions
    r'\d+\s*milion',      # millions
    r'\d+[\.,]\d+',       # decimals
]
NUMERIC_REGEX = re.compile('|'.join(NUMERIC_PATTERNS), re.IGNORECASE)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def tokenize_simple(text: str) -> list[str]:
    """Simple tokenization: lowercase, split on whitespace."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.split()


def count_sentences(text: str) -> int:
    """Count sentences based on punctuation."""
    # Split on sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)
    # Filter empty strings
    return len([s for s in sentences if s.strip()])


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def count_pattern_matches(text: str, words_set: set) -> int:
    """Count occurrences of words from a set in text."""
    tokens = tokenize_simple(text)
    return sum(1 for t in tokens if t in words_set)


def count_questions(text: str) -> int:
    """Count question marks in text."""
    return text.count('?')


# =============================================================================
# BATCH COMPUTATION (Single Pass)
# =============================================================================

def compute_text_metrics_batch(texts: list[str]) -> dict[str, list]:
    """
    Compute all text-based metrics in a single pass.
    
    Returns dict with lists (same length as input texts):
    - word_count
    - sentence_count
    - words_per_sentence
    - question_count
    - self_ref_count
    - negation_count
    - future_count
    - past_count
    - numeric_count
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
        words = count_words(text)
        sentences = count_sentences(text)
        
        results['word_count'].append(words)
        results['sentence_count'].append(sentences)
        results['words_per_sentence'].append(words / sentences if sentences > 0 else 0)
        results['question_count'].append(count_questions(text))
        results['self_ref_count'].append(count_pattern_matches(text, SELF_REFERENCE_WORDS))
        results['negation_count'].append(count_pattern_matches(text, NEGATION_WORDS))
        results['future_count'].append(count_pattern_matches(text, FUTURE_MARKERS))
        results['past_count'].append(count_pattern_matches(text, PAST_MARKERS))
        results['numeric_count'].append(len(NUMERIC_REGEX.findall(text)))
    
    return results


# =============================================================================
# AGGREGATION FUNCTIONS (Per Speaker)
# =============================================================================

def aggregate_speaker_metrics(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    text_col: str = 'cleaned_text'
) -> dict[str, dict]:
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
    logger.info("Computing speaker text metrics...")
    
    # First, compute metrics for all texts in batch
    all_metrics = compute_text_metrics_batch(df[text_col].tolist())
    
    # Add metrics as columns
    for metric_name, values in all_metrics.items():
        df = df.copy()
        df[f'_metric_{metric_name}'] = values
    
    # Aggregate by speaker
    speakers = df[speaker_col].unique()
    results = {}
    
    for speaker in speakers:
        speaker_df = df[df[speaker_col] == speaker]
        n_speeches = len(speaker_df)
        
        if n_speeches == 0:
            continue
        
        # Verbosity metrics
        total_words = speaker_df['_metric_word_count'].sum()
        avg_words = speaker_df['_metric_word_count'].mean()
        avg_sentences = speaker_df['_metric_sentence_count'].mean()
        avg_words_per_sentence = speaker_df['_metric_words_per_sentence'].mean()
        
        # Linguistic patterns (per 1000 words for normalization)
        per_1k = 1000 / total_words if total_words > 0 else 0
        
        question_total = speaker_df['_metric_question_count'].sum()
        self_ref_total = speaker_df['_metric_self_ref_count'].sum()
        negation_total = speaker_df['_metric_negation_count'].sum()
        future_total = speaker_df['_metric_future_count'].sum()
        past_total = speaker_df['_metric_past_count'].sum()
        numeric_total = speaker_df['_metric_numeric_count'].sum()
        
        # Temporal orientation ratio
        temporal_ratio = (future_total / past_total) if past_total > 0 else (
            2.0 if future_total > 0 else 1.0
        )
        
        results[speaker] = {
            'verbosity': {
                'avg_words_per_speech': round(avg_words, 1),
                'avg_sentences_per_speech': round(avg_sentences, 1),
                'avg_words_per_sentence': round(avg_words_per_sentence, 1),
                'total_words': int(total_words),
            },
            'linguistic': {
                'questions_per_1k_words': round(question_total * per_1k, 2),
                'self_ref_per_1k_words': round(self_ref_total * per_1k, 2),
                'negation_per_1k_words': round(negation_total * per_1k, 2),
                'future_markers_per_1k_words': round(future_total * per_1k, 2),
                'past_markers_per_1k_words': round(past_total * per_1k, 2),
                'temporal_orientation': round(temporal_ratio, 2),  # >1 = future, <1 = past
                'data_citations_per_1k_words': round(numeric_total * per_1k, 2),
            },
            'n_speeches': n_speeches
        }
    
    logger.info("Computed text metrics for %d speakers", len(results))
    return results


# =============================================================================
# EMBEDDING-BASED METRICS
# =============================================================================

def compute_consistency_index(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    speaker_col: str = 'deputy'
) -> dict[str, dict]:
    """
    Compute thematic consistency for each speaker.
    
    Lower variance = more consistent (always talks about same things)
    Higher variance = less consistent (jumps between topics)
    
    Returns score 0-100 where 100 = maximally consistent.
    """
    logger.info("Computing consistency index...")
    results = {}
    
    speakers = df[speaker_col].unique()
    
    # Collect all variances for normalization
    all_variances = []
    
    for speaker in speakers:
        mask = df[speaker_col] == speaker
        speaker_embeddings = embeddings[mask]
        
        if len(speaker_embeddings) < 2:
            continue
        
        # Compute variance of embeddings
        # Using mean of per-dimension variance
        variance = np.mean(np.var(speaker_embeddings, axis=0))
        all_variances.append((speaker, variance, len(speaker_embeddings)))
    
    if not all_variances:
        return {}
    
    # Normalize to 0-100 scale (invert so high = consistent)
    variances_only = [v[1] for v in all_variances]
    max_var = max(variances_only) if variances_only else 1
    min_var = min(variances_only) if variances_only else 0
    var_range = max_var - min_var if max_var > min_var else 1
    
    for speaker, variance, n_speeches in all_variances:
        # Normalize and invert (0 variance = 100 score)
        normalized = (variance - min_var) / var_range
        score = (1 - normalized) * 100
        
        results[speaker] = {
            'consistency_score': round(score, 1),
            'raw_variance': round(float(variance), 6),
            'n_speeches': n_speeches,
            'interpretation': (
                'very_consistent' if score >= 80 else
                'consistent' if score >= 60 else
                'moderate' if score >= 40 else
                'variable' if score >= 20 else
                'highly_variable'
            )
        }
    
    logger.info("Computed consistency for %d speakers", len(results))
    return results


def compute_topic_leadership(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_centroids: np.ndarray,
    cluster_labels: dict,
    speaker_col: str = 'deputy',
    cluster_col: str = 'cluster'
) -> dict[str, dict]:
    """
    Identify which speakers are the "leaders" (most representative) of each topic.
    
    A speaker leads a topic if their average embedding is closest to the cluster centroid.
    
    Returns for each speaker:
    - topics_led: list of topic IDs where this speaker is the leader
    - leadership_scores: dict of topic_id -> distance to centroid
    - dominant_topic: the topic this speaker is most aligned with
    """
    logger.info("Computing topic leadership...")
    
    # Compute speaker centroids
    speaker_centroids = {}
    speaker_n_speeches = {}
    
    for speaker in df[speaker_col].unique():
        mask = df[speaker_col] == speaker
        speaker_embeddings = embeddings[mask]
        
        if len(speaker_embeddings) >= 3:  # Minimum speeches for leadership
            speaker_centroids[speaker] = np.mean(speaker_embeddings, axis=0)
            speaker_n_speeches[speaker] = len(speaker_embeddings)
    
    if not speaker_centroids:
        return {}
    
    # For each cluster, find the closest speaker
    topic_leaders = {}  # topic_id -> (speaker, distance)
    speaker_topic_distances = defaultdict(dict)  # speaker -> {topic_id: distance}
    
    for cluster_id, centroid in enumerate(cluster_centroids):
        if cluster_id >= len(cluster_centroids):
            continue
            
        min_distance = float('inf')
        leader = None
        
        for speaker, speaker_centroid in speaker_centroids.items():
            distance = np.linalg.norm(speaker_centroid - centroid)
            speaker_topic_distances[speaker][cluster_id] = float(distance)
            
            if distance < min_distance:
                min_distance = distance
                leader = speaker
        
        if leader:
            topic_leaders[cluster_id] = (leader, min_distance)
    
    # Build results per speaker
    results = {}
    
    for speaker, centroid in speaker_centroids.items():
        # Find topics led by this speaker
        topics_led = [
            tid for tid, (lead, _) in topic_leaders.items() 
            if lead == speaker
        ]
        
        # Find dominant topic (minimum distance)
        distances = speaker_topic_distances[speaker]
        if distances:
            dominant_topic = min(distances, key=distances.get)
            dominant_label = cluster_labels.get(dominant_topic, f"Topic {dominant_topic}")
        else:
            dominant_topic = None
            dominant_label = None
        
        results[speaker] = {
            'topics_led': topics_led,
            'topics_led_labels': [cluster_labels.get(t, f"Topic {t}") for t in topics_led],
            'n_topics_led': len(topics_led),
            'dominant_topic': dominant_topic,
            'dominant_topic_label': dominant_label,
            'topic_distances': {
                cluster_labels.get(k, f"Topic {k}"): round(v, 4) 
                for k, v in distances.items()
            },
            'n_speeches': speaker_n_speeches.get(speaker, 0)
        }
    
    logger.info("Computed topic leadership for %d speakers", len(results))
    return results


# =============================================================================
# TEMPORAL PATTERNS
# =============================================================================

def compute_intervention_patterns(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    date_col: str = 'date'
) -> dict[str, dict]:
    """
    Analyze intervention patterns over time for each speaker.
    
    Returns:
    - avg_speeches_per_month: activity level
    - regularity_score: 0-100 (100 = very regular, 0 = sporadic)
    - active_months: number of months with at least one speech
    - burst_score: tendency to cluster speeches (0-100)
    """
    from backend.analyzers.temporal import parse_date
    
    logger.info("Computing intervention patterns...")
    
    # Parse dates
    df = df.copy()
    df['_parsed_date'] = df[date_col].apply(parse_date)
    df['_month'] = df['_parsed_date'].apply(
        lambda x: f"{x.year}-{x.month:02d}" if x else None
    )
    
    # Filter rows with valid dates
    df = df[df['_month'].notna()]
    
    # Get all months in dataset
    all_months = sorted(df['_month'].unique())
    total_months = len(all_months)
    
    if total_months == 0:
        return {}
    
    results = {}
    
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        n_speeches = len(speaker_df)
        
        if n_speeches < 2:
            continue
        
        # Count speeches per month
        month_counts = speaker_df['_month'].value_counts().to_dict()
        active_months = len(month_counts)
        
        # Average per active month
        avg_per_active_month = n_speeches / active_months if active_months > 0 else 0
        
        # Average across all months (including zeros)
        avg_per_month = n_speeches / total_months if total_months > 0 else 0
        
        # Regularity: what % of months is this speaker active?
        regularity = (active_months / total_months) * 100 if total_months > 0 else 0
        
        # Burst score: standard deviation of speeches per month
        # High std = bursty, low std = regular
        counts_list = [month_counts.get(m, 0) for m in all_months]
        std_counts = np.std(counts_list) if counts_list else 0
        mean_counts = np.mean(counts_list) if counts_list else 0
        
        # Coefficient of variation (normalized burstiness)
        cv = std_counts / mean_counts if mean_counts > 0 else 0
        burst_score = min(cv * 50, 100)  # Scale to 0-100
        
        results[speaker] = {
            'n_speeches': n_speeches,
            'active_months': active_months,
            'total_months_in_data': total_months,
            'avg_speeches_per_month': round(avg_per_month, 2),
            'avg_speeches_per_active_month': round(avg_per_active_month, 2),
            'regularity_score': round(regularity, 1),
            'burst_score': round(burst_score, 1),
            'interpretation': (
                'very_regular' if regularity >= 80 else
                'regular' if regularity >= 60 else
                'moderate' if regularity >= 40 else
                'sporadic' if regularity >= 20 else
                'very_sporadic'
            )
        }
    
    logger.info("Computed intervention patterns for %d speakers", len(results))
    return results


# =============================================================================
# VOCABULARY RICHNESS
# =============================================================================

def compute_vocabulary_richness(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    text_col: str = 'cleaned_text'
) -> dict[str, dict]:
    """
    Compute vocabulary richness metrics for each speaker.
    
    Returns:
    - type_token_ratio (TTR): unique words / total words
    - hapax_ratio: words used only once / total unique words
    - vocabulary_size: number of unique words
    """
    logger.info("Computing vocabulary richness...")
    results = {}
    
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        
        if len(speaker_df) < 2:
            continue
        
        # Combine all texts
        all_text = ' '.join(speaker_df[text_col].tolist())
        tokens = tokenize_simple(all_text)
        
        if len(tokens) < 50:  # Minimum tokens for meaningful analysis
            continue
        
        total_tokens = len(tokens)
        token_counts = Counter(tokens)
        unique_tokens = len(token_counts)
        
        # Type-Token Ratio
        ttr = unique_tokens / total_tokens if total_tokens > 0 else 0
        
        # Hapax legomena (words appearing exactly once)
        hapax = sum(1 for count in token_counts.values() if count == 1)
        hapax_ratio = hapax / unique_tokens if unique_tokens > 0 else 0
        
        # Normalize TTR for comparison (using root TTR for length normalization)
        root_ttr = unique_tokens / np.sqrt(total_tokens) if total_tokens > 0 else 0
        
        results[speaker] = {
            'vocabulary_size': unique_tokens,
            'total_words': total_tokens,
            'type_token_ratio': round(ttr, 4),
            'root_ttr': round(root_ttr, 2),  # Better for cross-speaker comparison
            'hapax_count': hapax,
            'hapax_ratio': round(hapax_ratio, 4),
            'n_speeches': len(speaker_df),
            'richness_score': round(root_ttr * 10, 1),  # Scaled 0-100ish
            'interpretation': (
                'very_rich' if root_ttr >= 15 else
                'rich' if root_ttr >= 12 else
                'moderate' if root_ttr >= 9 else
                'limited' if root_ttr >= 6 else
                'very_limited'
            )
        }
    
    logger.info("Computed vocabulary richness for %d speakers", len(results))
    return results


# =============================================================================
# NETWORK ANALYSIS (Mention Detection)
# =============================================================================

def compute_interaction_network(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    text_col: str = 'cleaned_text',
    party_col: str = 'group'
) -> dict[str, dict]:
    """
    Build a mention network based on references to other politicians.
    
    Detects patterns like:
    - "l'onorevole Rossi"
    - "il collega Bianchi"
    - "come diceva il ministro Verdi"
    
    Returns for each speaker:
    - mentions_given: who they mention
    - mentions_received: who mentions them
    - out_degree: number of unique people mentioned
    - in_degree: number of unique people who mention them
    """
    logger.info("Computing interaction network...")
    
    # Get all speaker names (for matching)
    all_speakers = df[speaker_col].unique()
    
    # Extract last names for matching
    speaker_last_names = {}
    for speaker in all_speakers:
        # Extract last name (first word, typically surname)
        parts = speaker.split()
        if parts:
            last_name = parts[0].lower()
            if len(last_name) >= 3:  # Avoid too short matches
                speaker_last_names[last_name] = speaker
    
    # Mention patterns
    MENTION_PATTERNS = [
        r"l['\s]onorevole\s+(\w+)",
        r"il\s+colleg[ao]\s+(\w+)",
        r"la\s+colleg[ao]\s+(\w+)",
        r"il\s+ministro\s+(\w+)",
        r"la\s+ministra\s+(\w+)",
        r"il\s+senatore\s+(\w+)",
        r"la\s+senatrice\s+(\w+)",
        r"il\s+deputato\s+(\w+)",
        r"la\s+deputata\s+(\w+)",
        r"come\s+diceva\s+(\w+)",
        r"come\s+ha\s+detto\s+(\w+)",
    ]
    
    # Build edges
    mentions = defaultdict(list)  # speaker -> list of mentioned speakers
    mentioned_by = defaultdict(list)  # speaker -> list of speakers who mention them
    
    for _, row in df.iterrows():
        speaker = row[speaker_col]
        text = row[text_col].lower()
        
        for pattern in MENTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                match_lower = match.lower()
                # Check if match corresponds to a known speaker
                if match_lower in speaker_last_names:
                    mentioned_speaker = speaker_last_names[match_lower]
                    if mentioned_speaker != speaker:  # Don't count self-mentions
                        mentions[speaker].append(mentioned_speaker)
                        mentioned_by[mentioned_speaker].append(speaker)
    
    # Aggregate results
    results = {}
    
    for speaker in all_speakers:
        speaker_df = df[df[speaker_col] == speaker]
        party = speaker_df[party_col].iloc[0] if len(speaker_df) > 0 else 'Unknown'
        
        given = mentions.get(speaker, [])
        received = mentioned_by.get(speaker, [])
        
        # Unique counts
        unique_given = set(given)
        unique_received = set(received)
        
        results[speaker] = {
            'party': party,
            'out_degree': len(unique_given),
            'in_degree': len(unique_received),
            'total_mentions_given': len(given),
            'total_mentions_received': len(received),
            'top_mentioned': Counter(given).most_common(5),
            'top_mentioners': Counter(received).most_common(5),
            'n_speeches': len(speaker_df),
            'network_score': len(unique_given) + len(unique_received) * 2,  # Weight received more
        }
    
    logger.info("Computed network for %d speakers", len(results))
    return results


# =============================================================================
# NER-BASED ENTITY FOCUS (Optional - Requires SpaCy)
# =============================================================================

_nlp = None
_spacy_available = False


def _load_spacy():
    """Lazy load spaCy model."""
    global _nlp, _spacy_available
    
    if _nlp is not None:
        return _nlp
    
    try:
        import spacy
        try:
            _nlp = spacy.load('it_core_news_sm')
            _spacy_available = True
            logger.info("Loaded spaCy model for NER")
        except OSError:
            logger.warning("SpaCy Italian model not found. Run: python -m spacy download it_core_news_sm")
            _spacy_available = False
    except ImportError:
        logger.warning("SpaCy not installed. Entity focus will be skipped.")
        _spacy_available = False
    
    return _nlp


def compute_entity_focus(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    text_col: str = 'cleaned_text',
    max_texts_per_speaker: int = 100
) -> dict[str, dict]:
    """
    Extract named entities mentioned by each speaker.
    
    Requires spaCy with Italian model.
    
    Returns for each speaker:
    - top_persons: most mentioned person names
    - top_orgs: most mentioned organizations
    - top_locations: most mentioned places
    """
    nlp = _load_spacy()
    
    if not _spacy_available or nlp is None:
        logger.warning("Skipping entity focus (spaCy not available)")
        return {}
    
    logger.info("Computing entity focus (this may take a while)...")
    
    results = {}
    
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        
        if len(speaker_df) < 2:
            continue
        
        # Sample if too many texts
        if len(speaker_df) > max_texts_per_speaker:
            speaker_df = speaker_df.sample(n=max_texts_per_speaker, random_state=42)
        
        persons = Counter()
        orgs = Counter()
        locations = Counter()
        
        # Process texts
        texts = speaker_df[text_col].tolist()
        
        for doc in nlp.pipe(texts, batch_size=50, disable=['parser']):
            for ent in doc.ents:
                if ent.label_ == 'PER':
                    persons[ent.text] += 1
                elif ent.label_ == 'ORG':
                    orgs[ent.text] += 1
                elif ent.label_ in ('LOC', 'GPE'):
                    locations[ent.text] += 1
        
        results[speaker] = {
            'top_persons': persons.most_common(10),
            'top_orgs': orgs.most_common(10),
            'top_locations': locations.most_common(10),
            'total_person_mentions': sum(persons.values()),
            'total_org_mentions': sum(orgs.values()),
            'total_location_mentions': sum(locations.values()),
            'n_speeches_analyzed': len(speaker_df),
        }
    
    logger.info("Computed entity focus for %d speakers", len(results))
    return results


# =============================================================================
# UNIFIED COMPUTATION
# =============================================================================

def compute_all_speaker_stats(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_centroids: np.ndarray,
    cluster_labels: dict,
    speaker_col: str = 'deputy',
    text_col: str = 'cleaned_text',
    date_col: str = 'date',
    party_col: str = 'group',
    include_ner: bool = False
) -> dict:
    """
    Compute all speaker statistics in an optimized manner.
    
    Args:
        df: DataFrame with speeches
        embeddings: Speech embeddings array
        cluster_centroids: Cluster centroid vectors
        cluster_labels: Dict mapping cluster_id -> label
        speaker_col: Column with speaker names
        text_col: Column with cleaned text
        date_col: Column with dates
        party_col: Column with party names
        include_ner: Whether to run NER-based entity extraction (slow)
    
    Returns:
        {
            'by_speaker': {
                speaker_name: {
                    'verbosity': {...},
                    'linguistic': {...},
                    'consistency': {...},
                    'topic_leadership': {...},
                    'intervention_patterns': {...},
                    'vocabulary': {...},
                    'network': {...},
                    'entity_focus': {...},  # if include_ner
                },
                ...
            },
            'rankings': {
                'most_verbose': [...],
                'most_consistent': [...],
                'most_questions': [...],
                'topic_leaders': {...},
                ...
            }
        }
    """
    logger.info("=" * 60)
    logger.info("Computing all speaker statistics...")
    logger.info("=" * 60)
    
    # 1. Text-based metrics (single pass)
    text_metrics = aggregate_speaker_metrics(df, speaker_col, text_col)
    
    # 2. Embedding-based metrics
    consistency = compute_consistency_index(df, embeddings, speaker_col)
    leadership = compute_topic_leadership(
        df, embeddings, cluster_centroids, cluster_labels, speaker_col
    )
    
    # 3. Temporal patterns
    intervention = compute_intervention_patterns(df, speaker_col, date_col)
    
    # 4. Vocabulary richness
    vocabulary = compute_vocabulary_richness(df, speaker_col, text_col)
    
    # 5. Network analysis
    network = compute_interaction_network(df, speaker_col, text_col, party_col)
    
    # 6. Entity focus (optional)
    entity_focus = {}
    if include_ner:
        entity_focus = compute_entity_focus(df, speaker_col, text_col)
    
    # Merge all metrics by speaker
    all_speakers = set(text_metrics.keys())
    by_speaker = {}
    
    for speaker in all_speakers:
        by_speaker[speaker] = {
            'verbosity': text_metrics.get(speaker, {}).get('verbosity', {}),
            'linguistic': text_metrics.get(speaker, {}).get('linguistic', {}),
            'consistency': consistency.get(speaker, {}),
            'topic_leadership': leadership.get(speaker, {}),
            'intervention_patterns': intervention.get(speaker, {}),
            'vocabulary': vocabulary.get(speaker, {}),
            'network': network.get(speaker, {}),
        }
        
        if include_ner and speaker in entity_focus:
            by_speaker[speaker]['entity_focus'] = entity_focus[speaker]
    
    # Build rankings
    rankings = _build_rankings(by_speaker)
    
    logger.info("=" * 60)
    logger.info("Speaker statistics complete: %d speakers analyzed", len(by_speaker))
    logger.info("=" * 60)
    
    return {
        'by_speaker': by_speaker,
        'rankings': rankings
    }


def _build_rankings(by_speaker: dict, top_n: int = 10) -> dict:
    """Build various rankings from speaker stats."""
    rankings = {}
    
    # Helper to safely get nested values
    def get_val(speaker, *keys, default=0):
        data = by_speaker.get(speaker, {})
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, {})
            else:
                return default
        return data if isinstance(data, (int, float)) else default
    
    speakers = list(by_speaker.keys())
    
    # Most verbose (highest avg words per speech)
    rankings['most_verbose'] = sorted(
        [(s, get_val(s, 'verbosity', 'avg_words_per_speech')) for s in speakers],
        key=lambda x: -x[1]
    )[:top_n]
    
    # Most concise (lowest avg words per speech, min 10 speeches)
    rankings['most_concise'] = sorted(
        [(s, get_val(s, 'verbosity', 'avg_words_per_speech')) 
         for s in speakers if get_val(s, 'verbosity', 'total_words') > 500],
        key=lambda x: x[1]
    )[:top_n]
    
    # Most questions
    rankings['most_questions'] = sorted(
        [(s, get_val(s, 'linguistic', 'questions_per_1k_words')) for s in speakers],
        key=lambda x: -x[1]
    )[:top_n]
    
    # Most self-referential
    rankings['most_self_referential'] = sorted(
        [(s, get_val(s, 'linguistic', 'self_ref_per_1k_words')) for s in speakers],
        key=lambda x: -x[1]
    )[:top_n]
    
    # Most negative (highest negation rate)
    rankings['most_negative'] = sorted(
        [(s, get_val(s, 'linguistic', 'negation_per_1k_words')) for s in speakers],
        key=lambda x: -x[1]
    )[:top_n]
    
    # Most future-oriented
    rankings['most_future_oriented'] = sorted(
        [(s, get_val(s, 'linguistic', 'temporal_orientation')) for s in speakers],
        key=lambda x: -x[1]
    )[:top_n]
    
    # Most data-driven
    rankings['most_data_driven'] = sorted(
        [(s, get_val(s, 'linguistic', 'data_citations_per_1k_words')) for s in speakers],
        key=lambda x: -x[1]
    )[:top_n]
    
    # Most consistent
    rankings['most_consistent'] = sorted(
        [(s, get_val(s, 'consistency', 'consistency_score')) for s in speakers],
        key=lambda x: -x[1]
    )[:top_n]
    
    # Most variable
    rankings['most_variable'] = sorted(
        [(s, get_val(s, 'consistency', 'consistency_score')) 
         for s in speakers if get_val(s, 'consistency', 'consistency_score') > 0],
        key=lambda x: x[1]
    )[:top_n]
    
    # Most regular (intervention patterns)
    rankings['most_regular'] = sorted(
        [(s, get_val(s, 'intervention_patterns', 'regularity_score')) for s in speakers],
        key=lambda x: -x[1]
    )[:top_n]
    
    # Richest vocabulary
    rankings['richest_vocabulary'] = sorted(
        [(s, get_val(s, 'vocabulary', 'root_ttr')) for s in speakers],
        key=lambda x: -x[1]
    )[:top_n]
    
    # Most connected (network)
    rankings['most_connected'] = sorted(
        [(s, get_val(s, 'network', 'network_score')) for s in speakers],
        key=lambda x: -x[1]
    )[:top_n]
    
    return rankings
