"""
Web Scout - Growth Department
Hunts for pain signals on public websites.
"""
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScout:
    """Hunts for prospects on public websites based on pain signals."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "X-Agent-Factory-Growth/1.0"
        })
        
        # Pain signal patterns
        self.pain_patterns = [
            r"missed\s+calls?",
            r"can'?t\s+answer",
            r"after\s+hours",
            r"voicemail",
            r"scheduling\s+(nightmare|problems?)",
            r"losing\s+customers?",
            r"overwhelmed",
            r"need\s+help\s+answering",
            r"receptionist",
        ]
        
    def analyze_website(self, url: str) -> Optional[Dict]:
        """
        Analyze a single website for pain signals.
        Returns a prospect dict or None if not a good fit.
        """
        try:
            logger.info(f"Analyzing: {url}")
            
            resp = self.session.get(url, timeout=10)
            if resp.status_code != 200:
                return None
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True).lower()
            
            # Extract company name
            title = soup.find('title')
            company_name = title.get_text().strip() if title else urlparse(url).netloc
            
            # Detect pain signals
            signals = []
            for pattern in self.pain_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    signals.append(pattern.replace(r'\s+', ' ').replace(r'\'?', "'"))
            
            # Look for contact info
            contact_info = self._extract_contact_info(soup, text)
            
            # Detect industry (basic heuristics)
            industry = self._detect_industry(text)
            
            # Only return if we found signals or it's a service business
            if signals or industry:
                return {
                    "prospect_name": company_name[:100],
                    "url": url,
                    "source": "web",
                    "industry": industry or "Unknown",
                    "signals": signals,
                    "contact_info": contact_info,
                    "discovered_at": datetime.now().isoformat(),
                    "notes": f"Analyzed from {url}"
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to analyze {url}: {e}")
            return None
    
    def _extract_contact_info(self, soup: BeautifulSoup, text: str) -> Dict:
        """Extract phone and email from page."""
        contact = {}
        
        # Phone pattern
        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if phone_match:
            contact["phone"] = phone_match.group()
        
        # Email pattern
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if email_match:
            contact["email"] = email_match.group()
        
        return contact
    
    def _detect_industry(self, text: str) -> Optional[str]:
        """Detect industry from page content."""
        industry_keywords = {
            "HVAC": ["hvac", "heating", "cooling", "air conditioning", "furnace"],
            "Plumbing": ["plumbing", "plumber", "drain", "pipe", "water heater"],
            "Electrical": ["electrical", "electrician", "wiring", "outlet"],
            "Legal": ["law firm", "attorney", "lawyer", "legal services"],
            "Medical": ["medical", "healthcare", "clinic", "doctor", "physician"],
            "Roofing": ["roofing", "roof repair", "shingles"],
            "Pest Control": ["pest control", "exterminator", "termite"],
            "Veterinary": ["veterinary", "vet clinic", "animal hospital", "pet care"],
        }
        
        for industry, keywords in industry_keywords.items():
            if any(kw in text for kw in keywords):
                return industry
        
        return None
    
    def hunt(self, seed_urls: List[str], max_results: int = 20) -> List[Dict]:
        """
        Hunt for prospects from a list of seed URLs.
        Returns list of prospect dicts.
        """
        prospects = []
        
        for url in seed_urls[:max_results]:
            result = self.analyze_website(url)
            if result:
                prospects.append(result)
                
            if len(prospects) >= max_results:
                break
        
        return prospects

if __name__ == "__main__":
    # Test run
    scout = WebScout()
    
    # Example seed URLs (would normally come from a discovery source)
    test_urls = [
        "https://www.zyratalk.com",  # Known test target
    ]
    
    results = scout.hunt(test_urls)
    print(json.dumps(results, indent=2))
