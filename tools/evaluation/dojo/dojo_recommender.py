"""
DOJO RECOMMENDER v1.0
CLI tool to suggest agent configurations based on standard roles.
Usage: python dojo_recommender.py --role <ROLE_ID>
"""

import json
import argparse
import sys
from pathlib import Path

# Fix path to point to actual location of role_map.json relative to this script
# Script is in: tools/evaluation/dojo/
# Map is in: docs/reasoning/
# So ../../../docs/reasoning/role_map.json
BASE_DIR = Path(__file__).parent.parent.parent.parent
ROLE_MAP_PATH = BASE_DIR / "docs" / "reasoning" / "role_map.json"

def load_role_map():
    if not ROLE_MAP_PATH.exists():
        print(f"[ERROR] Role map not found at {ROLE_MAP_PATH}")
        sys.exit(1)
    
    with open(ROLE_MAP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def recommend(role_id):
    data = load_role_map()
    roles = data.get("roles", {})
    
    if role_id not in roles:
        print(f"[ERROR] Role '{role_id}' not found.")
        print("Available Roles:", ", ".join(roles.keys()))
        return

    config = roles[role_id]
    
    print(f"\n--- DOJO RECOMMENDATION: {role_id} ---")
    print(f"Risk Tier: {config.get('risk_tier', 'UNRATED')}")
    if config.get('risk_notes'):
        print(f"Risk Notes: {config.get('risk_notes')}")
    print(f"Description: {config.get('description', 'N/A')}")
    print(f"Pass Gates: {config.get('min_pass_gates', [])}")
    
    print("\n[COPY-PASTE CONFIGURATION]")
    
    # Reasoning Profile Snippet
    profile_snippet = {
        "recommended_presets": config.get('recommended_presets'),
        "required_artifacts": config.get('required_artifacts')
    }
    print("\n--- persona_profile.json (Snippet) ---")
    print(json.dumps(profile_snippet, indent=2))
    
    # Scorer Snippet
    hard_gates = config.get('hard_gates')
    print("\n--- dojo_scorer.py (Hard Gates) ---")
    print(f"banned_terms = {json.dumps(hard_gates)}")
    
    print("\n[DOJO PACKS]")
    packs = config.get('dojo_packs', {})
    print(f"packs = {json.dumps(packs, indent=2)}")
        
    print("\n[NEXT STEPS]")
    print(f"  1. Paste the profile snippet into your agent's persona_profile.json.")
    print(f"  2. Update dojo_scorer.py with the banned_terms list.")
    print(f"  3. Run baseline: dojo run <agent> {packs.get('L1', 'basic')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", help="Target Role ID (e.g. LEGAL_INTAKE)")
    parser.add_argument("--list", action="store_true", help="List available roles")
    args = parser.parse_args()
    
    if args.list:
        data = load_role_map()
        print("Available Roles:", ", ".join(data.get("roles", {}).keys()))
    elif args.role:
        recommend(args.role.upper())
    else:
        parser.print_help()
