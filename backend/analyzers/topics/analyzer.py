"""
Topics Analyzer - Main analyzer class.
"""
import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .extraction import extract_cluster_topics
from .labeling import get_cluster_labels

logger = logging.getLogger(__name__)


@analyzer
class TopicsAnalyzer(BaseAnalyzer):
    """Analyzer for cluster topic extraction and labeling."""
    
    name = "topics"
    description = "Cluster topic extraction and labeling"
    version = "1.0"
    
    default_features = {}  # No sub-features
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        analyzer_config = self.config.get(self.name, {})
        self.use_pos_filtering = analyzer_config.get('use_pos_filtering', True)
        self.top_n_keywords = analyzer_config.get('top_n_keywords', 5)
    
    def compute(self) -> dict:
        """Compute topic extraction."""
        logger.info("Extracting cluster topics...")
        
        topics = extract_cluster_topics(
            df=self.df,
            text_col=self.text_col,
            cluster_col=self.cluster_col,
            top_n=self.top_n_keywords
        )
        
        labels = {cid: self._label_from_keywords(kw) for cid, kw in topics.items()}
        
        result = {
            'cluster_topics': topics,
            'cluster_labels': labels
        }
        
        logger.info("Topic extraction complete: %d clusters", len(topics))
        return result
    
    def _label_from_keywords(self, keywords: list[str]) -> str:
        """Generate label from keywords."""
        if not keywords:
            return "Unknown"
        label_words = keywords[:min(3, len(keywords))]
        return " / ".join(word.title() for word in label_words)
