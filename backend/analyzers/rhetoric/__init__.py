"""
Rhetoric Analyzer Package - Speech style and rhetoric patterns.
"""
from .analyzer import RhetoricAnalyzer
from .patterns import (
    compute_rhetoric_scores, 
    add_rhetoric_scores, 
    classify_rhetorical_style,
    POPULIST_MARKERS,
    ANTI_ESTABLISHMENT_MARKERS,
    EMOTIONAL_INTENSIFIERS,
    INSTITUTIONAL_MARKERS
)

__all__ = [
    'RhetoricAnalyzer',
    'compute_rhetoric_scores',
    'add_rhetoric_scores',
    'classify_rhetorical_style',
]
