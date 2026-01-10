import sys
sys.stdout.reconfigure(encoding='utf-8')
import argparse
import os
import json
import time
import warnings
# Suppress the "backend='api' is deprecated" warning because it's the only one that works.
warnings.filterwarnings("ignore", category=UserWarning, module="duckduckgo_search")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="duckduckgo_search")
# Replaced DDG with Google
from googlesearch import search
from bs4 import BeautifulSoup
from utils import load_env, extract_json_from_text
from gemini_helper import call_gemini

# --- Step 1: The Brain (Troy) ---
def load_specialist(name):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'specialists', f'{name}.txt')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def generate_criteria(vertical):
    print(f"   > 🏗️  Troy: Designing search criteria for '{vertical}'...")
    persona = load_specialist("Troy")
    
    # One-Shot Prompt (Morgan Protocol)
    prompt = f"""
    [TASK]
    Generate 5 targeted Google search queries to find small-to-mid-sized businesses in the '{vertical}' industry.
    Focus on keywords that reveal them, NOT full sentences.
    
    [EXAMPLE OUTPUT]
    {{
        "queries": [
            "Plumbers Phoenix bad reviews",
            "Emergency plumbing Denver",
            "Plumbing contact form",
            "Schedule plumbing online",
            "Local plumber complaint"
        ]
    }}
    
    [INSTRUCTION]
    Return VALID JSON ONLY. No markdown formatted blocks. Use SHORT KEYWORDS.
    [/TASK]
    """
    
    response = call_gemini(prompt, persona_context=persona, context_label="scout_criteria")
    
    if response:
        # Robust Parsing (Updated for Llama 3)
        data = extract_json_from_text(response)
        if data and 'queries' in data:
            # Clean queries (Strip brackets/quotes that Llama might hallucinate)
            cleaned_queries = [q.strip("[]\"' ") for q in data['queries']]
            return cleaned_queries
        else:
            print(f"⚠️ Failed to parse Troy's criteria (Raw len: {len(response)}).")

    # Fallback
    print("   ⚠️ Troy failed. Using generic fallback queries.")
    return [f"{vertical} businesses", f"{vertical} near me", f"{vertical} reviews"]

# Replaced Manual Scraper with DDGS (backend='api' verified working)
from ddgs import DDGS

# --- Step 2: The Hands (WebWorker) ---
def perform_search(queries):
    results = []
    print(f"   > 🔎 WebWorker: Executing {len(queries)} search strategies (via DDG API)...")
    
    for q in queries:
        print(f"     ...searching: '{q}'")
        try:
            # Verified working backend: 'api' (Legacy but reliable)
            with DDGS() as ddgs:
                search_res = list(ddgs.text(q, backend='api', max_results=5))
                
                print(f"     -> Hits: {len(search_res)}")
                for r in search_res:
                    results.append({
                        'title': r.get('title', 'Unknown Title'),
                        'href': r.get('href', ''),
                        'body': r.get('body', ''),
                        'query_source': q
                    })
                time.sleep(1) # Polite delay
        except Exception as e:
            print(f"     ⚠️ Search error: {e}")
                
    # Deduplicate by URL
    unique_results = {r.get('href'): r for r in results if r.get('href')}.values()
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
import requests

def score_leads(leads, vertical):
    print(f"   > 💠 Nova: Scoring {len(leads)} leads for Quality & Automation Fit...")
    persona = load_specialist("Nova")
    
    qualified = []
    ignorable_domains = ["yelp.com", "angi.com", "thumbtack.com", "facebook.com", "linkedin.com", "yellowpages.com", "bbb.org", "homeadvisor.com", "porch.com"]
    
    for lead in leads:
        # 1. Pre-Filter Aggregators
        if any(domain in lead['href'] for domain in ignorable_domains):
            continue

        # 2. Quick spider for context
        snippet = fetch_homepage_snippet(lead['href'])
        
        # If we have no snippet and no body, it's a dead lead
        if not snippet and not lead.get('body'):
             continue
             
        # Use body as fallback snippet if fetch failed
        if not snippet:
            snippet = lead.get('body', '')
        
        # One-Shot Prompt for Nova
        prompt = f"""
        [LEAD DATA]
        Vertical: {vertical}
        Title: {lead['title']}
        URL: {lead['href']}
        Snippet: {lead.get('body', '')}
        Homepage Preview: {snippet}
        
        [TASK]
        Score this lead (0-10) on "Likelihood to need AI Automation".
        
        [EXAMPLE OUTPUT]
        {{
            "score": 8,
            "reason": "Site mentions 'Call for appointment' and has no booking widget.",
            "pass": true
        }}
        
        Return VALID JSON ONLY.
        [/TASK]
        """
        
        # Using Local Llama
        response = call_gemini(prompt, persona_context=persona, context_label="nova_score")
        
        if response:
            evaluation = extract_json_from_text(response)
            
            if evaluation:
                try:
                    score = int(evaluation.get('score', 0))
                    
                    print(f"     - [{score}/10] {lead['title'][:30]}... ({evaluation.get('pass')})")
                    
                    if score >= 5: # Threshold
                        lead['nova_score'] = score
                        lead['nova_reason'] = evaluation.get('reason', 'No reason provided')
                        qualified.append(lead)
                except:
                     print(f"     - [?] Failed to parse score for {lead['title'][:15]}...")
            else:
                 print(f"     - [?] Failed to parse JSON for {lead['title'][:15]}...")

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
