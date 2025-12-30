"""
Tests for Rhetoric Analyzer.

Tests:
- Rhetoric Patterns (populist, anti-establishment, emotional, institutional)
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestRhetoricAnalyzer:
    """Tests for RhetoricAnalyzer class."""
    
    def test_analyzer_registration(self):
        """Test that RhetoricAnalyzer is registered."""
        from backend.analyzers import AnalyzerRegistry
        
        assert 'rhetoric' in AnalyzerRegistry.names()
    
    def test_analyzer_compute(self, mock_data, analyzer_kwargs):
        """Test full analyzer computation."""
        from backend.analyzers.rhetoric import RhetoricAnalyzer
        
        analyzer = RhetoricAnalyzer(**analyzer_kwargs)
        result = analyzer.compute()
        
        assert isinstance(result, dict)
        assert 'by_speaker' in result
        assert 'by_party' in result


class TestRhetoricPatterns:
    """Tests for rhetoric pattern detection."""
    
    def test_compute_rhetoric_scores_single(self):
        """Test rhetoric scores on single text."""
        from backend.analyzers.rhetoric import compute_rhetoric_scores
        
        # Text with populist markers
        populist_text = "Il popolo è stato tradito dalla casta e dall'élite."
        result = compute_rhetoric_scores(populist_text)
        
        assert 'populist' in result
        assert 'anti_establishment' in result
        assert 'emotional' in result
        assert 'institutional' in result
        
        # Populist score should be higher
        assert result['populist'] > 0
    
    def test_rhetoric_scores_empty_text(self):
        """Test rhetoric scores on empty text."""
        from backend.analyzers.rhetoric import compute_rhetoric_scores
        
        result = compute_rhetoric_scores("")
        
        # Should return zeros without error
        assert all(v == 0 for v in result.values())
    
    def test_institutional_text(self):
        """Test institutional language detection."""
        from backend.analyzers.rhetoric import compute_rhetoric_scores
        
        inst_text = "La proposta di emendamento alla normativa è stata valutata dalla commissione."
        result = compute_rhetoric_scores(inst_text)
        
        assert result['institutional'] > 0
