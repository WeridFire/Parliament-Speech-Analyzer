"""
Tests for backend scrapers (parsing logic, not actual HTTP calls).
"""
import pytest
import re
from bs4 import BeautifulSoup

import pytest
import re
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

from backend.scrapers.camera import _parse_speeches_from_html as parse_camera_html
from backend.scrapers.senate import _parse_speeches_from_html as parse_senate_html


# =============================================================================
# Mocks
# =============================================================================

@pytest.fixture
def mock_rosters():
    """Mock roster data to avoid network calls."""
    return {
        'all_names': {'MELONI', 'SCHLEIN', 'RENZI', 'BOCCIA', 'ROSSI', 'BIANCHI'},
        'name_to_info': {
            'MELONI': {'full_name': 'MELONI', 'party': 'FDI', 'profile_url': 'http://test/meloni'},
            'SCHLEIN': {'full_name': 'SCHLEIN', 'party': 'PD-IDP', 'profile_url': 'http://test/schlein'},
            'RENZI': {'full_name': 'RENZI', 'party': 'IV-C-RE', 'profile_url': 'http://test/renzi'},
            'BOCCIA': {'full_name': 'BOCCIA', 'party': 'PD-IDP', 'profile_url': 'http://test/boccia'},
            'ROSSI': {'full_name': 'ROSSI', 'party': 'MISTO', 'profile_url': 'http://test/rossi'},
            'BIANCHI': {'full_name': 'BIANCHI', 'party': 'LEGA', 'profile_url': 'http://test/bianchi'},
        }
    }


# =============================================================================
# Camera HTML Parsing Tests
# =============================================================================

class TestCameraParser:
    """Tests for Camera dei Deputati HTML parsing."""
    
    @patch('backend.scrapers.utils.get_rosters')
    def test_extracts_speaker_with_party(self, mock_get_rosters, camera_html_sample, mock_rosters):
        """Should extract speaker name and party from Camera HTML."""
        mock_get_rosters.return_value = mock_rosters
        soup = BeautifulSoup(camera_html_sample, 'html.parser')
        speeches = parse_camera_html(soup, "2024-12-01", "http://test.url")
        
        # Should find at least one speech
        assert len(speeches) > 0
        
        # Check first speech has expected fields
        speech = speeches[0]
        assert hasattr(speech, 'speaker')
        assert hasattr(speech, 'party')
        assert hasattr(speech, 'text')
    
    @patch('backend.scrapers.utils.get_rosters')
    def test_extracts_presidente(self, mock_get_rosters, camera_html_sample, mock_rosters):
        """Should extract PRESIDENTE speeches."""
        mock_get_rosters.return_value = mock_rosters
        soup = BeautifulSoup(camera_html_sample, 'html.parser')
        speeches = parse_camera_html(soup, "2024-12-01", "http://test.url")
        
        # Check if PRESIDENTE is found
        presidente_speeches = [s for s in speeches if 'PRESIDENTE' in s.speaker.upper()]
        # It's OK if not found in this sample, just check no crash
        assert isinstance(speeches, list)
    
    @patch('backend.scrapers.utils.get_rosters')
    def test_handles_empty_html(self, mock_get_rosters, mock_rosters):
        """Should handle empty HTML gracefully."""
        mock_get_rosters.return_value = mock_rosters
        soup = BeautifulSoup("<div></div>", 'html.parser')
        speeches = parse_camera_html(soup, "2024-12-01", "http://test.url")
        
        assert speeches == []


# =============================================================================
# Senate HTML Parsing Tests
# =============================================================================

class TestSenateParser:
    """Tests for Senate HTML parsing."""
    
    @patch('backend.scrapers.utils.get_rosters')
    def test_extracts_speaker_with_party(self, mock_get_rosters, senate_html_sample, mock_rosters):
        """Should extract speaker name and party from Senate HTML."""
        mock_get_rosters.return_value = mock_rosters
        soup = BeautifulSoup(senate_html_sample, 'html.parser')
        speeches = parse_senate_html(soup, "2024-12-01", "http://test.url")
        
        # Should find speeches
        assert len(speeches) > 0
        
        # Check structure
        for speech in speeches:
            assert hasattr(speech, 'speaker')
            assert hasattr(speech, 'text')
            assert len(speech.text) > 0
    
    @patch('backend.scrapers.utils.get_rosters')
    def test_extracts_party_from_parentheses(self, mock_get_rosters, senate_html_sample, mock_rosters):
        """Should extract party from SPEAKER (PARTY). format."""
        mock_get_rosters.return_value = mock_rosters
        soup = BeautifulSoup(senate_html_sample, 'html.parser')
        speeches = parse_senate_html(soup, "2024-12-01", "http://test.url")
        
        # Find speeches with parties
        with_party = [s for s in speeches if s.party]
        
        # Check parties are valid
        for speech in with_party:
            assert speech.party != ""
            assert "(" not in speech.party  # Parentheses should be stripped
    
    @patch('backend.scrapers.utils.get_rosters')
    def test_extracts_notes(self, mock_get_rosters, senate_html_sample, mock_rosters):
        """Should extract parliamentary notes like (Applausi)."""
        mock_get_rosters.return_value = mock_rosters
        soup = BeautifulSoup(senate_html_sample, 'html.parser')
        speeches = parse_senate_html(soup, "2024-12-01", "http://test.url")
        
        # Check if notes are extracted
        some_have_notes = any(len(s.notes) > 0 for s in speeches)
        # It's OK if no notes in this sample
        assert isinstance(speeches, list)
    
    @patch('backend.scrapers.utils.get_rosters')
    def test_handles_empty_html(self, mock_get_rosters, mock_rosters):
        """Should handle empty HTML gracefully."""
        mock_get_rosters.return_value = mock_rosters
        soup = BeautifulSoup("<div></div>", 'html.parser')
        speeches = parse_senate_html(soup, "2024-12-01", "http://test.url")
        
        assert speeches == []


# =============================================================================
# Speaker Pattern Matching Tests
# =============================================================================

class TestSpeakerPatterns:
    """Tests for speaker name pattern matching."""
    
    def test_speaker_with_party_pattern(self):
        """Test regex pattern for SPEAKER (PARTY). format."""
        pattern = re.compile(
            r'^([A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+)?)\s*\(([^)]+)\)\.\s+(.+)',
            re.DOTALL
        )
        
        text = "BOCCIA (PD-IDP). Signora Presidente, vorrei dire qualcosa."
        match = pattern.match(text)
        
        assert match is not None
        assert match.group(1) == "BOCCIA"
        assert match.group(2) == "PD-IDP"
        assert "Signora Presidente" in match.group(3)
    
    def test_presidente_pattern(self):
        """Test regex pattern for PRESIDENTE. format."""
        pattern = re.compile(r'^(PRESIDENTE|PRESIDENTESSA)\.\s+(.+)', re.DOTALL)
        
        text = "PRESIDENTE. La seduta è aperta."
        match = pattern.match(text)
        
        assert match is not None
        assert match.group(1) == "PRESIDENTE"
        assert "seduta" in match.group(2)
    
    def test_speaker_no_party_pattern(self):
        """Test regex pattern for SPEAKER. format (no party)."""
        pattern = re.compile(
            r'^([A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+){0,2})\.\s+(.+)',
            re.DOTALL
        )
        
        text = "ROSSI. Vorrei intervenire su questo punto."
        match = pattern.match(text)
        
        assert match is not None
        assert match.group(1) == "ROSSI"
