"""
DOJO GAUNTLET v2.0 (The Auto-Tuner)
Orchestrates the Self-Healing Loop on a TEMPORARY agent variant.
Relentlessly improves the agent until it passes the rubric or hitting max loops.
"""

import os
import sys
import shutil
import argparse
import subprocess
import json
import time
from pathlib import Path

# Config
BASE_DIR = Path(__file__).parent
FACTORY_ROOT = BASE_DIR.parent.parent.parent
AGENTS_DIR = FACTORY_ROOT / "agents" / "clients"
LOGS_DIR = BASE_DIR / "dojo_logs"

def run_step(command, description):
    print(f"\n[STEP] {description}...")
    try:
        # Use sys.executable to ensure we use the same python interpreter
        result = subprocess.run(
            [sys.executable] + command,
            capture_output=True,
            text=True,
            check=True,
            cwd=FACTORY_ROOT
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Step failed: {e}")
        print(f"Stderr: {e.stderr}")
        return None

def apply_patch(agent_slug, patch_path):
    """
    Apply a patch file to the agent's system_prompt.txt.
    We do this rigorously by reading the patch and applying the change.
    Since `patch` command might not be available on Windows, we'll do a simple Python replace if exact match found,
    OR (since our Architect output is structured) we might just ask the Architect to output the full file in the next version.
    
    For now, for the prototype, we will trust the Architect's 'patch' file is actually a diff we can parse or
    we will modify the Architect to output the FULL NEW PROMPT for the Gauntlet to consume easily.
    
    Actually, let's look at dojo_architect.py - it creates a diff file.
    Parsing a standard unified diff in python is tricky without `patch`.
    
    STRATEGY: We will cheat slightly for the Gauntlet.
    We will modify dojo_architect.py to optionally output a `system_prompt.new` file alongside the patch.
    """
    # For this iteration, we will assume we can't easily validly apply the patch without 'patch'.
    # So we will implement a 'Apply' helper in python here using the Unified Diff logic if possible, 
    # OR we rely on a helper script.
    
    # Simpler: Let's read the patch, find the "+" lines that aren't "+++", and append them?
    # No, that's brittle.
    
    # Better: Let's Invoke the Architect to "Apply" its own fix if requested?
    # Let's write a simple 'patch_applier.py' or just handle it here.
    
    pass # To be implemented in loop

def run_gauntlet(client_slug, scenario_path, max_loops=3):
    print(f"--- THE GAUNTLET: {client_slug} ---")
    print(f"Scenario: {Path(scenario_path).name}")
    
    # 1. Create Sandbox Agent
    sandbox_slug = f"{client_slug}_gauntlet"
    sandbox_dir = AGENTS_DIR / sandbox_slug
    source_dir = AGENTS_DIR / client_slug
    
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    shutil.copytree(source_dir, sandbox_dir)
    print(f"[SETUP] Created sandbox: {sandbox_slug}")
    
    current_score = 0
    loop_count = 0
    
    while current_score < 90 and loop_count < max_loops:
        loop_count += 1
        print(f"\n=== LOOP {loop_count}/{max_loops} ===")
        
        # A. Run Simulation
        output = run_step(
            ["tools/evaluation/dojo/dojo_runner.py", sandbox_slug, scenario_path, "--turns", "3"],
            f"Running Simulation ({sandbox_slug})"
        )
        if not output: break
        
        # Parse Log Path from Output
        # Helper: find the last generated log for this agent
        sandbox_logs = LOGS_DIR / sandbox_slug
        # Get newest file
        try:
             latest_log = max(sandbox_logs.glob("*.txt"), key=os.path.getctime)
        except ValueError:
            print("[FAIL] No log generated.")
            break
            
        print(f"[LOG] {latest_log.name}")
        
        # B. Score
        score_out = run_step(
            ["tools/evaluation/dojo/dojo_scorer.py", str(latest_log), "--rubric", "legal"],
            "Scoring"
        )
        
        # Extract Score
        score_file = latest_log.with_suffix('.score.json')
        with open(score_file, 'r') as f:
            score_data = json.load(f)
        current_score = score_data['score']
        print(f"[SCORE] {current_score}/100")
        
        if current_score >= 90:
            print(f"\n[VICTORY] Agent passed the Gauntlet!")
            break
            
        # C. Coach (Diagnose)
        coach_out = run_step(
            ["tools/evaluation/dojo/dojo_coach.py", str(latest_log)],
            "Coaching"
        )
        # Find the Change Order (newest in shadow_orders/sandbox_slug)
        orders_dir = BASE_DIR / "shadow_orders" / sandbox_slug
        try:
            latest_order = max(orders_dir.glob("*.json"), key=os.path.getctime)
        except ValueError:
            print("[FAIL] Coach produced no order.")
            break
            
        # D. Architect (Generate Fix)
        # We need the Architect to actually give us the TEXT to write, not just a patch file.
        # But `dojo_architect.py` saves a .patch.
        # Check if the Architect printed the fix content or if we can extract it.
        # For this prototype, I will MODIFY dojo_architect to save `system_prompt.new` for the Gauntlet.
        
        # Temp Hack: We'll modify the system prompt manually in the loop for demonstration?
        # No, we need it automated.
        
        print("[ARCHITECT] Generating fix...")
        # Run architect - it generates a patch
        run_step(["tools/evaluation/dojo/dojo_architect.py", str(latest_order)], "Drafting Patch")
        
        # Find patch
        patches_dir = orders_dir / "patches"
        try:
            latest_patch = max(patches_dir.glob("*.patch"), key=os.path.getctime)
        except ValueError:
             print("[FAIL] Architect produced no patch.")
             break
             
        # E. APPLY (The Dangerous Part - Safe in Sandbox)
        # We need to extract the "+" lines from the patch and append them (Simplified Logic for Prototype)
        # OR we assume the Architect put the FULL NEW PROMPT in a side file.
        
        # Let's Read the patch and try to append the new block.
        with open(latest_patch, 'r') as f:
            patch_content = f.read()
            
        # Extract lines starting with "+ " (ignoring +++ and @@)
        new_lines = []
        for line in patch_content.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                new_lines.append(line[1:])
        
        new_block = "\n".join(new_lines).strip()
        
        # Append to system prompt
        promp_path = sandbox_dir / "system_prompt.txt"
        with open(promp_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n{new_block}")
            
        print("[APPLIED] Patch appended to sandbox system prompt.")
        
    # Cleanup
    print(f"\n=== GAUNTLET COMPLETE ===")
    print(f"Final Score: {current_score}")
    print(f"Sandbox preserved at: agents/clients/{sandbox_slug}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("client", help="Client slug")
    parser.add_argument("scenario", help="Path to scenario")
    args = parser.parse_args()
    
    run_gauntlet(args.client, args.scenario)
