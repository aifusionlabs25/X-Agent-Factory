"""
X API Diagnostic Script - Nova's Protocol
Tests auth vs access-tier issues in under 5 minutes.
"""
import os
import json
import urllib.parse
from pathlib import Path

import requests

# Load token from .env.growth (raw, auto URL-decode)
def load_token():
    env_path = Path(__file__).parent.parent / "growth" / ".env.growth"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() == "X_GROWTH_RADAR_BEARER_TOKEN":
                        # Auto URL-decode if needed
                        raw = value.strip()
                        if '%' in raw:
                            raw = urllib.parse.unquote(raw)
                        return raw
    return os.environ.get("X_GROWTH_RADAR_BEARER_TOKEN", "").strip()

def run_diagnostic():
    token = load_token()
    
    if not token:
        print("[ERROR] No Bearer Token found!")
        return
    
    print(f"[TOKEN] Loaded (first 20 chars): {token[:20]}...")
    print(f"[TOKEN] Length: {len(token)} chars")
    print()
    
    # Session setup - Nova's protocol: raw token, no encoding
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "User-Agent": "X-Agent-Factory-Growth/1.0"
    })
    
    # =============================================
    # TEST 1: Recent Search (the endpoint we need)
    # =============================================
    print("=" * 60)
    print("TEST 1: Recent Search API")
    print("=" * 60)
    
    # Nova's fix: Use api.x.com, NOT api.twitter.com
    url1 = "https://api.x.com/2/tweets/search/recent"
    params1 = {
        "query": "test",
        "max_results": 10
    }
    
    print(f"[URL] {url1}")
    print(f"[PARAMS] {params1}")
    
    resp1 = None
    try:
        resp1 = session.get(url1, params=params1, timeout=30)
        print(f"[STATUS] {resp1.status_code}")
        
        # Nova's logging: response body error details
        try:
            body = resp1.json()
            if "errors" in body:
                for err in body.get("errors", []):
                    print(f"[ERROR TITLE] {err.get('title', 'N/A')}")
                    print(f"[ERROR DETAIL] {err.get('detail', 'N/A')}")
                    print(f"[ERROR TYPE] {err.get('type', 'N/A')}")
            elif "error" in body:
                print(f"[ERROR] {body.get('error')}")
                print(f"[DESCRIPTION] {body.get('error_description', 'N/A')}")
            elif "data" in body:
                print(f"[SUCCESS] Found {len(body.get('data', []))} tweets")
            else:
                print(f"[BODY] {json.dumps(body, indent=2)[:500]}")
        except:
            print(f"[RAW] {resp1.text[:500]}")
    except Exception as e:
        print(f"[EXCEPTION] {type(e).__name__}: {e}")
    
    print()
    
    # =============================================
    # TEST 2: Tweet Lookup (non-search read endpoint)
    # =============================================
    print("=" * 60)
    print("TEST 2: Tweet Lookup API (non-search)")
    print("=" * 60)
    
    # Known public tweet ID (Jack Dorsey's first tweet)
    url2 = "https://api.x.com/2/tweets"
    params2 = {
        "ids": "20"  # First tweet ever
    }
    
    print(f"[URL] {url2}")
    print(f"[PARAMS] {params2}")
    
    resp2 = None
    try:
        resp2 = session.get(url2, params=params2, timeout=30)
        print(f"[STATUS] {resp2.status_code}")
        
        try:
            body = resp2.json()
            if "errors" in body:
                for err in body.get("errors", []):
                    print(f"[ERROR TITLE] {err.get('title', 'N/A')}")
                    print(f"[ERROR DETAIL] {err.get('detail', 'N/A')}")
                    print(f"[ERROR TYPE] {err.get('type', 'N/A')}")
            elif "error" in body:
                print(f"[ERROR] {body.get('error')}")
                print(f"[DESCRIPTION] {body.get('error_description', 'N/A')}")
            elif "data" in body:
                print(f"[SUCCESS] Retrieved tweet data")
                print(f"[TWEET] {body.get('data', [{}])[0].get('text', 'N/A')[:100]}")
            else:
                print(f"[BODY] {json.dumps(body, indent=2)[:500]}")
        except:
            print(f"[RAW] {resp2.text[:500]}")
    except Exception as e:
        print(f"[EXCEPTION] {type(e).__name__}: {e}")
    
    print()
    
    # =============================================
    # INTERPRETATION
    # =============================================
    print("=" * 60)
    print("INTERPRETATION (Nova's Protocol)")
    print("=" * 60)
    
    if resp1 and resp2:
        s1 = resp1.status_code
        s2 = resp2.status_code
        
        print(f"Search Status: {s1}")
        print(f"Lookup Status: {s2}")
        print()
        
        if s1 == 401 and s2 == 401:
            print("DIAGNOSIS: 401 on BOTH -> Token/header handling is wrong")
        elif s1 == 402 or s2 == 402:
            print("DIAGNOSIS: 402 -> Payment Required (no API credits)")
        elif s1 == 403 and s2 != 403:
            print("DIAGNOSIS: 403 on Search only -> Entitlement issue")
        elif s1 == 403 and s2 == 403:
            print("DIAGNOSIS: 403 on BOTH -> Project/app access level issue")
        elif s1 == 429 or s2 == 429:
            print("DIAGNOSIS: 429 -> Rate limited (API working)")
        elif s1 == 200 and s2 == 200:
            print("DIAGNOSIS: 200 on BOTH -> Everything works!")
        else:
            print(f"DIAGNOSIS: Mixed results")

if __name__ == "__main__":
    run_diagnostic()
