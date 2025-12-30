"""
Tests for the rosters module (deputy/senator whitelist validation).
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from backend.scrapers.rosters import (
    fetch_camera_roster,
    fetch_senato_roster,
    fetch_all_rosters,
    get_rosters,
    load_cached_rosters,
    save_rosters_cache,
    _normalize_name,
    ROSTER_CACHE_FILE
)


class TestNameNormalization:
    """Test name normalization for matching."""
    
    def test_normalize_uppercase(self):
        assert _normalize_name("MARIO ROSSI") == "Mario Rossi"
    
    def test_normalize_mixed_case(self):
        assert _normalize_name("Mario ROSSI") == "Mario ROSSI"  # Only normalizes if all caps
    
    def test_normalize_whitespace(self):
        assert _normalize_name("  Mario   Rossi  ") == "Mario Rossi"


class TestRosterCaching:
    """Test roster caching mechanism."""
    
    def test_save_and_load_cache(self, tmp_path, monkeypatch):
        # Use temp directory for cache
        temp_cache = tmp_path / "test_rosters.json"
        monkeypatch.setattr('backend.scrapers.rosters.ROSTER_CACHE_FILE', temp_cache)
        
        # Create test data
        test_rosters = {
            'camera': [{'full_name': 'Test Deputy', 'party': 'Test', 'profile_url': 'http://test', 'source': 'camera'}],
            'senato': [],
            'all_names': ['Test Deputy'],
            'name_to_info': {'Test Deputy': {'full_name': 'Test Deputy', 'party': 'Test', 'profile_url': 'http://test'}},
            'timestamp': datetime.now().isoformat(),
            'legislature': 19
        }
        
        # Save
        save_rosters_cache(test_rosters)
        assert temp_cache.exists()
        
        # Load
        loaded = load_cached_rosters()
        assert loaded is not None
        assert 'Test Deputy' in loaded['all_names']
    
    def test_cache_expiration(self, tmp_path, monkeypatch):
        # Use temp directory
        temp_cache = tmp_path / "expired_rosters.json"
        monkeypatch.setattr('backend.scrapers.rosters.ROSTER_CACHE_FILE', temp_cache)
        
        # Create expired cache (35 days old)
        old_timestamp = (datetime.now() - timedelta(days=35)).isoformat()
        expired_data = {
            'camera': [],
            'senato': [],
            'all_names': [],
            'name_to_info': {},
            'timestamp': old_timestamp,
            'legislature': 19
        }
        
        with open(temp_cache, 'w') as f:
            json.dump(expired_data, f)
        
        # Should return None for expired cache
        loaded = load_cached_rosters()
        assert loaded is None


class TestNameValidation:
    """Test validation logic in scrapers."""
    
    @patch('backend.scrapers.camera._get_rosters')
    def test_validate_deputy_in_roster(self, mock_get_rosters):
        from backend.scrapers.camera import _validate_and_enrich_deputy
        
        # Mock roster data
        mock_get_rosters.return_value = {
            'all_names': {'Mario Rossi', 'Luigi Verdi'},
            'name_to_info': {
                'Mario Rossi': {
                    'full_name': 'Mario Rossi',
                    'party': 'Partito Democratico',
                    'profile_url': 'http://camera.it/rossi'
                }
            }
        }
        
        result = _validate_and_enrich_deputy('MARIO ROSSI', 'PD')
        assert result is not None
        assert result['name'] == 'Mario Rossi'
        assert result['party'] == 'Partito Democratico'
        assert result['profile_url'] == 'http://camera.it/rossi'
    
    @patch('backend.scrapers.camera._get_rosters')
    def test_validate_deputy_not_in_roster(self, mock_get_rosters):
        from backend.scrapers.camera import _validate_and_enrich_deputy
        
        mock_get_rosters.return_value = {
            'all_names': {'Mario Rossi'},
            'name_to_info': {}
        }
        
        # Should return None for invalid name (false positives like "Concluso")
        result = _validate_and_enrich_deputy('Concluso', '')
        assert result is None
    
    @patch('backend.scrapers.camera._get_rosters')
    def test_validate_deputy_presidente_skipped(self, mock_get_rosters):
        from backend.scrapers.camera import _validate_and_enrich_deputy
        
        # PRESIDENTE should be skipped (not validated)
        result = _validate_and_enrich_deputy('PRESIDENTE', '')
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
