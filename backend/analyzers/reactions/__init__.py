"""
Reactions Analyzer Package - Applause and protests between groups.
"""
from .analyzer import ReactionsAnalyzer
from .applause import compute_reactions

__all__ = [
    'ReactionsAnalyzer',
    'compute_reactions',
]
