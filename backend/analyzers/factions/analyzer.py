"""
Factions Analyzer - Main analyzer class.
"""
import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .conformity import compute_senator_conformity, get_all_factions

logger = logging.getLogger(__name__)


@analyzer
class FactionsAnalyzer(BaseAnalyzer):
    """Analyzer for internal party divisions."""
    
    name = "factions"
    description = "Internal party divisions and factions"
    version = "1.0"
    
    default_features = {
        'conformity': True,
        'faction_detection': True,
    }
    
    @classmethod
    def get_dependencies(cls) -> list[str]:
        return ['embeddings']
    
    def compute(self) -> dict:
        """Compute faction analysis."""
        logger.info("Computing faction analysis...")
        
        result = {}
        
        if self.is_feature_enabled('conformity'):
            conformity_df = compute_senator_conformity(
                df=self.df,
                embeddings=self.embeddings,
                speaker_col=self.speaker_col,
                party_col=self.party_col
            )
            
            # Convert to dict for JSON
            result['conformity'] = conformity_df.to_dict('records') if not conformity_df.empty else []
        
        if self.is_feature_enabled('faction_detection'):
            result['by_party'] = get_all_factions(self.df, self.embeddings)
        
        logger.info("Faction analysis complete")
        return result
