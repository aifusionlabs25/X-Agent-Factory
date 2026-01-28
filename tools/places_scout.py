"""
Places Scout - Google Places API Integration (Phase G1.9)
Nationwide Sourcing Engine with SQLite Persistence.

NOVA SPEC G1.9:
- Batch Execution (Coverage Packs)
- SQLite Persistence (Dedupe, State, Logs)
- Cost Governors (Daily Limits, Field Masks)
- Two-Stage Fetch (Search -> Dedupe -> Enrich)
"""
import os
import json
import hashlib
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
import yaml
from dotenv import load_dotenv

# Import G1.9 DB
from growth_db import GrowthDB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent / "growth"
CONFIG_PATH = BASE_DIR / "config.yaml"
ENV_PATH = BASE_DIR / ".env.growth"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

GMAPS_API_KEY = os.getenv("GMAPS_API_KEY")

class PlacesScout:
    """
    Phase G1.9: Nationwide Places Scout.
    Uses SQLite for dedupe and state management.
    """
    
    BASE_URL_SEARCH = "https://places.googleapis.com/v1/places:searchText"
    BASE_URL_DETAILS = "https://places.googleapis.com/v1/places/" # + place_id
    
    def __init__(self):
        self.db = GrowthDB()
        self.config = self._load_config()
        self.places_config = self.config.get("sources", {}).get("google_places", {})
        self.enabled = self.places_config.get("enabled", False)
        
        # Cost Guards
        self.max_daily_requests = self.places_config.get("max_search_requests_per_day", 50)
        self.rate_limit = self.places_config.get("rate_limit_seconds", 1.0)
        
        # Field Masks (Nova Spec G1.9 Strict)
        # Stage 1: Discovery (minimal) - Removed websiteUri per spec to save cost/bytes if not crucial
        # Spec says: "searchText minimal mask: id, displayName, formattedAddress, types, location"
        self.mask_search = "places.id,places.displayName,places.formattedAddress,places.types,places.location"
        
        # Stage 2: Enrichment (Shortlist only)
        # Spec says: "getPlace: id, displayName, formattedAddress, phone, website, rating, userRatingCount, businessStatus"
        self.mask_details = "id,displayName,formattedAddress,nationalPhoneNumber,websiteUri,rating,userRatingCount,businessStatus"
        
        if not GMAPS_API_KEY:
            logger.warning("GMAPS_API_KEY not found. Places Scout disabled.")
            self.enabled = False

    def _load_config(self) -> dict:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    # ========================================
    # STAGE 1: BATCH DISCOVERY
    # ========================================
    
    def search_batch(self, queries: List[Dict], run_id: str) -> List[Dict]:
        """Execute a batch of queries with persistence."""
        if not self.enabled:
            return []
            
        new_candidates = []
        
        for q in queries:
            logger.info(f"Query: {q['text']} ({q['region_tag']})")
            
            results = self._api_search_text(q)
            
            # Log query with full traceability
            self.db.log_query(
                {**q, "run_id": run_id}, 
                len(results), 
                error=None if results else "No results or error"
            )
            
            for place in results:
                # Upsert to DB (Stage 2: Dedupe)
                is_new = self.db.upsert_place(place, source="PLACES_API", run_id=run_id)
                
                if is_new:
                    # Normalize for pipeline return
                    norm = self.normalize_place(place, q['text'], q['region_tag'])
                    new_candidates.append(norm)
            
            # Rate limit
            time.sleep(self.rate_limit)
            
        return new_candidates

    def _api_search_text(self, query_dict: Dict) -> List[Dict]:
        """Call Places API text search with resilience."""
        query_text = query_dict['text']
        
        # Cache Key (Nova Spec: endpoint + field_mask)
        # We perform hash of (text + region + field_mask)
        raw_key = f"{query_text}|{query_dict.get('region_tag')}|{self.mask_search}"
        cache_key = f"search:{hashlib.md5(raw_key.encode()).hexdigest()}"
        
        cached = self.db.get_cache(cache_key)
        if cached:
            logger.info("Cache hit for search")
            return cached
            
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GMAPS_API_KEY,
            "X-Goog-FieldMask": self.mask_search
        }
        payload = {
            "textQuery": query_text, 
            "maxResultCount": query_dict.get("max_results", 20)
        }
        
        # Resilience with Backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = requests.post(self.BASE_URL_SEARCH, headers=headers, json=payload, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    places = data.get("places", [])
                    # Cache success (24h)
                    self.db.set_cache(
                        cache_key, 
                        places, 
                        ttl_hours=24,
                        extras={"endpoint": "searchText", "field_mask": self.mask_search}
                    )
                    return places
                    
                elif resp.status_code in [429, 503]:
                    logger.warning(f"API {resp.status_code} (attempt {attempt+1}/{max_retries}). Retrying...")
                    time.sleep(2 ** attempt) # Exponential backoff
                else:
                    logger.error(f"API Error {resp.status_code}: {resp.text}")
                    break
                    
            except Exception as e:
                logger.error(f"Request failed: {e}")
                time.sleep(1)
                
        return []

    # ========================================
    # STAGE 3: SELECTIVE ENRICHMENT
    # ========================================

    def enrich_place(self, place_id: str) -> Optional[Dict]:
        """Fetch details for a specific place (Stage 3)."""
        if not self.enabled:
            return None
            
        # Check Cache
        raw_key = f"{place_id}|{self.mask_details}"
        cache_key = f"details:{hashlib.md5(raw_key.encode()).hexdigest()}"
        
        cached = self.db.get_cache(cache_key)
        if cached:
            return cached
            
        url = f"{self.BASE_URL_DETAILS}{place_id}"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GMAPS_API_KEY,
            "X-Goog-FieldMask": self.mask_details
        }
        
        # Resilience
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    place = resp.json()
                    # Cache details (30 days)
                    self.db.set_cache(
                        cache_key, 
                        place, 
                        ttl_hours=24*30,
                        extras={"endpoint": "getPlace", "field_mask": self.mask_details}
                    )
                    
                    # Update DB record with enriched data
                    self.db.upsert_place(place, source="PLACES_API_ENRICHED")
                    return place
                    
                elif resp.status_code in [429, 503]:
                    logger.warning(f"API {resp.status_code} (attempt {attempt+1}). Retrying...")
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Details Error {place_id}: {resp.status_code}")
                    break
                    
            except Exception as e:
                logger.error(f"Details Request failed: {e}")
                time.sleep(1)
                
        return None

    # ========================================
    # UTILS
    # ========================================

    def normalize_place(self, place: Dict, source_query: str, region_tag: str) -> Dict:
        """Normalize API response to standard prospect object."""
        place_id = place.get("id") or place.get("name", "").split("/")[-1] # details sometimes return name=places/ID
        name = place.get("displayName", {}).get("text", "Unknown Business")
        address = place.get("formattedAddress", "")
        website = place.get("websiteUri", "")
        
        # Domain parsing
        domain = None
        if website:
            try:
                parsed = urlparse(website)
                domain = parsed.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]
            except:
                pass
                
        # Prospect Key (Dedup): Domain > Name
        if domain:
            prospect_key = domain
        else:
            prospect_key = f"name:{name.lower().replace(' ', '-')}"
            
        return {
            "id": hashlib.md5(place_id.encode()).hexdigest()[:12],
            "name": name,
            "source": "GBP_API",
            "region_tag": region_tag,
            "score": 5,
            "moment_score": 0,
            "b2b_confidence": 6,
            "bucket": "WATCH",
            "prospect_key": prospect_key,
            "domain": domain,
            "domain_quality": "good" if domain else "low",
            "expanded_urls": [website] if website else [],
            "x_handle": None,
            "x_profile_url": None,
            "site_type": "UNKNOWN",
            "persona_type": "UNKNOWN",
            "evidence": [{
                "type": "gmaps_api",
                "text": f"{name} | {address}",
                "url": website or "",
                "created_at": datetime.now().isoformat(),
                "query": source_query
            }],
            "why_this_lead": f"Google Maps verified business. Region: {region_tag}",
            "recommended_action": "WATCH",
            "tags": ["gmaps_api", region_tag] + [t.lower().replace('_', ' ') for t in place.get("types", [])[:3]],
            "discovered_at": datetime.now().isoformat(),
            "gbp_data": {
                "place_id": place_id,
                "address": address,
                "types": place.get("types", []),
                "maps_url": f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else None,
                "phone": place.get("nationalPhoneNumber")
            }
        }

def get_scout() -> PlacesScout:
    return PlacesScout()

if __name__ == "__main__":
    # Smoke Test
    scout = get_scout()
    if scout.enabled:
        print("Running G1.9 Scout Test...")
        # Mock batch
        mock_queries = [{
            "text": "plumber in Phoenix AZ", 
            "region_tag": "AZ-Phoenix", 
            "max_results": 5
        }]
        results = scout.search_batch(mock_queries, run_id="test_run_001")
        print(f"Found {len(results)} new prospects.")
        if results:
            # Test enrichment on first result
            pid = results[0]['gbp_data']['place_id']
            print(f"Enriching {pid}...")
            details = scout.enrich_place(pid)
            print(f"Phone: {details.get('nationalPhoneNumber')}")
