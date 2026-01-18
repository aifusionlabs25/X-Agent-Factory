"""
Phase 13: Intake Packager Tests
Tests the intake packager using a saved HTML fixture instead of live network calls.

Usage:
    pytest tests/test_intake_packager.py -v
"""
import os
import sys
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from intake_packager import (
    compute_slug,
    extract_metadata,
    extract_main_content,
    infer_industry,
    infer_pain_points,
    build_dossier,
    run_intake
)
from schema_validator import validate_dossier


class TestIntakePackagerHelpers:
    """Unit tests for helper functions."""
    
    def test_compute_slug_simple(self):
        """Test slug generation from simple name."""
        assert compute_slug("Acme Solar") == "acme_solar"
    
    def test_compute_slug_with_punctuation(self):
        """Test slug handles punctuation."""
        assert compute_slug("Bob's HVAC & Plumbing!") == "bobs_hvac_plumbing"
    
    def test_compute_slug_empty(self):
        """Test slug with empty string."""
        assert compute_slug("") == "unknown_client"
    
    def test_infer_industry_hvac(self):
        """Test industry inference for HVAC content."""
        content = "We provide heating and cooling services for commercial buildings."
        assert infer_industry(content, "example.com") == "HVAC"
    
    def test_infer_industry_solar(self):
        """Test industry inference for solar content."""
        content = "Our solar panel installations reduce your energy costs."
        assert infer_industry(content, "example.com") == "Solar"
    
    def test_infer_industry_default(self):
        """Test default industry for unrecognized content."""
        content = "We sell widgets and gadgets."
        assert infer_industry(content, "example.com") == "General Services"
    
    def test_infer_pain_points_returns_list(self):
        """Test pain points returns non-empty list."""
        points = infer_pain_points("HVAC")
        assert isinstance(points, list)
        assert len(points) >= 1
        assert all(isinstance(p, str) for p in points)


class TestIntakePackagerWithFixture:
    """Integration tests using HTML fixture."""
    
    FIXTURE_PATH = Path(__file__).parent / "fixtures" / "acmesolar.html"
    OUTPUT_SLUG = "acmesolar_commercial_solar_solutions"
    OUTPUT_DIR = Path(__file__).parent.parent / "ingested_clients" / OUTPUT_SLUG
    
    @classmethod
    def setup_class(cls):
        """Load fixture and clean previous test output."""
        if cls.OUTPUT_DIR.exists():
            shutil.rmtree(cls.OUTPUT_DIR)
        
        with open(cls.FIXTURE_PATH, 'r', encoding='utf-8') as f:
            cls.fixture_html = f.read()
    
    @classmethod
    def teardown_class(cls):
        """Clean up after tests (optional - keep for inspection)."""
        # Uncomment to enable cleanup:
        # if cls.OUTPUT_DIR.exists():
        #     shutil.rmtree(cls.OUTPUT_DIR)
        pass
    
    def test_extract_metadata_from_fixture(self):
        """Test metadata extraction from HTML fixture."""
        metadata = extract_metadata(self.fixture_html, "https://acmesolar.com")
        
        assert metadata["title"] == "AcmeSolar - Commercial Solar Solutions"
        assert "commercial solar" in metadata["description"].lower()
        assert metadata["domain"] == "acmesolar.com"
    
    def test_extract_main_content(self):
        """Test main content extraction."""
        content = extract_main_content(self.fixture_html)
        
        assert "solar" in content.lower()
        assert "energy" in content.lower()
    
    def test_build_dossier_from_fixture(self):
        """Test dossier building from fixture data."""
        metadata = extract_metadata(self.fixture_html, "https://acmesolar.com")
        content = extract_main_content(self.fixture_html)
        
        dossier = build_dossier(metadata, content, ["https://acmesolar.com"])
        
        # Check required fields exist
        assert "schema_version" in dossier
        assert "client_profile" in dossier
        assert "target_audience" in dossier
        assert "value_proposition" in dossier
        assert "offer" in dossier
        
        # Check industry inference
        assert dossier["client_profile"]["industry"] == "Solar"
    
    def test_full_intake_with_mocked_fetch(self):
        """Test full intake pipeline with mocked network call."""
        
        def mock_fetch(url, session=None):
            return self.fixture_html
        
        with patch('intake_packager.fetch_page', mock_fetch):
            success = run_intake("https://acmesolar.com")
        
        assert success, "Intake should succeed with fixture"
    
    def test_dossier_validates_against_schema(self):
        """Verify generated dossier passes schema validation."""
        # Find the dossier (may have different slug based on title parsing)
        ingested_dir = Path(__file__).parent.parent / "ingested_clients"
        dossier_files = list(ingested_dir.glob("acme*/dossier.json"))
        
        assert len(dossier_files) >= 1, "Dossier file not found"
        
        valid, error = validate_dossier(str(dossier_files[0]))
        assert valid, f"Dossier validation failed: {error}"
    
    def test_dossier_has_tbd_for_unknown_fields(self):
        """Verify unknown fields are marked TBD per policy."""
        ingested_dir = Path(__file__).parent.parent / "ingested_clients"
        dossier_files = list(ingested_dir.glob("acme*/dossier.json"))
        
        assert len(dossier_files) >= 1, "Dossier file not found"
        
        with open(dossier_files[0], 'r', encoding='utf-8') as f:
            dossier = json.load(f)
        
        # Region should be TBD (cannot infer from content alone)
        assert dossier["client_profile"]["region"] == "TBD"
        
        # metric_proof should be TBD
        assert "TBD" in dossier["value_proposition"]["metric_proof"]
    
    def test_source_bundle_exists(self):
        """Verify source_bundle.md was created."""
        ingested_dir = Path(__file__).parent.parent / "ingested_clients"
        bundle_files = list(ingested_dir.glob("acme*/extracted/source_bundle.md"))
        
        assert len(bundle_files) >= 1, "Source bundle not found"
        assert bundle_files[0].stat().st_size > 0, "Source bundle is empty"
    
    def test_intake_notes_exists(self):
        """Verify intake_notes.md was created."""
        ingested_dir = Path(__file__).parent.parent / "ingested_clients"
        notes_files = list(ingested_dir.glob("acme*/intake_notes.md"))
        
        assert len(notes_files) >= 1, "Intake notes not found"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
