"""
Identity Analyzer - Main analyzer class for identity metrics.

Orchestrates:
- Thematic Fingerprint
- Generalism Index
- Distinctive Keywords
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .fingerprint import compute_thematic_fingerprint
from .generalism import compute_generalism_index
from .keywords import compute_distinctive_keywords

logger = logging.getLogger(__name__)


@analyzer
class IdentityAnalyzer(BaseAnalyzer):
    """
    Analyzer for political identity and DNA.
    
    Computes:
    - thematic_fingerprint: Radar chart of topic affinity
    - generalism_index: Entropy-based specialization score
    - distinctive_keywords: TF-IDF distinctive terms per party
    """
    
    name = "identity"
    description = "Political identity and DNA analysis"
    version = "1.0"
    
    default_features = {
        'thematic_fingerprint': True,
        'generalism_index': True,
        'distinctive_keywords': True,
    }
    
    @classmethod
    def get_dependencies(cls) -> list[str]:
        """Identity analyzer requires embeddings and cluster centroids."""
        return ['embeddings', 'cluster_labels', 'cluster_centroids']
    
    def compute(self) -> dict:
        """
        Compute all identity metrics.
        
        Returns:
            {
                'thematic_fingerprints': {...},
                'generalism_index': {...},
                'distinctive_keywords': {...}
            }
        """
        self.validate_dependencies()
        
        result = {}
        
        # Thematic Fingerprint
        if self.is_feature_enabled('thematic_fingerprint'):
            logger.info("Computing thematic fingerprints...")
            result['thematic_fingerprints'] = compute_thematic_fingerprint(
                df=self.df,
                embeddings=self.embeddings,
                cluster_centroids=self.cluster_centroids,
                cluster_labels=self.cluster_labels,
                speaker_col=self.speaker_col,
                party_col=self.party_col
            )
        
        # Generalism Index
        if self.is_feature_enabled('generalism_index'):
            logger.info("Computing generalism index...")
            result['generalism_index'] = compute_generalism_index(
                df=self.df,
                cluster_col=self.cluster_col,
                speaker_col=self.speaker_col,
                party_col=self.party_col
            )
        
        # Distinctive Keywords
        if self.is_feature_enabled('distinctive_keywords'):
            logger.info("Computing distinctive keywords...")
            result['distinctive_keywords'] = compute_distinctive_keywords(
                df=self.df,
                party_col=self.party_col,
                text_col=self.text_col
            )
        
        logger.info("Identity analysis complete")
        return result
