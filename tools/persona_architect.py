import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import argparse
import json
from utils import load_env, load_json
import requests

# Configuration
load_env()

# --- STYLE GUIDELINES (The "Morgan Protocol") ---
# Injected into every Agent Skeleton to ensure high quality.
STYLE_INJECTION = """
[CRITICAL CONFIGURATION]
You must enforce the following Style Guidelines in the System Prompt:
1. **NO FILLERS**: Ban phrases like 'Got it', 'Sure thing', 'I understand'.
2. **CONCISENESS**: Limit responses to 2-3 sentences unless explaining complex concepts.
3. **PRONUNCIATION**: If the word 'live' refers to real-time, pronounce it 'l-eye-v'.
4. **NAME USAGE**: Use the user's name ONLY in the Greeting and Goodbye. Never in between.
"""

def generate_with_ollama(prompt, persona_context, context_label=""):
    """Generates content using local Ollama instance."""
    print(f"   🧠 Llama 3 Thinking ({context_label})...")
    OLLAMA_URL = "http://localhost:11434/api/generate"
    
    full_prompt = f"{persona_context}\n\n{prompt}"
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": full_prompt,
            "stream": False
        })
        response.raise_for_status()
        data = response.json()
        return data['response']
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return None

def load_specialist(name):
    """Loads the persona context for a specialist."""
    path = f"specialists/{name}.txt"
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return f"You are {name}, an expert Systems Architect."

def build_persona(vertical, agent_name, output_dir=None):
    # 1. Load Troy (The Architect)
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
    
    {STYLE_INJECTION}
    
    Do not include fluff. Output raw text for the LLM.
    """
    
    # Using local Llama 3
    skeleton_content = generate_with_ollama(
        prompt=prompt_request_skeleton, 
        persona_context=troy_context,
        context_label=f"architect_skeleton_{agent_name}"
    )
    
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
    Ensure the tone aligns with: {template_data['tone']}
    """
    
    # Using local Llama 3
    soul_content = generate_with_ollama(
        prompt=prompt_request_soul, 
        persona_context=troy_context,
        context_label=f"architect_soul_{agent_name}"
    )
    
    # Clean Parse & Save Both
    if output_dir:
        agent_dir = output_dir
    else:
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
    parser = argparse.ArgumentParser(description="Persona Architect Tool")
    parser.add_argument("vertical", help="Industry Vertical (e.g. Veterinarian)")
    parser.add_argument("agent_name", help="Agent Name (e.g. Ava)")
    parser.add_argument("--output_dir", help="Output directory", default=None)
    
    args = parser.parse_args()
    
    build_persona(args.vertical, args.agent_name, args.output_dir)
