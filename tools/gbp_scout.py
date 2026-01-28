"""
GBP Scout - Google Business Profile Scout (Phase G1.7)
Searches Google Maps for local businesses and extracts prospect data.

NOVA SPEC G1.7 COMPLIANCE:
- HTML fetch + parse (no paid APIs)
- Rate limiting (1 req/3s)
- 24h caching
- Normalized prospect objects
- Fallback to manual CSV import
"""
import os
import re
import json
import hashlib
import logging
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse
import csv

import requests
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
CONFIG_PATH = Path(__file__).parent.parent / "growth" / "config.yaml"
CACHE_DIR = Path(__file__).parent.parent / "growth" / "cache" / "gbp"
MANUAL_IMPORT_DIR = Path(__file__).parent.parent / "growth" / "manual_import"
BUDGET_FILE = CACHE_DIR / "weekly_budget.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


CONFIG = load_config()


class GBPScout:
    """
    Phase G1.7: Google Business Profile Scout.
    Searches Google Maps and extracts business data.
    """
    
    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        MANUAL_IMPORT_DIR.mkdir(parents=True, exist_ok=True)
        
        self.config = CONFIG.get("sources", {}).get("google_business", {})
        self.enabled = self.config.get("enabled", False)
        self.weekly_budget = self.config.get("weekly_budget", 5)
        self.max_per_query = self.config.get("max_per_query", 10)
        self.cache_ttl = self.config.get("cache_ttl_hours", 24)
        self.rate_limit = self.config.get("rate_limit_seconds", 3)
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        })
    
    # ========================================
    # BUDGET TRACKING
    # ========================================
    
    def _get_week_key(self) -> str:
        """Get current week key (YYYY-WW)."""
        now = datetime.now()
        return f"{now.year}-W{now.isocalendar()[1]:02d}"
    
    def _load_budget(self) -> Dict:
        """Load weekly budget tracker."""
        if BUDGET_FILE.exists():
            try:
                with open(BUDGET_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"week": self._get_week_key(), "used": 0, "queries": []}
    
    def _save_budget(self, budget: Dict):
        """Save weekly budget tracker."""
        try:
            with open(BUDGET_FILE, 'w') as f:
                json.dump(budget, f, indent=2)
        except Exception as e:
            logger.warning(f"Budget save failed: {e}")
    
    def _check_budget(self) -> Tuple[bool, int]:
        """Check if we have budget remaining. Returns (has_budget, remaining)."""
        budget = self._load_budget()
        week_key = self._get_week_key()
        
        # Reset if new week
        if budget.get("week") != week_key:
            budget = {"week": week_key, "used": 0, "queries": []}
            self._save_budget(budget)
        
        remaining = self.weekly_budget - budget.get("used", 0)
        return remaining > 0, remaining
    
    def _consume_budget(self, query: str):
        """Consume one query from budget."""
        budget = self._load_budget()
        budget["used"] = budget.get("used", 0) + 1
        budget["queries"].append({
            "query": query,
            "timestamp": datetime.now().isoformat()
        })
        self._save_budget(budget)
    
    # ========================================
    # CACHING
    # ========================================
    
    def _get_cache_path(self, query: str) -> Path:
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return CACHE_DIR / f"gbp_{query_hash}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        if not cache_path.exists():
            return False
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < timedelta(hours=self.cache_ttl)
    
    def _load_cache(self, cache_path: Path) -> Optional[List[Dict]]:
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    logger.debug(f"GBP cache hit: {cache_path.name}")
                    return json.load(f)
            except:
                pass
        return None
    
    def _save_cache(self, cache_path: Path, results: List[Dict]):
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            logger.warning(f"GBP cache write failed: {e}")
    
    # ========================================
    # SEARCH & PARSING
    # ========================================
    
    def search_google_maps(self, query: str) -> List[Dict]:
        """
        Search Google Maps for businesses.
        Uses HTML parsing (no API required).
        """
        cache_path = self._get_cache_path(query)
        cached = self._load_cache(cache_path)
        if cached is not None:
            logger.info(f"GBP cache hit: {query}")
            return cached
        
        # Check budget
        has_budget, remaining = self._check_budget()
        if not has_budget:
            logger.warning(f"GBP weekly budget exhausted ({self.weekly_budget}/week)")
            return []
        
        # Rate limiting
        time.sleep(self.rate_limit + random.uniform(0.5, 1.5))
        
        try:
            # Build search URL
            search_url = f"https://www.google.com/maps/search/{quote_plus(query)}"
            logger.info(f"GBP Search: {query}")
            
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"GBP search failed: HTTP {response.status_code}")
                return []
            
            # Parse results
            results = self._parse_maps_html(response.text, query)
            
            if results:
                self._consume_budget(query)
                self._save_cache(cache_path, results)
                logger.info(f"GBP found {len(results)} businesses for: {query}")
            else:
                logger.info(f"GBP no results for: {query}")
            
            return results
            
        except Exception as e:
            logger.error(f"GBP search error: {e}")
            return []
    
    def _parse_maps_html(self, html: str, query: str) -> List[Dict]:
        """
        Parse Google Maps HTML to extract business listings.
        Note: This is fragile and may need updates as Google changes their HTML.
        """
        results = []
        
        # Try to extract business data from page
        # Google Maps uses complex JavaScript rendering, so we look for
        # structured data or fallback patterns
        
        # Look for phone numbers
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, html)
        
        # Look for addresses (basic pattern)
        address_pattern = r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way)[\s,]+[\w\s]+,\s*[A-Z]{2}\s+\d{5}'
        addresses = re.findall(address_pattern, html)
        
        # Look for structured data (ld+json)
        ld_pattern = r'<script type="application/ld\+json"[^>]*>(.*?)</script>'
        ld_matches = re.findall(ld_pattern, html, re.DOTALL)
        
        for ld_json in ld_matches:
            try:
                data = json.loads(ld_json)
                if isinstance(data, dict):
                    if data.get("@type") == "LocalBusiness" or "LocalBusiness" in str(data.get("@type", "")):
                        business = self._extract_from_ld_json(data, query)
                        if business:
                            results.append(business)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and ("LocalBusiness" in str(item.get("@type", ""))):
                            business = self._extract_from_ld_json(item, query)
                            if business:
                                results.append(business)
            except json.JSONDecodeError:
                continue
        
        # If no structured data, try pattern matching for business names
        if not results:
            # Look for common business listing patterns
            # This is a simplified approach - real scraping would need more sophistication
            name_patterns = [
                r'"title":"([^"]+)"',
                r'aria-label="([^"]+(?:HVAC|Plumbing|Dental|Law|Electric|Roofing)[^"]*)"',
            ]
            
            for pattern in name_patterns:
                names = re.findall(pattern, html, re.IGNORECASE)
                for name in names[:self.max_per_query]:
                    if len(name) > 3 and len(name) < 100:
                        results.append({
                            "name": name.strip(),
                            "category": self._guess_category(query),
                            "phone": phones[0] if phones else None,
                            "address": addresses[0] if addresses else None,
                            "website": None,
                            "rating": None,
                            "review_count": None,
                            "maps_url": f"https://www.google.com/maps/search/{quote_plus(name)}",
                            "source_query": query
                        })
        
        return results[:self.max_per_query]
    
    def _extract_from_ld_json(self, data: Dict, query: str) -> Optional[Dict]:
        """Extract business info from structured data."""
        try:
            name = data.get("name", "")
            if not name:
                return None
            
            phone = data.get("telephone", "")
            address_data = data.get("address", {})
            if isinstance(address_data, dict):
                address = f"{address_data.get('streetAddress', '')}, {address_data.get('addressLocality', '')}, {address_data.get('addressRegion', '')} {address_data.get('postalCode', '')}".strip(", ")
            else:
                address = str(address_data)
            
            website = data.get("url", "") or data.get("sameAs", "")
            if isinstance(website, list):
                website = website[0] if website else ""
            
            rating_data = data.get("aggregateRating", {})
            rating = rating_data.get("ratingValue") if isinstance(rating_data, dict) else None
            review_count = rating_data.get("reviewCount") if isinstance(rating_data, dict) else None
            
            return {
                "name": name,
                "category": self._guess_category(query),
                "phone": phone if phone else None,
                "address": address if address.strip() else None,
                "website": website if website else None,
                "rating": float(rating) if rating else None,
                "review_count": int(review_count) if review_count else None,
                "maps_url": f"https://www.google.com/maps/search/{quote_plus(name)}",
                "source_query": query
            }
        except Exception as e:
            logger.debug(f"LD+JSON extraction failed: {e}")
            return None
    
    def _guess_category(self, query: str) -> str:
        """Guess category from search query."""
        query_lower = query.lower()
        categories = {
            "hvac": "HVAC",
            "plumb": "Plumbing",
            "electric": "Electrical",
            "roof": "Roofing",
            "pest": "Pest Control",
            "dental": "Dental",
            "dentist": "Dental",
            "law": "Legal",
            "attorney": "Legal",
            "lawyer": "Legal",
            "property": "Property Management",
            "vet": "Veterinary",
            "doctor": "Medical",
            "clean": "Cleaning",
            "landscap": "Landscaping"
        }
        for key, value in categories.items():
            if key in query_lower:
                return value
        return "Business"
    
    # ========================================
    # MANUAL IMPORT
    # ========================================
    
    def import_from_csv(self) -> List[Dict]:
        """Import prospects from CSV files in manual_import directory."""
        results = []
        
        if not MANUAL_IMPORT_DIR.exists():
            return results
        
        csv_files = list(MANUAL_IMPORT_DIR.glob("*.csv"))
        
        for csv_file in csv_files:
            try:
                logger.info(f"Importing from CSV: {csv_file.name}")
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Normalize column names
                        name = row.get("name", row.get("Name", ""))
                        website = row.get("website", row.get("Website", row.get("url", "")))
                        phone = row.get("phone", row.get("Phone", ""))
                        address = row.get("address", row.get("Address", ""))
                        category = row.get("category", row.get("Category", "Business"))
                        
                        if name.strip():
                            results.append({
                                "name": name.strip(),
                                "category": category or "Business",
                                "phone": phone.strip() if phone else None,
                                "address": address.strip() if address else None,
                                "website": website.strip() if website else None,
                                "rating": None,
                                "review_count": None,
                                "maps_url": None,
                                "source_query": f"csv:{csv_file.name}"
                            })
                
                # Archive processed file
                archive_dir = MANUAL_IMPORT_DIR / "processed"
                archive_dir.mkdir(exist_ok=True)
                csv_file.rename(archive_dir / f"{datetime.now().strftime('%Y%m%d')}_{csv_file.name}")
                
            except Exception as e:
                logger.error(f"CSV import error ({csv_file.name}): {e}")
        
        logger.info(f"Imported {len(results)} prospects from CSV")
        return results
    
    # ========================================
    # PROSPECT NORMALIZATION
    # ========================================
    
    def normalize_prospect(self, raw: Dict) -> Dict:
        """Normalize GBP data to standard prospect format."""
        name = raw.get("name", "Unknown")
        website = raw.get("website", "")
        phone = raw.get("phone", "")
        address = raw.get("address", "")
        
        # Extract domain from website
        domain = None
        if website:
            try:
                parsed = urlparse(website if website.startswith("http") else f"https://{website}")
                domain = parsed.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]
            except:
                pass
        
        # Dedup key: prefer domain, fallback to phone, then name
        if domain:
            prospect_key = domain
        elif phone:
            # Normalize phone for dedup
            phone_normalized = re.sub(r'\D', '', phone)
            prospect_key = f"phone:{phone_normalized}"
        else:
            prospect_key = f"name:{name.lower().replace(' ', '-')}"
        
        return {
            "id": hashlib.md5(prospect_key.encode()).hexdigest()[:12],
            "name": name,
            "source": "GBP",
            "score": 5,  # Base score, will be adjusted by enricher
            "moment_score": 0,  # No pain signal from GBP
            "b2b_confidence": 6 if phone and address else 4,  # High base for verified businesses
            "bucket": "WATCH",  # Will be adjusted after enrichment
            "prospect_key": prospect_key,
            "domain": domain,
            "domain_quality": "good" if domain else "low",
            "expanded_urls": [website] if website else [],
            "x_handle": None,
            "x_profile_url": None,
            "context_gate": "PASS",  # GBP leads bypass X context gates
            "vendor_pitch_gate": "PASS",
            "site_type": "UNKNOWN",  # Will be set by enricher
            "persona_type": "UNKNOWN",  # Will be set by enricher
            "icp_lane": None,
            "evidence_signals": [],
            "penalties": [],
            "evidence": [{
                "type": "gbp",
                "text": f"{raw.get('category', 'Business')} | {address or 'No address'}",
                "url": raw.get("maps_url", ""),
                "created_at": datetime.now().isoformat(),
                "query": raw.get("source_query", "")
            }],
            "why_this_lead": f"Found via Google Business Profile. Category: {raw.get('category')}. {'Has phone.' if phone else ''} {'Has address.' if address else ''}".strip(),
            "recommended_action": "WATCH",
            "tags": [raw.get("category", "business").lower().replace(" ", "_"), "gbp_source"],
            "discovered_at": datetime.now().isoformat(),
            # GBP-specific fields
            "gbp_data": {
                "phone": phone,
                "address": address,
                "category": raw.get("category"),
                "rating": raw.get("rating"),
                "review_count": raw.get("review_count"),
                "maps_url": raw.get("maps_url")
            }
        }
    
    # ========================================
    # MAIN HUNT
    # ========================================
    
    def hunt(self) -> List[Dict]:
        """
        Run GBP hunt with budget constraints.
        Returns normalized prospect list.
        """
        if not self.enabled:
            logger.info("GBP Scout disabled in config")
            return []
        
        has_budget, remaining = self._check_budget()
        if not has_budget:
            logger.warning(f"GBP weekly budget exhausted")
            # Fall back to manual import
            return self._hunt_manual_only()
        
        logger.info(f"GBP Scout starting (budget: {remaining}/{self.weekly_budget} remaining)")
        
        all_results = []
        queries_to_run = []
        
        # Select queries based on ICP lanes
        query_config = self.config.get("queries", {})
        for lane, queries in query_config.items():
            if queries:
                # Pick 1-2 queries per lane
                selected = random.sample(queries, min(2, len(queries)))
                queries_to_run.extend(selected)
        
        # Limit to remaining budget
        queries_to_run = queries_to_run[:remaining]
        
        logger.info(f"Running {len(queries_to_run)} GBP queries")
        
        for query in queries_to_run:
            results = self.search_google_maps(query)
            for raw in results:
                normalized = self.normalize_prospect(raw)
                all_results.append(normalized)
        
        # Also check manual imports
        manual_results = self.import_from_csv()
        for raw in manual_results:
            normalized = self.normalize_prospect(raw)
            all_results.append(normalized)
        
        logger.info(f"GBP Scout found {len(all_results)} total prospects")
        return all_results
    
    def _hunt_manual_only(self) -> List[Dict]:
        """Hunt with manual import only (when budget exhausted)."""
        logger.info("GBP running manual import only (budget exhausted)")
        results = []
        
        manual_results = self.import_from_csv()
        for raw in manual_results:
            normalized = self.normalize_prospect(raw)
            results.append(normalized)
        
        return results


def get_scout() -> GBPScout:
    return GBPScout()


if __name__ == "__main__":
    scout = get_scout()
    results = scout.hunt()
    
    print(f"Found {len(results)} prospects")
    for p in results[:5]:
        print(f"  - {p['name']} | {p['domain'] or 'no website'} | {p.get('gbp_data', {}).get('phone', 'no phone')}")
