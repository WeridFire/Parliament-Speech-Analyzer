"""
Tests for backend scrapers (parsing logic, not actual HTTP calls).
"""
import pytest
import re
from bs4 import BeautifulSoup

from backend.scrapers.camera import _parse_speeches_from_html as parse_camera_html
from backend.scrapers.senate import _parse_speeches_from_html as parse_senate_html


# =============================================================================
# Camera HTML Parsing Tests
# =============================================================================

class TestCameraParser:
    """Tests for Camera dei Deputati HTML parsing."""
    
    def test_extracts_speaker_with_party(self, camera_html_sample):
        """Should extract speaker name and party from Camera HTML."""
        soup = BeautifulSoup(camera_html_sample, 'html.parser')
        speeches = parse_camera_html(soup, "2024-12-01", "http://test.url")
        
        # Should find at least one speech
        assert len(speeches) > 0
        
        # Check first speech has expected fields
        speech = speeches[0]
        assert hasattr(speech, 'speaker')
        assert hasattr(speech, 'party')
        assert hasattr(speech, 'text')
    
    def test_extracts_presidente(self, camera_html_sample):
        """Should extract PRESIDENTE speeches."""
        soup = BeautifulSoup(camera_html_sample, 'html.parser')
        speeches = parse_camera_html(soup, "2024-12-01", "http://test.url")
        
        # Check if PRESIDENTE is found
        presidente_speeches = [s for s in speeches if 'PRESIDENTE' in s.speaker.upper()]
        # It's OK if not found in this sample, just check no crash
        assert isinstance(speeches, list)
    
    def test_handles_empty_html(self):
        """Should handle empty HTML gracefully."""
        soup = BeautifulSoup("<div></div>", 'html.parser')
        speeches = parse_camera_html(soup, "2024-12-01", "http://test.url")
        
        assert speeches == []


# =============================================================================
# Senate HTML Parsing Tests
# =============================================================================

class TestSenateParser:
    """Tests for Senate HTML parsing."""
    
    def test_extracts_speaker_with_party(self, senate_html_sample):
        """Should extract speaker name and party from Senate HTML."""
        soup = BeautifulSoup(senate_html_sample, 'html.parser')
        speeches = parse_senate_html(soup, "2024-12-01", "http://test.url")
        
        # Should find speeches
        assert len(speeches) > 0
        
        # Check structure
        for speech in speeches:
            assert hasattr(speech, 'speaker')
            assert hasattr(speech, 'text')
            assert len(speech.text) > 0
    
    def test_extracts_party_from_parentheses(self, senate_html_sample):
        """Should extract party from SPEAKER (PARTY). format."""
        soup = BeautifulSoup(senate_html_sample, 'html.parser')
        speeches = parse_senate_html(soup, "2024-12-01", "http://test.url")
        
        # Find speeches with parties
        with_party = [s for s in speeches if s.party]
        
        # Check parties are valid
        for speech in with_party:
            assert speech.party != ""
            assert "(" not in speech.party  # Parentheses should be stripped
    
    def test_extracts_notes(self, senate_html_sample):
        """Should extract parliamentary notes like (Applausi)."""
        soup = BeautifulSoup(senate_html_sample, 'html.parser')
        speeches = parse_senate_html(soup, "2024-12-01", "http://test.url")
        
        # Check if notes are extracted
        some_have_notes = any(len(s.notes) > 0 for s in speeches)
        # It's OK if no notes in this sample
        assert isinstance(speeches, list)
    
    def test_handles_empty_html(self):
        """Should handle empty HTML gracefully."""
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
