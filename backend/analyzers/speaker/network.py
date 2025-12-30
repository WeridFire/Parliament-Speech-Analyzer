"""
Interaction Network - Mention detection between speakers.
"""
import logging
import re
from collections import defaultdict

import pandas as pd

logger = logging.getLogger(__name__)


def compute_interaction_network(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    text_col: str = 'cleaned_text'
) -> dict:
    """
    Compute interaction network based on mentions.
    
    Detects when speakers mention each other by name.
    
    Returns:
    - mentions_given: who this speaker mentions
    - mentions_received: who mentions this speaker
    - out_degree: number of different speakers mentioned
    - in_degree: number of different speakers mentioning
    """
    speakers = set(df[speaker_col].unique())
    
    # Build lookup for speaker names
    speaker_patterns = {}
    for speaker in speakers:
        # Create regex pattern for each speaker
        parts = speaker.split()
        if len(parts) >= 2:
            # Match surname or full name (case insensitive)
            surname = parts[-1]
            if len(surname) >= 3:
                speaker_patterns[speaker] = re.compile(r'\b' + re.escape(surname) + r'\b', re.IGNORECASE)
    
    # Track mentions
    mentions_given = defaultdict(lambda: defaultdict(int))
    mentions_received = defaultdict(lambda: defaultdict(int))
    
    for _, row in df.iterrows():
        speaker = row[speaker_col]
        text = str(row[text_col])
        
        # Check for mentions of other speakers
        for other_speaker, pattern in speaker_patterns.items():
            if other_speaker == speaker:
                continue
            
            matches = len(pattern.findall(text))
            if matches > 0:
                mentions_given[speaker][other_speaker] += matches
                mentions_received[other_speaker][speaker] += matches
    
    # Build result
    result = {}
    
    for speaker in speakers:
        given = dict(mentions_given.get(speaker, {}))
        received = dict(mentions_received.get(speaker, {}))
        
        out_degree = len(given)
        in_degree = len(received)
        total_given = sum(given.values())
        total_received = sum(received.values())
        
        result[speaker] = {
            'mentions_given': total_given,
            'mentions_received': total_received,
            'out_degree': out_degree,
            'in_degree': in_degree,
            'top_mentioned': sorted(given.items(), key=lambda x: -x[1])[:5],
            'mentioned_by': sorted(received.items(), key=lambda x: -x[1])[:5],
        }
    
    logger.info("Computed interaction network for %d speakers", len(result))
    return result
