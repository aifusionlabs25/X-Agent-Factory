import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import requests
import json
import argparse
from utils import load_env, load_json

load_env()
TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")

# Base API URL (Phoenix/V2)
# Note: Using standard V2 endpoint. Update if specific enterprise endpoint is required.
BASE_URL = "https://api.tavus.io/v2"

def deploy_agent(agent_name):
    print(f"🚀 Deployment: Preparing to deploy '{agent_name}' to Tavus...")
    
    # 1. Locate Artifacts
    agent_dir = f"agents/{agent_name.lower()}"
    sys_prompt_path = f"{agent_dir}/system_prompt.txt"
    
    if not os.path.exists(sys_prompt_path):
        # Try finding directory by partial match if exact match fails
        found = False
        for d in os.listdir("agents"):
            if agent_name.lower() in d:
                sys_prompt_path = f"agents/{d}/system_prompt.txt"
                agent_dir = f"agents/{d}"
                found = True
                break
        if not found:
            print(f"❌ Error: Agent artifacts not found for '{agent_name}'.")
            return

    print(f"   > Loading Identity from: {sys_prompt_path}")
    with open(sys_prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read()

    # 2. Create Persona/Replica
    # This creates a new conversation replica with the specific system prompt
    url = f"{BASE_URL}/replicas"
    headers = {
        "x-api-key": TAVUS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "replica_name": f"{agent_name} (Factory Deployed)",
        "system_prompt": system_prompt,
        "context": "Factory Automated Deployment"
    }
    
    print("   > Contacting Tavus Orbital Network...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        replica_id = data.get('replica_id') or data.get('id')
        print(f"✅ Deployment Successful!")
        print(f"   > Replica ID: {replica_id}")
        
        # Save Deployment Record
        record = {
            "deployed_at": "timestamp_here", # simplified
            "replica_id": replica_id,
            "platform": "Tavus"
        }
        with open(f"{agent_dir}/deployment.json", "w", encoding='utf-8') as f:
            json.dump(record, f, indent=4)
            
    except Exception as e:
        print(f"❌ Deployment Failed: {e}")
        if 'response' in locals():
            print(f"   > Response: {response.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deploy_agent.py <agent_name>")
    else:
        deploy_agent(sys.argv[1])
