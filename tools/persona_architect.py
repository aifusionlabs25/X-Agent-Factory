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

    # 3. Architect System Prompt (The Skeleton)
    prompt_request_skeleton = f"""
    [INPUT DATA]
    Vertical: {template_data['vertical_name']}
    Agent Name: {template_data['agent_name']}
    Role: {template_data['role']}
    Protocols: {json.dumps(template_data.get('triage_protocol', {}))}
    
    [INSTRUCTION]
    Design the 'System Prompt' (The Skeleton).
    Focus ONLY on Logic, Guardrails, Step-by-step Protocols, and Safety.
    Do not include fluff. Output raw text for the LLM.
    """
    
    skeleton_content = generate_with_gemini(troy_context, prompt_request_skeleton)
    
    # 4. Architect Persona Context (The Soul)
    prompt_request_soul = f"""
    [INPUT DATA]
    Vertical: {template_data['vertical_name']}
    Agent Name: {template_data['agent_name']}
    Tone: {template_data['tone']}
    Pain Points: {template_data['pain_points']}
    
    [INSTRUCTION]
    Design the 'Persona Context' (The Soul).
    Focus ONLY on Vibe, Voice, Backstory, and deeply held beliefs.
    This is for a Tavus Video Replica to 'act' the part.
    """
    
    soul_content = generate_with_gemini(troy_context, prompt_request_soul)
    
    # Clean Parse & Save Both
    agent_dir = f"agents/{agent_name.lower()}_{vertical.lower().replace(' ', '_')}"
    if not os.path.exists(agent_dir):
        os.makedirs(agent_dir)

    # Save Skeleton
    if skeleton_content:
        clean_skeleton = skeleton_content
        if "Troy Ready." in skeleton_content:
             clean_skeleton = skeleton_content.split("Troy Ready.")[1].strip()
        with open(f"{agent_dir}/system_prompt.txt", "w", encoding='utf-8') as f:
            f.write(clean_skeleton.strip())
            
    # Save Soul
    if soul_content:
        clean_soul = soul_content
        if "Troy Ready." in soul_content:
             clean_soul = soul_content.split("Troy Ready.")[1].strip()
        with open(f"{agent_dir}/persona_context.txt", "w", encoding='utf-8') as f:
            f.write(clean_soul.strip())

    print(f"✅ Troy has forged the Agent: {agent_dir}")
    print(f"   💀 Skeleton: system_prompt.txt")
    print(f"   👻 Soul: persona_context.txt")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python persona_architect.py <vertical> <agent_name>")
    else:
        build_persona(sys.argv[1], sys.argv[2])
