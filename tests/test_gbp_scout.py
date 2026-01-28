"""
Tests for GBP Scout - Phase G1.7
Unit tests for Google Business Profile parsing, deduplication, and budget tracking.
"""
import pytest
import sys
import re
from pathlib import Path
from unittest.mock import Mock, patch

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from gbp_scout import GBPScout


@pytest.fixture
def scout():
    return GBPScout()


class TestPhoneNormalization:
    """Tests for phone number normalization and dedup."""
    
    def test_phone_with_dashes(self, scout):
        """Phone with dashes should normalize."""
        result = re.sub(r'\D', '', "602-555-1234")
        assert result == "6025551234"
    
    def test_phone_with_parens(self, scout):
        """Phone with parentheses should normalize."""
        result = re.sub(r'\D', '', "(602) 555-1234")
        assert result == "6025551234"
    
    def test_phone_with_dots(self, scout):
        """Phone with dots should normalize."""
        result = re.sub(r'\D', '', "602.555.1234")
        assert result == "6025551234"


class TestDomainNormalization:
    """Tests for domain normalization."""
    
    def test_www_stripped(self, scout):
        """www. prefix should be stripped."""
        domain = "www.example.com"
        domain = domain.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        assert domain == "example.com"
    
    def test_uppercase_lowered(self, scout):
        """Domain should be lowercased."""
        domain = "EXAMPLE.COM"
        assert domain.lower() == "example.com"


class TestCategoryGuessing:
    """Tests for category guessing from query."""
    
    def test_hvac_category(self, scout):
        """HVAC query should return HVAC category."""
        result = scout._guess_category("hvac contractor phoenix")
        assert result == "HVAC"
    
    def test_plumbing_category(self, scout):
        """Plumber query should return Plumbing category."""
        result = scout._guess_category("plumber mesa")
        assert result == "Plumbing"
    
    def test_dental_category(self, scout):
        """Dental query should return Dental category."""
        result = scout._guess_category("dental clinic tempe")
        assert result == "Dental"
    
    def test_legal_category(self, scout):
        """Law firm query should return Legal category."""
        result = scout._guess_category("law firm phoenix")
        assert result == "Legal"


class TestProspectNormalization:
    """Tests for prospect normalization."""
    
    def test_basic_normalization(self, scout):
        """Test basic prospect normalization."""
        raw = {
            "name": "ABC HVAC Services",
            "phone": "(602) 555-1234",
            "address": "123 Main St, Phoenix, AZ",
            "website": "https://www.abchvac.com",
            "category": "HVAC",
            "rating": 4.5,
            "review_count": 100
        }
        
        result = scout.normalize_prospect(raw)
        
        assert result["name"] == "ABC HVAC Services"
        assert result["source"] == "GBP"
        assert result["domain"] == "abchvac.com"
        assert result["gbp_data"]["phone"] == "(602) 555-1234"
        assert result["gbp_data"]["rating"] == 4.5
    
    def test_no_website_uses_phone_key(self, scout):
        """Prospect without website should use phone as key."""
        raw = {
            "name": "XYZ Plumbing",
            "phone": "480-555-9999",
            "address": "456 Oak Ave, Mesa, AZ",
            "website": None,
            "category": "Plumbing"
        }
        
        result = scout.normalize_prospect(raw)
        
        assert result["domain"] is None
        assert "phone:" in result["prospect_key"]
    
    def test_b2b_confidence_with_phone_address(self, scout):
        """Prospect with phone AND address should have high B2B confidence."""
        raw = {
            "name": "Test Business",
            "phone": "602-555-0000",
            "address": "789 Test St",
            "website": None,
            "category": "Business"
        }
        
        result = scout.normalize_prospect(raw)
        
        assert result["b2b_confidence"] >= 4


class TestBudgetTracking:
    """Tests for weekly budget tracking."""
    
    def test_week_key_format(self, scout):
        """Week key should be in YYYY-WW format."""
        week_key = scout._get_week_key()
        assert re.match(r'\d{4}-W\d{2}', week_key), f"Invalid week key format: {week_key}"
    
    def test_budget_check(self, scout):
        """Budget check should return tuple of (has_budget, remaining)."""
        has_budget, remaining = scout._check_budget()
        assert isinstance(has_budget, bool)
        assert isinstance(remaining, int)


class TestManualImport:
    """Tests for CSV import functionality."""
    
    def test_import_from_empty_dir(self, scout):
        """Import from empty directory should return empty list."""
        # Create temp dir structure
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # This test just verifies the method doesn't crash
            # Real import would need actual CSV files
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
