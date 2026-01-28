"""
Tests for Prospect Enricher - Phase G1.6
Unit tests for persona classifier, ICP lane matching, and denylist expansion.
"""
import pytest
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from prospect_enricher import ProspectEnricher


@pytest.fixture
def enricher():
    return ProspectEnricher()


class TestPersonaClassifier:
    """Unit tests for BUYER/AGENCY/VENDOR/CREATOR classification."""
    
    def test_agency_detection(self, enricher):
        """Test that agency markers trigger AGENCY persona."""
        agency_html = """
        We are a full-service marketing agency helping clients grow.
        Book a call with our team. View our case studies.
        """
        persona, reasons = enricher.classify_persona(agency_html, "")
        assert persona == "AGENCY", f"Expected AGENCY, got {persona}"
        assert len(reasons) >= 2, "Should have at least 2 reasons"
    
    def test_vendor_detection(self, enricher):
        """Test that vendor markers trigger VENDOR persona."""
        vendor_html = """
        Our SaaS platform provides API integrations for developers.
        Try our free trial today. See pricing tiers.
        """
        persona, reasons = enricher.classify_persona(vendor_html, "")
        assert persona == "VENDOR", f"Expected VENDOR, got {persona}"
    
    def test_creator_detection(self, enricher):
        """Test that creator markers trigger CREATOR persona."""
        creator_html = """
        Welcome to my YouTube channel and podcast!
        Subscribe for weekly content. Newsletter signup.
        """
        persona, reasons = enricher.classify_persona(creator_html, "")
        assert persona == "CREATOR", f"Expected CREATOR, got {persona}"
    
    def test_buyer_detection(self, enricher):
        """Test that local business signals trigger BUYER persona."""
        buyer_html = """
        Our Services - HVAC repair, installation, maintenance.
        Contact us today. Serving the Austin area.
        Call (512) 555-1234 for a free estimate.
        """
        persona, reasons = enricher.classify_persona(buyer_html, "")
        assert persona == "BUYER", f"Expected BUYER, got {persona}"
        assert "has_services" in reasons or "has_local_signals" in reasons
    
    def test_unknown_fallback(self, enricher):
        """Test that insufficient signals return UNKNOWN."""
        minimal_html = "<html><body>Hello world</body></html>"
        persona, reasons = enricher.classify_persona(minimal_html, "")
        assert persona == "UNKNOWN", f"Expected UNKNOWN, got {persona}"


class TestDenylistExpansion:
    """Regression tests for denylist URL expansion."""
    
    def test_cal_com_is_denylist(self, enricher):
        """cal.com should be in denylist."""
        assert enricher.is_denylist_domain("cal.com") is True
    
    def test_buymeacoffee_is_denylist(self, enricher):
        """buymeacoffee.com should be in denylist."""
        assert enricher.is_denylist_domain("buymeacoffee.com") is True
    
    def test_linktree_is_denylist(self, enricher):
        """linktr.ee should be in denylist."""
        assert enricher.is_denylist_domain("linktr.ee") is True
    
    def test_blogspot_subdomain_is_denylist(self, enricher):
        """Blogspot subdomains should be in denylist."""
        assert enricher.is_denylist_domain("example.blogspot.com") is True
    
    def test_real_business_not_denylist(self, enricher):
        """Real business domains should NOT be in denylist."""
        assert enricher.is_denylist_domain("johnsplumbing.com") is False
        assert enricher.is_denylist_domain("acmehvac.com") is False


class TestDomainCanonicalization:
    """Tests for domain normalization."""
    
    def test_www_stripped(self, enricher):
        """www. prefix should be stripped."""
        assert enricher.canonicalize_domain("www.example.com") == "example.com"
    
    def test_lowercase(self, enricher):
        """Domain should be lowercased."""
        assert enricher.canonicalize_domain("EXAMPLE.COM") == "example.com"
    
    def test_path_stripped(self, enricher):
        """Path should be stripped."""
        assert enricher.canonicalize_domain("example.com/page") == "example.com"


class TestICPLaneMatching:
    """Tests for ICP lane matching."""
    
    def test_home_services_match(self, enricher):
        """Home services keywords should match lane."""
        html = "We provide HVAC repair, plumbing, and electrical services."
        lane, boost = enricher.match_icp_lane(html, "")
        assert lane == "home_services_owner_operator", f"Expected home_services, got {lane}"
        assert boost > 0
    
    def test_medical_dental_match(self, enricher):
        """Dental/medical keywords should match lane."""
        html = "Our dental practice offers orthodontics and general dentistry."
        lane, boost = enricher.match_icp_lane(html, "")
        assert lane == "medical_dental_practice", f"Expected medical_dental, got {lane}"
    
    def test_negative_keywords_disqualify(self, enricher):
        """Negative keywords should disqualify from lane."""
        html = "Our marketing agency helps HVAC companies with SEO."
        lane, boost = enricher.match_icp_lane(html, "")
        # Should NOT match home_services due to "agency" negative
        assert lane != "home_services_owner_operator"


class TestB2BBoostCalculation:
    """Tests for B2B boost calculation."""
    
    def test_business_buyer_gets_boost(self, enricher):
        """BUSINESS site + BUYER persona should get positive boost."""
        enrichment = {
            "site_type": "BUSINESS",
            "persona_type": "BUYER",
            "has_phone": True,
            "has_contact_page": True,
            "has_address": True,
            "services_detected": ["repair", "installation"],
            "icp_boost": 2
        }
        boost, reasons = enricher.calculate_b2b_boost(enrichment)
        assert boost > 0, f"Expected positive boost, got {boost}"
    
    def test_agency_gets_penalty(self, enricher):
        """AGENCY persona should get penalty."""
        enrichment = {
            "site_type": "BUSINESS",
            "persona_type": "AGENCY",
            "has_phone": True,
            "icp_boost": 0
        }
        boost, reasons = enricher.calculate_b2b_boost(enrichment)
        # Agency penalty should reduce overall boost
        assert any("AGENCY" in r for r in reasons)
    
    def test_blog_gets_penalty(self, enricher):
        """BLOG site should get penalty."""
        enrichment = {
            "site_type": "BLOG",
            "persona_type": "UNKNOWN",
            "has_phone": False,
            "icp_boost": 0
        }
        boost, reasons = enricher.calculate_b2b_boost(enrichment)
        assert boost < 0, f"Expected negative boost for blog, got {boost}"


class TestGoldenSample:
    """Golden sample tests for expected classification."""
    
    def test_local_hvac_is_buyer(self, enricher):
        """Local HVAC company should be classified as BUYER."""
        html = """
        ABC HVAC Services
        Heating, Cooling, Air Conditioning Repair
        Serving the greater Phoenix area since 1985.
        Call us: (602) 555-1234
        Contact our team for a free estimate.
        123 Main Street, Phoenix, AZ 85001
        """
        persona, reasons = enricher.classify_persona(html, "Family owned HVAC company")
        assert persona == "BUYER", f"Local HVAC should be BUYER, got {persona}"
    
    def test_marketing_agency_is_agency(self, enricher):
        """Marketing agency should be classified as AGENCY."""
        html = """
        We help businesses grow with SEO and lead generation.
        Our clients include Fortune 500 companies.
        Book a call to discuss your marketing strategy.
        Case studies available on request.
        """
        persona, reasons = enricher.classify_persona(html, "Marketing agency")
        assert persona == "AGENCY", f"Marketing agency should be AGENCY, got {persona}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
