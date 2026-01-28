"""
DOJO ARCHITECT v1.0
The Shadow Surgeon.
Reads 'shadow_orders' and generates a proposed PATCH (diff).
Does NOT apply the patch to the live agent output.
"""

import json
import argparse
import difflib
import requests
from pathlib import Path

# Config
BASE_DIR = Path(__file__).parent
ORDERS_DIR = BASE_DIR / "shadow_orders"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Import Loader
try:
    from dojo_agent_loader import load_agent_data
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent))
    from dojo_agent_loader import load_agent_data

def generate_patch(agent_slug, system_prompt, required_fix):
    """
    Ask LLM to perform only the specific edit requested.
    Returns the new system prompt text.
    """
    prompt = f"""You are a PROMPT ARCHITECT.
    
    CURRENT SYSTEM PROMPT:
    {system_prompt}
    
    REQUIRED FIX:
    {required_fix}
    
    TASK:
    Rewrite the system prompt to incorporate the fix.
    - Change ONLY what is necessary.
    - Maintain all other constraints.
    - Do NOT add conversational filler.
    
    OUTPUT:
    The full updated system prompt content.
    """
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=120
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception as e:
        print(f"[ERROR] LLM Architect failed: {e}")
        return None

def create_diff_file(agent_slug, original, modified, order_id):
    """
    Create a unified diff file for review.
    """
    diff = difflib.unified_diff(
        original.splitlines(),
        modified.splitlines(),
        fromfile='system_prompt.txt (ORIGINAL)',
        tofile='system_prompt.txt (PROPOSED)',
        lineterm=''
    )
    
    diff_text = "\n".join(diff)
    
    # Save Patch
    patch_dir = ORDERS_DIR / agent_slug / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)
    patch_path = patch_dir / f"{order_id}.patch"
    
    with open(patch_path, "w", encoding="utf-8") as f:
        f.write(diff_text)
        
    print(f"\n[PATCH GENERATED] {patch_path}")
    print("Preview:\n")
    print("\n".join(diff_text.splitlines()[:20])) # Show first 20 lines
    return patch_path

def run_architect(order_path):
    order_path = Path(order_path)
    if not order_path.exists():
        print(f"[ERROR] Order not found: {order_path}")
        return

    with open(order_path, "r", encoding="utf-8") as f:
        order = json.load(f)
        
    agent_slug = order["agent"]
    print(f"--- ARCHITECT: Processing {order['id']} ---")
    print(f"Agent: {agent_slug}")
    print(f"Fix: {order['required_fix']}")
    
    # Load Agent
    try:
        agent_data = load_agent_data(agent_slug)
        current_prompt = agent_data["system_prompt"]
    except Exception as e:
        print(f"[FAIL] Could not load agent: {e}")
        return

    # Generate New Prompt
    print("Drafting fix with LLM...")
    new_prompt = generate_patch(agent_slug, current_prompt, order["required_fix"])
    
    if new_prompt and new_prompt != current_prompt:
        create_diff_file(agent_slug, current_prompt, new_prompt, order["id"])
    else:
        print("[FAIL] No changes generated or LLM failed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("order_path", help="Path to shadow change order JSON")
    args = parser.parse_args()
    
    run_architect(args.order_path)
