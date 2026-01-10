from duckduckgo_search import DDGS
from time import sleep

queries = [
    "test query",
    "Phoenix roofers reviews",
    "Roofers Phoenix bad reviews",
    "Phoenix roofing companies with poor scheduling"
]

print("Testing DuckDuckGo Search (Batch Mode)...")
try:
    with DDGS() as ddgs:
        for q in queries:
            print(f"\nQuery: '{q}'")
            results = list(ddgs.text(q, max_results=3))
            print(f" -> Results found: {len(results)}")
            for r in results:
                print(f"    - {r['title']}")
            sleep(1)
            
except Exception as e:
    print(f"Error: {e}")
