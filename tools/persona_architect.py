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
    return f"You are {name}, an expert Systems Architect."

import requests
import json

# Configuration
load_env()
API_KEY = os.getenv("GOOGLE_API_KEY")

def generate_with_gemini(system_prompt, user_message):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_message}]} 
        ]
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return None

def build_persona(vertical, agent_name):
    # 1. Load Troy
    troy_context = load_specialist("Troy")
    
    print(f"🏗️ Troy: Architecting system prompt for '{agent_name}' ({vertical})...")
    
    # 2. Load Vertical Template
    template_path = f"templates/vertical_templates/{vertical.lower().replace(' ', '_')}.json"
    template_data = load_json(template_path)
    
    if not template_data:
        print(f"❌ Template not found for {vertical}")
        return

    # 3. Architect System Prompt
    prompt_request = f"""
    [INPUT DATA]
    Vertical: {template_data['vertical_name']}
    Agent Name: {template_data['agent_name']}
    Role: {template_data['role']}
    Tone: {template_data['tone']}
    Pain Points: {template_data['pain_points']}
    Protocols: {json.dumps(template_data.get('triage_protocol', {}))}
    
    [INSTRUCTION]
    Design a 'System Prompt' for this agent. 
    Use your [PrmptEngnrgExp] to ensure it adheres to the [PRMPTINJ] safety standards.
    The output should be the raw system prompt text to quite literally 'program' the agent.
    """
    
    system_prompt_content = generate_with_gemini(troy_context, prompt_request)
    
    if system_prompt_content:
        # Save
        agent_dir = f"agents/{agent_name.lower()}_{vertical.lower().replace(' ', '_')}"
        if not os.path.exists(agent_dir):
            os.makedirs(agent_dir)
            
        with open(f"{agent_dir}/system_prompt_v2.txt", "w", encoding='utf-8') as f:
            f.write(system_prompt_content)
        print(f"✅ Troy has forged the System Prompt: {agent_dir}/system_prompt_v2.txt")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python persona_architect.py <vertical> <agent_name>")
    else:
        build_persona(sys.argv[1], sys.argv[2])
