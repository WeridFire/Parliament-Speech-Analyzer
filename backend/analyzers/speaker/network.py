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
        # Name format is: "COGNOME Nome [PARTITO]" or just "COGNOME Nome"
        # First, remove the party bracket part if present
        clean_name = re.sub(r'\s*\[[^\]]*\]$', '', speaker).strip()
        
        parts = clean_name.split()
        if len(parts) >= 1:
            # The surname is the FIRST word (Italian convention: "ROSSI Mario")
            surname = parts[0]
            
            # Validate: real surnames are ALL CAPS (e.g., "ROSSI", "MELONI")
            # This filters out scraper noise like "Allora", "Lei oggi", "Non basta"
            if len(surname) >= 3 and surname.isupper():
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
