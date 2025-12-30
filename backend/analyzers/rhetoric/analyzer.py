"""
Rhetoric Analyzer - Main analyzer class.
"""
import logging

import pandas as pd

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .patterns import compute_rhetoric_scores, add_rhetoric_scores

logger = logging.getLogger(__name__)


@analyzer
class RhetoricAnalyzer(BaseAnalyzer):
    """Analyzer for speech style and rhetoric patterns."""
    
    name = "rhetoric"
    description = "Speech style and rhetoric patterns"
    version = "1.0"
    
    default_features = {
        'populist': True,
        'anti_establishment': True,
        'emotional': True,
        'institutional': True,
    }
    
    def compute(self) -> dict:
        """Compute rhetoric scores aggregated by speaker and party."""
        logger.info("Computing rhetoric scores...")
        
        # Add scores to each speech
        scored_df = add_rhetoric_scores(self.df, self.text_col)
        
        result = {
            'by_speaker': {},
            'by_party': {},
            'rankings': {}
        }
        
        # Aggregate by speaker
        for speaker in scored_df[self.speaker_col].unique():
            speaker_df = scored_df[scored_df[self.speaker_col] == speaker]
            
            if len(speaker_df) < 3:
                continue
            
            result['by_speaker'][speaker] = {
                'populist': round(speaker_df['populist'].mean(), 2),
                'anti_establishment': round(speaker_df['anti_establishment'].mean(), 2),
                'emotional': round(speaker_df['emotional'].mean(), 2),
                'institutional': round(speaker_df['institutional'].mean(), 2),
                'party': speaker_df[self.party_col].iloc[0],
                'n_speeches': len(speaker_df)
            }
        
        # Aggregate by party
        for party in scored_df[self.party_col].unique():
            if party == 'Unknown Group':
                continue
                
            party_df = scored_df[scored_df[self.party_col] == party]
            
            result['by_party'][party] = {
                'populist': round(party_df['populist'].mean(), 2),
                'anti_establishment': round(party_df['anti_establishment'].mean(), 2),
                'emotional': round(party_df['emotional'].mean(), 2),
                'institutional': round(party_df['institutional'].mean(), 2),
                'n_speeches': len(party_df)
            }
        
        # Build rankings
        speakers = list(result['by_speaker'].items())
        
        for metric in ['populist', 'anti_establishment', 'emotional', 'institutional']:
            sorted_speakers = sorted(speakers, key=lambda x: -x[1][metric])[:10]
            result['rankings'][f'most_{metric}'] = [
                {'speaker': s, 'score': d[metric], 'party': d['party']}
                for s, d in sorted_speakers
            ]
        
        logger.info("Rhetoric analysis complete")
        return result
