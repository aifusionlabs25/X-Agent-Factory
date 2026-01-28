"""
DOJO AGENT LOADER
Adapter layer to resolve X Agent Factory paths and load agent artifacts.
"""

import os
import json
from pathlib import Path

# Factory Base Dir (Assumes this script is in tools/evaluation/dojo/)
FACTORY_DIR = Path(__file__).parent.parent.parent.parent
AGENTS_ROOT = FACTORY_DIR / "agents" / "clients"

def resolve_agent_paths(client_slug):
    """
    Resolve absolute paths for a given client slug.
    Returns dict of paths or None if not found.
    """
    agent_dir = AGENTS_ROOT / client_slug
    
    if not agent_dir.exists():
        return None
        
    paths = {
        "root": agent_dir,
        "system_prompt": agent_dir / "system_prompt.txt",
        "persona_profile": agent_dir / "persona_profile.json",
        "persona_context": agent_dir / "persona_context.txt",
        "manifest": agent_dir / "kb_manifest.json"
    }
    
    return paths

def load_agent_data(client_slug):
    """
    Load all critical agent data for simulation.
    Returns dict with content and metadata.
    """
    paths = resolve_agent_paths(client_slug)
    if not paths:
        raise ValueError(f"Agent client_slug '{client_slug}' not found in {AGENTS_ROOT}")
        
    data = {
        "slug": client_slug,
        "system_prompt": "",
        "persona": {},
        "context": "",
        "meta": {}
    }
    
    # 1. System Prompt
    if paths["system_prompt"].exists():
        with open(paths["system_prompt"], "r", encoding="utf-8") as f:
            data["system_prompt"] = f.read()
            
    # 2. Persona Profile (Metadata)
    if paths["persona_profile"].exists():
        with open(paths["persona_profile"], "r", encoding="utf-8") as f:
            data["persona"] = json.load(f)
            
    # 3. Context (Optional)
    if paths["persona_context"].exists():
        with open(paths["persona_context"], "r", encoding="utf-8") as f:
            data["context"] = f.read()
            
    # 4. Extract Identity
    identity = data["persona"].get("identity", {})
    data["meta"]["name"] = identity.get("agent_display_name", "Agent")
    data["meta"]["role"] = identity.get("role_title", "Specialist")
    
    return data

if __name__ == "__main__":
    import sys
    # Quick Test
    slug = sys.argv[1] if len(sys.argv) > 1 else "knowles_law_firm"
    try:
        agent = load_agent_data(slug)
        print(f"[OK] Loaded {agent['meta']['name']}")
        print(f"     Prompt Length: {len(agent['system_prompt'])}")
    except Exception as e:
        print(f"[FAIL] {e}")
