import sys
# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

import os
import requests
import json
from utils import load_env, load_json, save_json, ensure_directory

# Load Environment
load_env()
API_KEY = os.getenv("GOOGLE_API_KEY")

def generate_kb_content(template_data):
    """Uses Gemini Pro to generate a Knowledge Base from the template."""
    print("🧠 Generator: contacting Gemini Pro 1.5...")
    
    prompt = f"""
    You are an expert Veterinary Triage Architect.
    Create a comprehensive Knowledge Base text file for an AI Agent named '{template_data['agent_name']}'.
    
    CONTEXT:
    Vertical: {template_data['vertical_name']}
    Tone: {template_data['tone']}
    
    PROTOCOLS TO IMPLEMENT:
    {json.dumps(template_data.get('triage_protocol', {}), indent=2)}
    
    OUTPUT FORMAT:
    - Pure text, organized by headers.
    - Q&A style for common issues (Vomiting, Diarrhea, Bleeding).
    - clear instructions on when to escalate to human.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        return None

def build_system_prompt(template_data, content_summary):
    """Interpolates the master system prompt."""
    with open('templates/system_prompt_template.txt', 'r', encoding='utf-8') as f:
        master_prompt = f.read()
    
    filled_prompt = master_prompt.replace("{{AGENT_NAME}}", template_data['agent_name'])
    filled_prompt = filled_prompt.replace("{{VERTICAL_NAME}}", template_data['vertical_name'])
    filled_prompt = filled_prompt.replace("{{CONTEXT_DESCRIPTION}}", f"Automated triage for {template_data['vertical_name']} clinics.")
    filled_prompt = filled_prompt.replace("{{PRIMARY_GOAL}}", "Efficient triage and appointment scheduling.")
    filled_prompt = filled_prompt.replace("{{TONE_VOICE}}", template_data['tone'])
    
    return filled_prompt

def run_generator(vertical):
    print(f"🏗️ Architect: Building Agent for '{vertical}'...")
    
    # 1. Load Template
    template_path = f"templates/vertical_templates/{vertical.lower()}.json"
    data = load_json(template_path)
    if not data:
        print("❌ Template not found.")
        return

    # 2. Generate KB (The "Brain")
    kb_content = generate_kb_content(data)
    if not kb_content:
        return

    # 3. Save Artifacts
    agent_dir = f"agents/{data['agent_name'].lower()}_{vertical.lower()}"
    ensure_directory(agent_dir)
    
    # Save KB
    with open(f"{agent_dir}/knowledge_base.txt", "w", encoding='utf-8') as f:
        f.write(kb_content)
    print(f"✅ KB Generated: {agent_dir}/knowledge_base.txt")
    
    # 4. Generate & Save System Prompt (The "Identity")
    sys_prompt = build_system_prompt(data, "KB Generated from protocols.")
    with open(f"{agent_dir}/system_prompt.txt", "w", encoding='utf-8') as f:
        f.write(sys_prompt)
    print(f"✅ System Prompt Created: {agent_dir}/system_prompt.txt")
    
    print("🏗️ Agent Architecture Complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python kb_generator.py <vertical>")
    else:
        run_generator(sys.argv[1])
