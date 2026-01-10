import requests
from bs4 import BeautifulSoup
import time

def manual_search(query):
    url = "https://html.duckduckgo.com/html/"
    payload = {'q': query}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://html.duckduckgo.com/'
    }
    
    print(f"Testing manual search for: '{query}'")
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # DDG HTML result selectors (usually class='result__a')
        results = []
        for link in soup.find_all('a', class_='result__a'):
            results.append({
                'title': link.get_text(strip=True),
                'href': link.get('href')
            })
            if len(results) >= 5:
                break
                
        print(f" -> Status: {res.status_code}")
        print(f" -> Found: {len(results)} results")
        for r in results:
            print(f"    - {r['title']} ({r['href']})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    manual_search("Phoenix roofers reviews")
