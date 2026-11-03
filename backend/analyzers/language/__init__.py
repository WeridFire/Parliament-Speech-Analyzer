"""
Language Analyzer Package - Readability and polarization of the phrasing.
"""
from .analyzer import LanguageAnalyzer
from .readability import compute_readability_scores
from .polarization import compute_polarization_scores

__all__ = [
    'LanguageAnalyzer',
    'compute_readability_scores',
    'compute_polarization_scores',
]
