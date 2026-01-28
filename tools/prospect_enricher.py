"""
Prospect Enricher - Growth Department (Phase G1.6)
Verifies domains, classifies personas, and matches ICP lanes.

NOVA SPEC G1.6 COMPLIANCE:
- Buyer vs Agency vs Vendor classifier
- ICP Lane matching (home_services, medical, legal, property)
- Domain canonicalization
- Evidence signals and penalties tracking
"""
import os
import re
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from urllib.parse import urlparse

import requests
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
CONFIG_PATH = Path(__file__).parent.parent / "growth" / "config.yaml"
CACHE_DIR = Path(__file__).parent.parent / "growth" / "cache" / "enrichment"
CACHE_TTL_HOURS = 24


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


CONFIG = load_config()

# Industry keywords for detection
INDUSTRY_KEYWORDS = {
    "HVAC": ["hvac", "heating", "cooling", "air conditioning", "furnace"],
    "Plumbing": ["plumbing", "plumber", "drain", "sewer", "water heater"],
    "Electrical": ["electrical", "electrician", "wiring"],
    "Roofing": ["roofing", "roof repair", "roofer", "shingles"],
    "Pest Control": ["pest control", "exterminator", "termite"],
    "Cleaning": ["cleaning", "janitorial", "maid service"],
    "Landscaping": ["landscaping", "lawn care", "lawn service"],
    "Dental": ["dental", "dentist", "dentistry", "orthodontics"],
    "Legal": ["law firm", "attorney", "lawyer", "legal services"],
    "Medical": ["medical", "clinic", "healthcare", "doctor"],
    "Veterinary": ["veterinary", "vet", "animal hospital"],
    "Towing": ["towing", "tow truck", "roadside"],
    "Property Management": ["property management", "rentals", "apartments"],
    "Contractor": ["contractor", "construction", "remodeling"]
}

# US States for location detection
US_STATES = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming"
]


class ProspectEnricher:
    """Phase G1.6: Enrich prospects with buyer classification and ICP matching."""
    
    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # Load config
        self.icp_lanes = CONFIG.get("icp_lanes", {})
        self.persona_markers = CONFIG.get("persona_markers", {})
        self.domain_denylist = set(CONFIG.get("domain_denylist", []))
        self.buyer_scoring = CONFIG.get("buyer_scoring", {})
    
    def canonicalize_domain(self, domain: str) -> str:
        """Normalize domain: strip www, lowercase, remove tracking."""
        if not domain:
            return domain
        domain = domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        # Remove trailing slashes or paths
        domain = domain.split("/")[0]
        return domain
    
    def is_denylist_domain(self, domain: str) -> bool:
        """Check if domain is in denylist."""
        if not domain:
            return False
        canonical = self.canonicalize_domain(domain)
        # Check exact match
        if canonical in self.domain_denylist:
            return True
        # Check suffix match (e.g., blogspot.com)
        for denylist in self.domain_denylist:
            if canonical.endswith(denylist):
                return True
        return False
    
    def _get_cache_path(self, domain: str) -> Path:
        domain_hash = hashlib.md5(domain.encode()).hexdigest()
        return CACHE_DIR / f"{domain_hash}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        if not cache_path.exists():
            return False
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < timedelta(hours=CACHE_TTL_HOURS)
    
    def _load_cache(self, cache_path: Path) -> Optional[Dict]:
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def _save_cache(self, cache_path: Path, data: Dict):
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Enrichment cache write failed: {e}")
    
    # ========================================
    # PHASE G1.6: PERSONA CLASSIFICATION
    # ========================================
    
    def classify_persona(self, html: str, bio: str = "") -> Tuple[str, List[str]]:
        """
        Classify persona type: BUYER, AGENCY, VENDOR, CREATOR, UNKNOWN
        Returns (persona_type, reasons)
        """
        text = (html + " " + bio).lower()
        reasons = []
        
        # Check AGENCY markers
        agency_markers = self.persona_markers.get("agency", [])
        agency_matches = [m for m in agency_markers if m.lower() in text]
        if len(agency_matches) >= 2:
            reasons = [f"agency:{m}" for m in agency_matches[:3]]
            return "AGENCY", reasons
        
        # Check VENDOR markers
        vendor_markers = self.persona_markers.get("vendor", [])
        vendor_matches = [m for m in vendor_markers if m.lower() in text]
        if len(vendor_matches) >= 2:
            reasons = [f"vendor:{m}" for m in vendor_matches[:3]]
            return "VENDOR", reasons
        
        # Check CREATOR markers
        creator_markers = self.persona_markers.get("creator", [])
        creator_matches = [m for m in creator_markers if m.lower() in text]
        if len(creator_matches) >= 2:
            reasons = [f"creator:{m}" for m in creator_matches[:3]]
            return "CREATOR", reasons
        
        # Check BUYER signals (service catalog + local signals)
        has_services = any(s in text for s in ["services", "our services", "what we do", "we offer"])
        has_local = any(l in text for l in ["service area", "serving", "hours", "location", "address"])
        has_contact = "contact" in text
        has_phone = bool(re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', html))
        
        buyer_signals = []
        if has_services:
            buyer_signals.append("has_services")
        if has_local:
            buyer_signals.append("has_local_signals")
        if has_contact:
            buyer_signals.append("has_contact")
        if has_phone:
            buyer_signals.append("has_phone")
        
        # BUYER requires 2+ buyer signals and <2 agency/vendor signals
        if len(buyer_signals) >= 2 and len(agency_matches) < 2 and len(vendor_matches) < 2:
            return "BUYER", buyer_signals
        
        return "UNKNOWN", []
    
    # ========================================
    # PHASE G1.6: ICP LANE MATCHING
    # ========================================
    
    def match_icp_lane(self, html: str, bio: str = "") -> Tuple[Optional[str], int]:
        """
        Match prospect to ICP lane.
        Returns (lane_name, score_boost)
        """
        text = (html + " " + bio).lower()
        
        best_lane = None
        best_score = 0
        best_matches = 0
        
        for lane_name, lane_config in self.icp_lanes.items():
            positive_kw = lane_config.get("positive_keywords", [])
            negative_kw = lane_config.get("negative_keywords", [])
            score_boost = lane_config.get("score_boost", 0)
            
            # Count positive matches
            positive_matches = sum(1 for kw in positive_kw if kw.lower() in text)
            
            # Check for negative matches (disqualifies)
            has_negative = any(kw.lower() in text for kw in negative_kw)
            
            if positive_matches >= 2 and not has_negative:
                if positive_matches > best_matches:
                    best_lane = lane_name
                    best_score = score_boost
                    best_matches = positive_matches
        
        return best_lane, best_score
    
    # ========================================
    # ENRICHMENT MAIN
    # ========================================
    
    def enrich(self, domain: str, bio: str = "") -> Dict:
        """
        Enrich a domain with website verification, persona classification, and ICP matching.
        """
        if not domain:
            return self._empty_enrichment("no_domain")
        
        # Canonicalize domain
        domain = self.canonicalize_domain(domain)
        
        # Check cache
        cache_path = self._get_cache_path(domain)
        cached = self._load_cache(cache_path)
        if cached:
            return cached
        
        # Check denylist
        if self.is_denylist_domain(domain):
            result = self._empty_enrichment("denylist_domain")
            result["site_type"] = "LINKHUB"
            result["site_reason"] = f"Domain in denylist: {domain}"
            result["persona_type"] = "UNKNOWN"
            self._save_cache(cache_path, result)
            return result
        
        # Fetch and analyze
        try:
            result = self._fetch_and_analyze(domain, bio)
            self._save_cache(cache_path, result)
            return result
        except Exception as e:
            logger.warning(f"Enrichment failed for {domain}: {e}")
            result = self._empty_enrichment(f"fetch_error:{type(e).__name__}")
            self._save_cache(cache_path, result)
            return result
    
    def _fetch_and_analyze(self, domain: str, bio: str = "") -> Dict:
        """Fetch domain homepage and analyze."""
        url = f"https://{domain}/"
        
        try:
            resp = self.session.get(url, timeout=10, allow_redirects=True)
            status_code = resp.status_code
            final_url = resp.url
            content_type = resp.headers.get("Content-Type", "")
            
            if status_code != 200:
                return self._empty_enrichment(f"http_{status_code}")
            
            if "text/html" not in content_type.lower():
                return self._empty_enrichment(f"non_html")
            
            html = resp.text[:50000]
            html_lower = html.lower()
            
            # Extract signals
            page_title = self._extract_title(html)
            has_phone = self._detect_phone(html)
            has_email = self._detect_email(html)
            has_contact_page = self._detect_contact_page(html_lower)
            has_address = self._detect_address(html_lower)
            industry_hint = self._detect_industry(html_lower)
            location_hint = self._detect_location(html_lower)
            services_detected = self._extract_services(html_lower)
            
            # G1.6: Classify site type
            site_type, site_reason = self._classify_site(domain, html_lower, has_contact_page, services_detected)
            
            # G1.6: Classify persona
            persona_type, persona_reasons = self.classify_persona(html, bio)
            
            # G1.6: Match ICP lane
            icp_lane, icp_boost = self.match_icp_lane(html, bio)
            
            # Build evidence signals list
            evidence_signals = []
            if has_phone:
                evidence_signals.append("phone_found")
            if has_email:
                evidence_signals.append("email_found")
            if has_contact_page:
                evidence_signals.append("contact_page")
            if has_address:
                evidence_signals.append("address_found")
            if services_detected:
                evidence_signals.append("services_listed")
            if industry_hint:
                evidence_signals.append(f"industry:{industry_hint}")
            if icp_lane:
                evidence_signals.append(f"icp:{icp_lane}")
            
            # Build penalties list
            penalties = []
            if persona_type == "AGENCY":
                penalties.append("agency_detected")
            if persona_type == "VENDOR":
                penalties.append("vendor_detected")
            if persona_type == "CREATOR":
                penalties.append("creator_detected")
            if site_type == "BLOG":
                penalties.append("blog_site")
            
            return {
                "status": "success",
                "site_type": site_type,
                "site_reason": site_reason,
                "persona_type": persona_type,
                "persona_reasons": persona_reasons,
                "icp_lane": icp_lane,
                "icp_boost": icp_boost,
                "final_url": final_url,
                "status_code": status_code,
                "page_title": page_title,
                "has_phone": has_phone,
                "has_email": has_email,
                "has_contact_page": has_contact_page,
                "has_address": has_address,
                "industry_hint": industry_hint,
                "location_hint": location_hint,
                "services_detected": services_detected,
                "evidence_signals": evidence_signals[:5],
                "penalties": penalties[:3],
                "enriched_at": datetime.now().isoformat()
            }
            
        except requests.exceptions.SSLError:
            return self._empty_enrichment("ssl_error")
        except requests.exceptions.Timeout:
            return self._empty_enrichment("timeout")
        except requests.exceptions.ConnectionError:
            return self._empty_enrichment("connection_error")
    
    def _empty_enrichment(self, reason: str) -> Dict:
        return {
            "status": "failed",
            "site_type": "UNKNOWN",
            "site_reason": reason,
            "persona_type": "UNKNOWN",
            "persona_reasons": [],
            "icp_lane": None,
            "icp_boost": 0,
            "final_url": None,
            "status_code": None,
            "page_title": None,
            "has_phone": False,
            "has_email": False,
            "has_contact_page": False,
            "has_address": False,
            "industry_hint": None,
            "location_hint": None,
            "services_detected": [],
            "evidence_signals": [],
            "penalties": [],
            "enriched_at": datetime.now().isoformat()
        }
    
    def _extract_title(self, html: str) -> Optional[str]:
        match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:100]
        return None
    
    def _detect_phone(self, html: str) -> bool:
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',
            r'tel:\+?\d+',
        ]
        for pattern in patterns:
            if re.search(pattern, html):
                return True
        return False
    
    def _detect_email(self, html: str) -> bool:
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|net|org|biz|info|co|us|io)'
        match = re.search(pattern, html)
        if match:
            email = match.group(0).lower()
            if not any(x in email for x in ["example", "test", "noreply"]):
                return True
        return False
    
    def _detect_contact_page(self, html_lower: str) -> bool:
        indicators = ['href="/contact"', 'href="contact"', '/contact-us', '>contact</a>']
        return any(ind in html_lower for ind in indicators)
    
    def _detect_address(self, html_lower: str) -> bool:
        """Detect physical address presence."""
        # ZIP code patterns, street indicators
        has_zip = bool(re.search(r'\b\d{5}(-\d{4})?\b', html_lower))
        has_street = any(s in html_lower for s in ["street", "ave", "avenue", "blvd", "drive", "road", "suite"])
        return has_zip or has_street
    
    def _detect_industry(self, html_lower: str) -> Optional[str]:
        for industry, keywords in INDUSTRY_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in html_lower)
            if count >= 2:
                return industry
        return None
    
    def _detect_location(self, html_lower: str) -> Optional[str]:
        for state in US_STATES:
            if state in html_lower:
                return state.title()
        return None
    
    def _extract_services(self, html_lower: str) -> List[str]:
        services = []
        service_terms = [
            "repair", "installation", "maintenance", "emergency service",
            "residential", "commercial", "24/7", "same day", "free estimate"
        ]
        for term in service_terms:
            if term in html_lower:
                services.append(term)
        return services[:5]
    
    def _classify_site(self, domain: str, html_lower: str,
                       has_contact: bool, services: List[str]) -> Tuple[str, str]:
        """Classify site type."""
        # Check for vendor markers
        vendor_markers = ["platform", "saas", "api", "integrations", "pricing tiers", "developers"]
        vendor_count = sum(1 for m in vendor_markers if m in html_lower)
        if vendor_count >= 3:
            return "VENDOR", f"vendor_markers:{vendor_count}"
        
        # Check for blog indicators
        blog_indicators = ["blog", "post", "article", "read more", "comments"]
        blog_count = sum(1 for b in blog_indicators if b in html_lower)
        if blog_count >= 3 and not has_contact:
            return "BLOG", f"blog_indicators:{blog_count}"
        
        # Check for business indicators
        biz_nav = ["services", "about", "contact", "locations", "pricing"]
        biz_count = sum(1 for b in biz_nav if b in html_lower)
        
        if biz_count >= 3 and has_contact:
            return "BUSINESS", f"nav_indicators:{biz_count}"
        
        if len(services) >= 2 and has_contact:
            return "BUSINESS", f"services:{len(services)}"
        
        if biz_count >= 2 or has_contact:
            return "BUSINESS", "moderate_signals"
        
        if vendor_count >= 2:
            return "VENDOR", f"vendor_markers:{vendor_count}"
        
        return "UNKNOWN", "insufficient_signals"
    
    # ========================================
    # PHASE G1.6: B2B BOOST CALCULATION
    # ========================================
    
    def calculate_b2b_boost(self, enrichment: Dict) -> Tuple[int, List[str]]:
        """
        Calculate B2B confidence boost with reasons.
        Returns (boost_value, boost_reasons)
        """
        boost = 0
        reasons = []
        
        site_type = enrichment.get("site_type", "UNKNOWN")
        persona_type = enrichment.get("persona_type", "UNKNOWN")
        
        # Site type adjustments
        if site_type == "BUSINESS":
            boost += 4
            reasons.append("+4 BUSINESS site")
        elif site_type == "BLOG":
            boost -= 4
            reasons.append("-4 BLOG site")
        elif site_type == "VENDOR":
            boost -= 3
            reasons.append("-3 VENDOR site")
        elif site_type == "LINKHUB":
            boost -= 4
            reasons.append("-4 LINKHUB site")
        
        # Persona adjustments (G1.6)
        if persona_type == "BUYER":
            boost += 2
            reasons.append("+2 BUYER persona")
        elif persona_type == "AGENCY":
            boost += self.buyer_scoring.get("agency_penalty", -4)
            reasons.append(f"{self.buyer_scoring.get('agency_penalty', -4)} AGENCY persona")
        elif persona_type == "VENDOR":
            boost += self.buyer_scoring.get("vendor_penalty", -3)
            reasons.append(f"{self.buyer_scoring.get('vendor_penalty', -3)} VENDOR persona")
        elif persona_type == "CREATOR":
            boost += self.buyer_scoring.get("creator_penalty", -2)
            reasons.append(f"{self.buyer_scoring.get('creator_penalty', -2)} CREATOR persona")
        
        # Signal adjustments
        if enrichment.get("has_phone"):
            boost += self.buyer_scoring.get("has_phone_boost", 2)
            reasons.append(f"+{self.buyer_scoring.get('has_phone_boost', 2)} has_phone")
        
        if enrichment.get("has_address"):
            boost += self.buyer_scoring.get("has_address_boost", 2)
            reasons.append(f"+{self.buyer_scoring.get('has_address_boost', 2)} has_address")
        
        if enrichment.get("has_contact_page"):
            boost += self.buyer_scoring.get("has_contact_page_boost", 1)
            reasons.append(f"+{self.buyer_scoring.get('has_contact_page_boost', 1)} has_contact_page")
        
        if enrichment.get("services_detected"):
            boost += self.buyer_scoring.get("has_services_boost", 1)
            reasons.append(f"+{self.buyer_scoring.get('has_services_boost', 1)} has_services")
        
        # ICP lane boost
        icp_boost = enrichment.get("icp_boost", 0)
        if icp_boost > 0:
            boost += icp_boost
            reasons.append(f"+{icp_boost} ICP lane match")
        
        return boost, reasons


def get_enricher() -> ProspectEnricher:
    return ProspectEnricher()


if __name__ == "__main__":
    enricher = get_enricher()
    
    test_domains = [
        "blueoceanapplications.com",
        "digitalgrowthgenius.com",
        "ekworkman.blogspot.com"
    ]
    
    for domain in test_domains:
        print(f"\n=== {domain} ===")
        result = enricher.enrich(domain)
        print(f"Site Type: {result['site_type']}")
        print(f"Persona: {result['persona_type']} ({result['persona_reasons']})")
        print(f"ICP Lane: {result['icp_lane']}")
        print(f"Evidence: {result['evidence_signals']}")
        print(f"Penalties: {result['penalties']}")
        boost, reasons = enricher.calculate_b2b_boost(result)
        print(f"B2B Boost: {boost} ({reasons})")
