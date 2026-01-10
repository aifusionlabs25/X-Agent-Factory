from duckduckgo_search import DDGS
import time

backends = ["api", "html", "lite"]
query = "Veterinarians near me"

print(f"Testing DDGS Library Backends for query: '{query}'")

for backend in backends:
    print(f"\n--- Testing Backend: {backend} ---")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, backend=backend, max_results=3))
            print(f"Status: SUCCESS")
            print(f"Found: {len(results)} results")
            for r in results:
                print(f" - {r.get('title', 'No Title')}")
    except Exception as e:
        print(f"Status: FAILED")
        print(f"Error: {e}")
    
    time.sleep(2)
