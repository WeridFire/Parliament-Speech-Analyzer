"""
Blocs Analyzer Package - Majority and opposition compared.

Provides:
- Issue ownership: which bloc devotes more of its attention to each topic
- Bloc vocabulary: the words that separate the two sides
- Bloc summary: volume and length of interventions on each side
"""
from .analyzer import BlocsAnalyzer
from .ownership import compute_bloc_summary, compute_issue_ownership, compute_bloc_keywords

__all__ = [
    'BlocsAnalyzer',
    'compute_bloc_summary',
    'compute_issue_ownership',
    'compute_bloc_keywords',
]
