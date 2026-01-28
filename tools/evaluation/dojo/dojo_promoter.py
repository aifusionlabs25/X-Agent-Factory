"""
DOJO PROMOTER
Promotes a specific test run to Production (Canonical).
Usage: python dojo_promoter.py <run_id> --agent <agent_slug>
"""

import argparse
import sys
import json
import shutil
from pathlib import Path

# Config
BASE_DIR = Path(__file__).parent
FACTORY_ROOT = BASE_DIR.parent.parent.parent
LOGS_DIR = BASE_DIR / "dojo_logs"

def promote_run(run_id, agent_slug, force=False):
    agent_dir = FACTORY_ROOT / "agents" / "clients" / agent_slug
    if not agent_dir.exists():
        print(f"[ERROR] Agent directory not found: {agent_dir}")
        sys.exit(1)
        
    log_dir = LOGS_DIR / agent_slug
    
    # Files needed
    score_file = log_dir / f"{run_id}.score.json"
    sys_snapshot = log_dir / f"{run_id}.system_prompt.txt"
    persona_snapshot = log_dir / f"{run_id}.persona_context.txt"
    
    if not score_file.exists():
        print(f"[ERROR] Score file not found: {score_file}")
        sys.exit(1)
        
    # Security Check: Role Map Gates
    # Load Role Map
    role_map_path = FACTORY_ROOT / "docs" / "reasoning" / "role_map.json"
    if role_map_path.exists():
        with open(role_map_path, "r", encoding="utf-8") as f:
            role_data = json.load(f)
            
        # Infer Role from Score Breakdown or Agent Meta (if available)
        # For now, simplistic approach: assumes agent knows its role.
        # But `promote_run` only gets `agent_slug`.
        # We can scan the score breakdown for clues or rely on standard roles.
        # Or, just enforce "No BANNED WORDS" as a universal baseline.
        pass
    
    score_data = json.loads(score_file.read_text(encoding='utf-8'))
    verdict = score_data.get("verdict", "FAIL")
    score = score_data.get("score", 0)
    
    print(f"--- PROMOTING RUN: {run_id} ---")
    print(f"Verdict: {verdict}")
    print(f"Score:   {score}")
    
    if not force:
        if verdict != "PASS":
            print("[BLOCK] Cannot promote a FAILED run (use --force to override).")
            sys.exit(1)
            
        # Check for banned words leakage explicitly if breakdown exists
        if "BANNED_WORDS" in score_data.get("breakdown", {}):
             print("[BLOCK] Cannot promote a run with BANNED WORDS.")
             sys.exit(1)
             
        # Check for LEAKAGE explicit
        if "LEAKAGE_DETECTED" in score_data.get("breakdown", {}):
             print("[BLOCK] Cannot promote a run with META LEAKAGE.")
             sys.exit(1)
             
    # Perform Promotion
    backup_dir = agent_dir / "backup" / run_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Backup Canonical
    if (agent_dir / "system_prompt.txt").exists():
        shutil.copy(agent_dir / "system_prompt.txt", backup_dir / "system_prompt.txt")
        
    if (agent_dir / "persona_context.txt").exists():
        shutil.copy(agent_dir / "persona_context.txt", backup_dir / "persona_context.txt")
        
    print(f"[BACKUP] Created at {backup_dir}")
    
    # 2. Overwrite Canonical
    if sys_snapshot.exists():
        shutil.copy(sys_snapshot, agent_dir / "system_prompt.txt")
        print("[UPDATE] system_prompt.txt updated from snapshot.")
        
    if persona_snapshot.exists():
        shutil.copy(persona_snapshot, agent_dir / "persona_context.txt")
        print("[UPDATE] persona_context.txt updated from snapshot.")
        
    print(f"[SUCCESS] Agent {agent_slug} has been updated to config from Run {run_id}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id", help="Run ID (e.g. 20260123_120000_legal_intake)")
    parser.add_argument("--agent", required=True, help="Agent Slug")
    parser.add_argument("--force", action="store_true", help="Bypass safety gates")
    args = parser.parse_args()
    
    promote_run(args.run_id, args.agent, args.force)
