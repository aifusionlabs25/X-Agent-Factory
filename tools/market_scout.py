import sys
# Force UTF-8 output for Windows console emoji support
sys.stdout.reconfigure(encoding='utf-8')
import argparse
import json
import random
import os
from utils import save_json, get_timestamp

# Configuration
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'intelligence', 'daily_opportunities.json')

# Mock Data Sources (In a real scenario, this would scrape Reddit/Forums)
PAIN_POINTS = [
    {"source": "r/Veterinary", "text": "I spend 2 hours a day just calling back clients to triage.", "sentiment": "negative", "vertical": "Veterinary"},
    {"source": "r/Plumbing", "text": "Dispatching is a nightmare. I need an AI to handle the phone.", "sentiment": "negative", "vertical": "Home Services"},
    {"source": "r/Dentistry", "text": "No shows are killing my practice. We need automated reminders that people actually answer.", "sentiment": "negative", "vertical": "Dental"},
    {"source": "Twitter", "text": "Why is it so hard to find a good lawyer? They never pick up.", "sentiment": "negative", "vertical": "Legal"}
]

COMPETITORS = {
    "Veterinary": ["VitusVet", "PetDesk"],
    "Home Services": ["ServiceTitan", "Housecall Pro"],
    "Dental": ["Solutionreach", "Lighthouse 360"],
    "Legal": ["Clio", "MyCase"]
}

def scan_pain_points():
    """Simulates scanning for high-frequency pain points."""
    print("🔭 Scout: Scanning social channels (Reddit, Twitter, Forums)...")
    # In V2, this will be replaced with actual scraping logic
    return PAIN_POINTS

def calculate_tam(vertical):
    """Simulates TAM calculation (mock logic)."""
    # Logic: Random base score * Urgency Multiplier
    base_score = random.uniform(5.0, 9.0)
    urgency_map = {"Veterinary": 1.2, "Home Services": 1.1, "Dental": 1.0, "Legal": 0.9}
    
    score = base_score * urgency_map.get(vertical, 1.0)
    return min(round(score, 1), 10.0)

def analyze_opportunity(pain_point):
    """Analyzes a single pain point to generate an opportunity card."""
    vertical = pain_point["vertical"]
    score = calculate_tam(vertical)
    
    return {
        "id": f"opp_{random.randint(1000, 9999)}",
        "vertical": vertical,
        "pain_point": pain_point["text"],
        "source": pain_point["source"],
        "tam_score": score,
        "competitors": COMPETITORS.get(vertical, []),
        "recommendation": "BUILD" if score > 8.0 else "WAIT"
    }

def run_scout():
    """Main execution function."""
    print(f"🏗️ Forge: Starting Market Scout... [{get_timestamp()}]")
    
    pain_points = scan_pain_points()
    opportunities = []
    
    print(f"🔍 Found {len(pain_points)} potential signals.")
    
    for pp in pain_points:
        opp = analyze_opportunity(pp)
        opportunities.append(opp)
        print(f"   > Analyzed {pp['vertical']}: Score {opp['tam_score']} ({opp['recommendation']})")
    
    # Sort by Score
    opportunities.sort(key=lambda x: x['tam_score'], reverse=True)
    
    report = {
        "generated_at": get_timestamp(),
        "scan_summary": f"Scanned {len(pain_points)} sources.",
        "top_opportunities": opportunities
    }
    
    save_json(OUTPUT_FILE, report)
    print(f"✅ Daily Opportunity Report saved to: {OUTPUT_FILE}")
    print("🔭 Scout Mission Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Market Scout")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    args = parser.parse_args()
    
    run_scout()
