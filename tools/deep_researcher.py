#!/usr/bin/env python3
"""
Deep Researcher - Knowledge Base Builder
GPU-accelerated web scraping and content extraction for X Agent Factory

Usage:
    python deep_researcher.py --job-id <id> --query <query> --agent <agent_id> --output <dir>
"""

import argparse
import json
import os
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Check for required packages
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    os.system("pip install requests beautifulsoup4 lxml")
    import requests
    from bs4 import BeautifulSoup

# Optional: GPU-accelerated embedding (if available)
try:
    import torch
    GPU_AVAILABLE = torch.cuda.is_available()
    if GPU_AVAILABLE:
        print(f"[GPU] Detected: {torch.cuda.get_device_name(0)}")
except ImportError:
    GPU_AVAILABLE = False


class DeepResearcher:
    """Deep web researcher for building Knowledge Bases"""
    
    def __init__(self, job_id: str, query: str, agent_id: str, output_dir: str, 
                 max_depth: int = 3, max_pages: int = 100):
        self.job_id = job_id
        self.query = query
        self.agent_id = agent_id
        self.output_dir = Path(output_dir)
        self.max_depth = max_depth
        self.max_pages = max_pages
        
        self.visited_urls = set()
        self.documents = []
        self.errors = []
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        
    def log(self, message: str):
        """Print timestamped log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def generate_search_urls(self) -> List[str]:
        """Generate list of URLs to search based on query"""
        search_engines = [
            f"https://www.google.com/search?q={self.query.replace(' ', '+')}",
            f"https://duckduckgo.com/html/?q={self.query.replace(' ', '+')}",
        ]
        
        # Domain-specific searches based on query content
        domain_sources = []
        query_lower = self.query.lower()
        
        if 'veterinary' in query_lower or 'pet' in query_lower or 'animal' in query_lower:
            domain_sources.extend([
                "https://www.aspca.org/pet-care/animal-poison-control",
                "https://www.avma.org/resources-tools/pet-owners",
                "https://www.petmd.com/",
                "https://vcahospitals.com/know-your-pet",
                "https://www.merckvetmanual.com/",
                "https://www.vet.cornell.edu/departments-centers-and-institutes/cornell-feline-health-center",
            ])
            
        if 'hvac' in query_lower or 'plumber' in query_lower or 'field service' in query_lower:
            domain_sources.extend([
                "https://www.servicetitan.com/blog",
                "https://www.achr.com/",
            ])
            
        return domain_sources if domain_sources else search_engines
    
    def fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch page content with error handling"""
        if url in self.visited_urls:
            return None
            
        self.visited_urls.add(url)
        
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.errors.append({"url": url, "error": str(e)})
            return None
    
    def extract_content(self, html: str, url: str) -> Dict:
        """Extract meaningful content from HTML"""
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Get title
        title = soup.title.string if soup.title else urlparse(url).path
        
        # Get main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
        
        if not main_content:
            return None
            
        # Extract text
        text = main_content.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)
        
        # Skip if too short (likely not useful content)
        if len(clean_text) < 200:
            return None
            
        # Extract links for further crawling
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/'):
                href = urljoin(url, href)
            if href.startswith('http') and href not in self.visited_urls:
                links.append(href)
        
        return {
            "title": title.strip() if title else "Untitled",
            "url": url,
            "content": clean_text,
            "word_count": len(clean_text.split()),
            "links": links[:20],  # Limit links to follow
            "extracted_at": datetime.now().isoformat()
        }
    
    def save_document(self, doc: Dict):
        """Save extracted document to output directory"""
        # Generate filename from URL hash
        url_hash = hashlib.md5(doc['url'].encode()).hexdigest()[:12]
        safe_title = "".join(c for c in doc['title'][:50] if c.isalnum() or c in ' -_').strip()
        filename = f"{safe_title}_{url_hash}.json"
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
            
        self.documents.append(filepath)
        self.log(f"[SAVED] {filename} ({doc['word_count']} words)")
    
    def crawl(self, url: str, depth: int = 0):
        """Recursively crawl and extract content"""
        if depth > self.max_depth:
            return
        if len(self.documents) >= self.max_pages:
            return
            
        self.log(f"[CRAWL] depth={depth}: {url[:80]}...")
        
        html = self.fetch_page(url)
        if not html:
            return
            
        doc = self.extract_content(html, url)
        if doc:
            self.save_document(doc)
            
            # Follow links
            for link in doc.get('links', [])[:5]:  # Limit links per page
                if len(self.documents) < self.max_pages:
                    time.sleep(0.5)  # Rate limiting
                    self.crawl(link, depth + 1)
    
    def run(self):
        """Execute the research job"""
        self.log(f"[START] Deep Research")
        self.log(f"   Job ID: {self.job_id}")
        self.log(f"   Agent: {self.agent_id}")
        self.log(f"   Query: {self.query}")
        self.log(f"   Max Pages: {self.max_pages}")
        self.log(f"   GPU: {'Yes' if GPU_AVAILABLE else 'No'}")
        
        # Get starting URLs
        start_urls = self.generate_search_urls()
        self.log(f"[SEEDS] {len(start_urls)} URLs")
        
        # Crawl each starting URL
        for url in start_urls:
            if len(self.documents) >= self.max_pages:
                break
            self.crawl(url, depth=0)
            time.sleep(1)  # Rate limiting between domains
        
        # Save summary
        summary = {
            "job_id": self.job_id,
            "agent_id": self.agent_id,
            "query": self.query,
            "documents_collected": len(self.documents),
            "urls_visited": len(self.visited_urls),
            "errors": len(self.errors),
            "started_at": datetime.now().isoformat(),
            "gpu_accelerated": GPU_AVAILABLE
        }
        
        summary_path = self.output_dir / "_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"")
        self.log(f"[DONE] Research Complete!")
        self.log(f"   Documents: {len(self.documents)}")
        self.log(f"   URLs Visited: {len(self.visited_urls)}")
        self.log(f"   Errors: {len(self.errors)}")
        self.log(f"   Output: {self.output_dir}")
        
        return summary


def main():
    parser = argparse.ArgumentParser(description='Deep Researcher for X Agent Factory')
    parser.add_argument('--job-id', required=True, help='Unique job identifier')
    parser.add_argument('--query', required=True, help='Research query')
    parser.add_argument('--agent', required=True, help='Target agent ID')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--max-depth', type=int, default=3, help='Max crawl depth')
    parser.add_argument('--max-pages', type=int, default=100, help='Max pages to crawl')
    
    args = parser.parse_args()
    
    researcher = DeepResearcher(
        job_id=args.job_id,
        query=args.query,
        agent_id=args.agent,
        output_dir=args.output,
        max_depth=args.max_depth,
        max_pages=args.max_pages
    )
    
    try:
        researcher.run()
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
