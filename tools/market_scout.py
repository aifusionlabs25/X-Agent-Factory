import sys
# Force UTF-8 output for Windows console emoji support
sys.stdout.reconfigure(encoding='utf-8')
import argparse
import json
import random
import os
import requests
import time
from datetime import datetime
from duckduckgo_search import DDGS
from utils import save_json, get_timestamp

# Configuration
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'intelligence', 'daily_opportunities.json')
OLLAMA_URL = "http://localhost:11434/api/generate"

def load_specialist(name):
    """Loads the persona context from the specialists directory."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'specialists', f'{name}.txt')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def perform_search(query):
    """Performs a real-time web search using DuckDuckGo."""
    print(f"   > 🔎 WebWorker: Searching external web for '{query}'...")
    try:
        results = DDGS().text(query, max_results=3)
        summary = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return summary
    except Exception as e:
        print(f"   > ⚠️ Search failed: {e}")
        return "No external data available."

def scan_vertical_live(vertical):
    """Scans a vertical using Llama 3 with WebWorker Persona."""
    print(f"   > 🔭 WebWorker: Surfing the ecosystem for '{vertical}'...")
    
    # Load Persona
    persona = load_specialist("WebWorker")
    
    # Perform Live Search
    search_query = f"{vertical} industry major pain points SOFTWARE AUTOMATION 2024"
    search_results = perform_search(search_query)

    prompt = f"""
    [[FACTORY_MODE]]
    {persona}

    [REAL-TIME SEARCH DATA]
    {search_results}
    
    [TASK]
    Act as WebWorker. Analyze the '{vertical}' industry using the Search Data above.
    Identify ONE critical pain point that software automation (AI Agents) could solve.
    
    Return JSON ONLY:
    {{
        "pain_point": "Impactful problem description based on search data",
        "source": "Cite a specific finding from search data",
        "tam_score": <float between 6.0 and 9.9 based on urgency>,
        "competitors": ["Competitor1", "Competitor2"],
        "recommendation": "BUILD" or "WAIT"
    }}
    [/TASK]
    """
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        })
        response.raise_for_status()
        data = response.json()
        result = json.loads(data['response'])
        
        # Add metadata
        result['id'] = f"opp_{int(time.time())}"[-6:]
        result['vertical'] = vertical
        return result
        
    except Exception as e:
        print(f"❌ Error scanning {vertical}: {e}")
        # Fallback for stability if Ollama fails mid-scan
        return {
            "id": "err_001",
            "vertical": vertical,
            "pain_point": "Scan failed - defaulting to manual review",
            "source": "System Error",
            "tam_score": 0.0,
            "competitors": [],
            "recommendation": "WAIT"
        }

def run_scout():
    print("🔭 Market Scout: R&D Engine Starting (LIVE MODE)...")
    
    # Target Sectors to Scan
    sectors = ["Veterinary", "Home Services", "Dental", "Legal"]
    opportunities = []

    for sector in sectors:
        opp = scan_vertical_live(sector)
        opportunities.append(opp)
        time.sleep(1) # Courtesy delay

    # Analysis Logic
    top_picks = sorted(opportunities, key=lambda x: x['tam_score'], reverse=True)
    
    # Generate Report
    report = {
        "generated_at": datetime.now().isoformat(),
        "scan_summary": f"Scanned {len(sectors)} sources via Llama 3.",
        "top_opportunities": top_picks
    }
    
    # Save Report
    save_json(OUTPUT_FILE, report)
    
    # Print Summary to Console
    print("\n📊 DAILY OPPORTUNITY REPORT (LIVE)")
    print("="*40)
    for opp in top_picks:
        status_icon = "🟢" if opp['recommendation'] == "BUILD" else "🔴"
        print(f"{status_icon} [{opp['tam_score']}] {opp['vertical']}: {opp['pain_point']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Market Scout")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    args = parser.parse_args()
    
    run_scout()
