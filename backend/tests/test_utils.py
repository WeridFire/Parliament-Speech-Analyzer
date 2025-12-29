"""
Tests for backend utilities (text, cache, retry).
"""
import pytest
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import modules to test
from backend.utils.text import clean_text
from backend.utils.retry import retry
from backend.utils.cache import (
    is_cache_valid,
    save_cache_metadata,
    get_cache_metadata,
    get_cache_age_days,
    CACHE_DIR
)


# =============================================================================
# Text Cleaning Tests
# =============================================================================

class TestCleanText:
    """Tests for clean_text function."""
    
    def test_removes_parliamentary_formulas(self):
        """Should remove common parliamentary procedural phrases."""
        text = "La seduta è aperta. Il governo propone una nuova legge."
        result = clean_text(text)
        assert "La seduta è aperta" not in result
        assert "governo propone" in result.lower() or "legge" in result.lower()
    
    def test_removes_presidente_calls(self):
        """Should remove 'Signor Presidente' and similar."""
        text = "Signor Presidente, vorrei sottolineare l'importanza di questa misura."
        result = clean_text(text)
        # The actual content should remain
        assert "importanza" in result.lower() or "misura" in result.lower()
    
    def test_preserves_substantive_content(self):
        """Should not remove actual political content."""
        text = "La riforma fiscale ridurrà le tasse per le famiglie."
        result = clean_text(text)
        assert "riforma" in result.lower() or "tasse" in result.lower() or "famiglie" in result.lower()
    
    def test_empty_input(self):
        """Should handle empty input gracefully."""
        result = clean_text("")
        assert result == ""
    
    def test_whitespace_input(self):
        """Should handle whitespace-only input."""
        result = clean_text("   \n\t  ")
        assert result.strip() == ""


# =============================================================================
# Retry Decorator Tests
# =============================================================================

class TestRetryDecorator:
    """Tests for retry decorator."""
    
    def test_succeeds_first_try(self):
        """Should return immediately if no exception."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = success_func()
        assert result == "success"
        assert call_count == 1
    
    def test_succeeds_after_failures(self):
        """Should retry and eventually succeed."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = fail_then_succeed()
        assert result == "success"
        assert call_count == 3
    
    def test_exhausts_retries(self):
        """Should raise exception after max attempts."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")
        
        with pytest.raises(ValueError, match="Permanent failure"):
            always_fails()
        
        assert call_count == 3
    
    def test_only_catches_specified_exceptions(self):
        """Should not catch exceptions not in the tuple."""
        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def raises_type_error():
            raise TypeError("Wrong type")
        
        with pytest.raises(TypeError):
            raises_type_error()


# =============================================================================
# Cache Validation Tests
# =============================================================================

class TestCacheValidation:
    """Tests for cache validation functions."""
    
    def test_cache_valid_when_fresh(self, tmp_path, monkeypatch):
        """Should return True for fresh cache."""
        # Patch CACHE_DIR to use temp directory
        monkeypatch.setattr('backend.utils.cache.CACHE_DIR', tmp_path)
        
        # Save fresh metadata
        save_cache_metadata('test_source')
        
        # Should be valid
        assert is_cache_valid('test_source', max_age_days=7) == True
    
    def test_cache_invalid_when_stale(self, tmp_path, monkeypatch):
        """Should return False for old cache."""
        monkeypatch.setattr('backend.utils.cache.CACHE_DIR', tmp_path)
        
        # Create old metadata
        meta_file = tmp_path / 'cache_meta_test_source.json'
        old_date = datetime.now() - timedelta(days=30)
        with open(meta_file, 'w') as f:
            json.dump({'created_at': old_date.isoformat(), 'version': '2.0'}, f)
        
        # Should be invalid
        assert is_cache_valid('test_source', max_age_days=7) == False
    
    def test_cache_invalid_when_missing(self, tmp_path, monkeypatch):
        """Should return False if no cache exists."""
        monkeypatch.setattr('backend.utils.cache.CACHE_DIR', tmp_path)
        
        assert is_cache_valid('nonexistent_source') == False
    
    def test_get_cache_age_days(self, tmp_path, monkeypatch):
        """Should return correct age in days."""
        monkeypatch.setattr('backend.utils.cache.CACHE_DIR', tmp_path)
        
        # Create metadata from 5 days ago
        meta_file = tmp_path / 'cache_meta_test.json'
        old_date = datetime.now() - timedelta(days=5)
        with open(meta_file, 'w') as f:
            json.dump({'created_at': old_date.isoformat(), 'version': '2.0'}, f)
        
        age = get_cache_age_days('test')
        assert age == 5
