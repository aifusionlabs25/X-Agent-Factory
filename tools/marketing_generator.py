import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import argparse
from utils import load_env, load_json

def load_specialist(name):
    """Loads the persona context for a specialist."""
    path = f"specialists/{name}.txt"
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return f"You are {name}, an expert in your field."

import requests

import requests
import json
import time

OLLAMA_URL = "http://localhost:11434/api/generate"

def generate_marketing_copy(agent_name, vertical, tone="Persuasive"):
    # 1. Load Sparkle (V2.0)
    sparkle_context = load_specialist("Sparkle")
    
    print(f"✨ Sparkle: Dreaming up campaigns for '{agent_name}' ({vertical})...")
    
    # 2. Construct Prompt
    prompt = f"""
    {sparkle_context}
    
    [TASK]
    Create a 3-email cold outreach sequence for the '{vertical}' industry.
    We are selling '{agent_name}', an AI Agent that solves [PAIN_POINT: Missed Calls/Lost Revenue].
    
    REQUIREMENTS:
    - Subject lines must be scroll-stopping (under 40 chars).
    - Tone: {tone}, but punchy (Sparkle Style).
    - Call to Action: "30-second demo".
    
    OUTPUT FORMAT:
    JSON ONLY: {{ "email_1": {{ "subject": "...", "body": "..." }}, "email_2": ... }}
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
        
        # Output Results
        print("\n✨ SPARKLE'S CAMPAIGN:")
        print(json.dumps(result, indent=2))
        
        # Save to file
        output_path = f"agents/{agent_name.lower()}_{vertical.lower().replace(' ', '_')}/marketing_campaign.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
            print(f"\n✅ Campaign Saved: {output_path}")

        return result

    except Exception as e:
        print(f"❌ Sparkle Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python marketing_generator.py <agent_name> <vertical>")
    else:
        generate_marketing_copy(sys.argv[1], sys.argv[2])
