import sys
sys.stdout.reconfigure(encoding='utf-8')
import argparse
import os
import json
import requests
import time
from ddgs import DDGS
from bs4 import BeautifulSoup
from utils import load_env

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

def load_specialist(name):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'specialists', f'{name}.txt')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def generate_with_gemini(persona_context, prompt):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found.")
        return None

    full_prompt = f"{persona_context}\n\n{prompt}"
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}]
    }
    
    # Retry Loop (3 attempts)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{GEMINI_URL}?key={api_key}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # If 429 (Too Many Requests), raise status to trigger except block
            if response.status_code == 429:
                print(f"   ⚠️ Gemini Rate Limit (429). Waiting {2 * (attempt + 1)}s...")
                time.sleep(2 * (attempt + 1))
                continue
                
            response.raise_for_status()
            return response.json()['candidates'][0]['content']['parts'][0]['text']
            
        except Exception as e:
            print(f"   ⚠️ Gemini Attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print("❌ Gemini failed after max retries.")
                return None
    return None

def generate_with_ollama(persona_context, prompt, model="llama3"):
    full_prompt = f"{persona_context}\n\n{prompt}"
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "format": "json"
        })
        response.raise_for_status()
        data = response.json()
        return json.loads(data['response'])
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return None

# --- Step 1: The Brain (Troy) ---
def generate_criteria(vertical):
    print(f"   > 🏗️  Troy: Designing search criteria for '{vertical}'...")
    persona = load_specialist("Troy")
    
    prompt = f"""
    [[FACTORY_MODE]]
    {persona}
    
    [TASK]
    Generate 5 targeted DuckDuckGo search queries to find small-to-mid-sized businesses in the '{vertical}' industry.
    Focus on signals that indicate they need automation:
    - "Bad reviews" or "Complaint"
    - "Schedule appointment" (to find booking pages)
    - "Contact us" 
    - Specific location based queries (e.g. "Plumbers in [City] waiting list") -> Use generic placeholders like "in Denver" or "in Austin" for this demo.
    
    Return JSON ONLY:
    {{
        "queries": ["query1", "query2", ...]
    }}
    [/TASK]
    """
    
    response = generate_with_gemini(persona, prompt)
    if response:
        # Clean parse
        clean_json = response
        if "```" in response:
            parts = response.split("```")
            clean_json = parts[1]
            if clean_json.startswith("json"):
                clean_json = clean_json[4:].strip()
        elif "Troy Ready." in response:
             clean_json = response.split("Troy Ready.")[1].strip()
             
        try:
            return json.loads(clean_json)['queries']
        except:
            print("⚠️ Failed to parse Troy's criteria.")
    
    return [f"{vertical} businesses", f"{vertical} near me", f"{vertical} reviews"]

# --- Step 2: The Hands (WebWorker) ---
def perform_search(queries):
    results = []
    print(f"   > 🔎 WebWorker: Executing {len(queries)} search strategies...")
    
    with DDGS() as ddgs:
        for q in queries:
            print(f"     ...searching: '{q}'")
            try:
                # Get top 10 results per query
                search_res = list(ddgs.text(q, max_results=10))
                for r in search_res:
                    r['query_source'] = q
                    results.append(r)
                time.sleep(2) # Polite delay
            except Exception as e:
                print(f"     ⚠️ Search error: {e}")
                
    # Deduplicate by URL
    unique_results = {r['href']: r for r in results}.values()
    print(f"     > Found {len(unique_results)} unique leads.")
    return list(unique_results)

def fetch_homepage_snippet(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ')
        return text[:1000] # Just enough for Nova to smell the vibe
    except:
        return ""

# --- Step 3: The Filter (Nova) ---
def score_leads(leads, vertical):
    print(f"   > 💠 Nova: Scoring {len(leads)} leads for Quality & Automation Fit...")
    persona = load_specialist("Nova")
    
    qualified = []
    ignorable_domains = ["yelp.com", "angi.com", "thumbtack.com", "facebook.com", "linkedin.com", "yellowpages.com", "bbb.org", "homeadvisor.com", "porch.com"]
    
    for lead in leads:
        # 1. Pre-Filter Aggregators
        if any(domain in lead['href'] for domain in ignorable_domains):
            print(f"     - [Skip] Aggregator detected: {lead['title'][:20]}...")
            continue

        # 2. Quick spider for context
        snippet = fetch_homepage_snippet(lead['href'])
        if not snippet:
             print(f"     - [Skip] Could not fetch site: {lead['title'][:20]}...")
             continue
        
        prompt = f"""
        [[FACTORY_MODE]]
        {persona}
        
        [LEAD DATA]
        Vertical: {vertical}
        Title: {lead['title']}
        URL: {lead['href']}
        Snippet: {lead['body']}
        Homepage Preview: {snippet}
        
        [TASK]
        Score this lead (0-10) on "Likelihood to need AI Automation".
        - High Score (6-10): Bad website, mentions "call us", complaints in snippet, manual scheduling, small local biz.
        - Low Score (0-5): Has "ServiceTitan", modern UI, enterprise corp, government site.
        
        Return JSON ONLY:
        {{
            "score": <int>,
            "reason": "...",
            "pass": <bool> (True if score >= 4)
        }}
        [/TASK]
        """
        
        # Using Llama 3 for speed/cost on the "Factory Floor"
        evaluation = generate_with_ollama(persona, prompt)
        
        if evaluation:
            # Safely extract score with type coercion
            raw_score = evaluation.get('score')
            try:
                score = int(raw_score) if raw_score is not None else 0
            except (ValueError, TypeError):
                score = 0
            
            print(f"     - [{score}/10] {lead['title'][:30]}... ({evaluation.get('pass')})")
            
            # Lowering threshold AND trusting the explicit 'pass' bool more
            if score >= 4:
                lead['nova_score'] = score
                lead['nova_reason'] = evaluation.get('reason', 'No reason provided')
                qualified.append(lead)
        else:
            print(f"     - [?] {lead['title'][:30]}... (Skipped)")



    return qualified

def run_prospect_scout(vertical):
    load_env()
    print(f"🚀 Prospect Scout Initiated for: {vertical}")
    
    # 1. Brain
    queries = generate_criteria(vertical)
    
    # 2. Hands
    raw_leads = perform_search(queries)
    
    # 3. Filter
    qualified_leads = score_leads(raw_leads, vertical)
    
    # 4. Save
    output_dir = "intelligence/leads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"{vertical.lower().replace(' ', '_')}_qualified.json"
    path = os.path.join(output_dir, filename)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(qualified_leads, f, indent=2)
        
    print(f"\n✅ Prospecting Complete.")
    print(f"   🎯 Qualified Leads: {len(qualified_leads)}")
    print(f"   💾 Saved to: {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prospect Scout Tool")
    parser.add_argument("vertical", help="Target Vertical (e.g. 'Plumbers')")
    args = parser.parse_args()
    
    run_prospect_scout(args.vertical)
