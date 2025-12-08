"""
Contact Enricher
Finds decision-maker contact info (email/name) from a domain.
Uses Hunter.io API (or similar) to find emails.

STUB: This is a placeholder implementation. 
Wire up Hunter.io or Apollo.io API keys to activate.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import requests
import json
from datetime import datetime

# Hunter.io Configuration
HUNTER_API_URL = "https://api.hunter.io/v2"

def enrich_contact(domain: str) -> dict:
    """
    Find decision-maker contact info for a domain.
    
    Returns:
        {
            "domain": str,
            "company": str,
            "emails": [
                {"email": str, "first_name": str, "last_name": str, "position": str, "confidence": int}
            ],
            "best_contact": {"email": str, "name": str, "title": str},
            "source": str
        }
    """
    api_key = os.environ.get("HUNTER_API_KEY")
    
    result = {
        "domain": domain,
        "company": None,
        "emails": [],
        "best_contact": None,
        "source": "hunter.io" if api_key else "stub",
        "timestamp": datetime.now().isoformat()
    }
    
    if not api_key:
        print(f"⚠️ HUNTER_API_KEY not found. Returning stub data for {domain}")
        # Return stub data for development
        result["company"] = domain.split('.')[0].title()
        result["emails"] = [
            {
                "email": f"info@{domain}",
                "first_name": "Contact",
                "last_name": "Us",
                "position": "General Inquiry",
                "confidence": 50
            }
        ]
        result["best_contact"] = {
            "email": f"info@{domain}",
            "name": "General Contact",
            "title": "Owner/Manager"
        }
        return result
    
    # Real Hunter.io API call
    try:
        # Domain Search - find all emails at domain
        search_url = f"{HUNTER_API_URL}/domain-search"
        params = {
            "domain": domain,
            "api_key": api_key,
            "limit": 10
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result["company"] = data.get("data", {}).get("organization")
        
        emails = data.get("data", {}).get("emails", [])
        result["emails"] = [
            {
                "email": e.get("value"),
                "first_name": e.get("first_name"),
                "last_name": e.get("last_name"),
                "position": e.get("position"),
                "confidence": e.get("confidence")
            }
            for e in emails
        ]
        
        # Find best contact (highest confidence, preferably owner/manager)
        priority_titles = ["owner", "ceo", "president", "founder", "manager", "director"]
        best = None
        best_score = 0
        
        for email in result["emails"]:
            score = email.get("confidence", 0)
            position = (email.get("position") or "").lower()
            
            # Boost score for priority titles
            for i, title in enumerate(priority_titles):
                if title in position:
                    score += 50 - (i * 5)
                    break
            
            if score > best_score:
                best_score = score
                best = email
        
        if best:
            result["best_contact"] = {
                "email": best.get("email"),
                "name": f"{best.get('first_name', '')} {best.get('last_name', '')}".strip(),
                "title": best.get("position")
            }
        
        print(f"✅ Found {len(result['emails'])} contacts for {domain}")
        
    except Exception as e:
        print(f"❌ Hunter.io error: {e}")
        result["error"] = str(e)
    
    return result


def batch_enrich(domains: list) -> list:
    """Enrich multiple domains."""
    results = []
    for domain in domains:
        result = enrich_contact(domain)
        results.append(result)
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Contact Enricher")
    parser.add_argument("domain", help="Domain to enrich (e.g., desertdiamondair.com)")
    args = parser.parse_args()
    
    result = enrich_contact(args.domain)
    print(json.dumps(result, indent=2))
