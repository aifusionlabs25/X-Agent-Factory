"""
DOJO A/B TESTER
Compares two agent variants against the same scenario.
Variant A: Baseline (No Reasoning)
Variant B: Reasoning (G15.2 Profile Injected)
"""

import sys
import shutil
import json
import argparse
from pathlib import Path
import subprocess

# Config
BASE_DIR = Path(__file__).parent
FACTORY_ROOT = BASE_DIR.parent.parent.parent
AGENTS_DIR = FACTORY_ROOT / "agents" / "clients"

def run_step(command):
    try:
        subprocess.run([sys.executable] + command, check=True, cwd=FACTORY_ROOT, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {e}")
        return False

def get_latest_score(slug):
    log_dir = BASE_DIR / "dojo_logs" / slug
    try:
        # Find latest score json
        latest = max(log_dir.glob("*.score.json"), key=os.path.getctime)
        with open(latest, 'r') as f:
            return json.load(f)["score"]
    except:
        return 0

def inject_reasoning(slug):
    """Injects reasoning profile into system prompt."""
    agent_dir = AGENTS_DIR / slug
    profile_path = agent_dir / "reasoning_profile.txt"
    prompt_path = agent_dir / "system_prompt.txt"
    
    if profile_path.exists() and prompt_path.exists():
        with open(profile_path, 'r') as f:
            profile = f.read()
            
        with open(prompt_path, 'r') as f:
            prompt = f.read()
            
        # Check if already injected
        if "[Reasoning: legal_intake_v1]" not in prompt:
            with open(prompt_path, 'w') as f:
                f.write(f"{profile}\n\n{prompt}")
            return True
    return False

def run_ab_test(client_slug, scenario_path):
    print(f"--- DOJO A/B TEST: {client_slug} ---")
    print(f"Scenario: {Path(scenario_path).name}")
    
    # 1. Setup Variants
    variant_a = f"{client_slug}_var_A" # Baseline
    variant_b = f"{client_slug}_var_B" # Reasoning
    
    for v in [variant_a, variant_b]:
        p = AGENTS_DIR / v
        if p.exists(): shutil.rmtree(p)
        shutil.copytree(AGENTS_DIR / client_slug, p)
        
    # 2. Configure Variant B (Inject Reasoning)
    print("[SETUP] Injecting Reasoning into Variant B...")
    inject_reasoning(variant_b)
    
    # 3. Run Tests
    print("\n>>> RUNNING VARIANT A (Baseline)...")
    run_step(["tools/evaluation/dojo/dojo_runner.py", variant_a, scenario_path, "--turns", "3"])
    run_step(["tools/evaluation/dojo/dojo_scorer.py", str(BASE_DIR/"dojo_logs"/variant_a/"latest.txt"), "--rubric", "legal"]) # Runner needs to output latest link? or we find it.
    
    # Find log manually since runner is unaware
    log_a_dir = BASE_DIR / "dojo_logs" / variant_a
    latest_log_a = max(log_a_dir.glob("*.txt"), key=os.path.getctime)
    run_step(["tools/evaluation/dojo/dojo_scorer.py", str(latest_log_a), "--rubric", "legal"])
    score_a = get_latest_score(variant_a)
    
    print("\n>>> RUNNING VARIANT B (Reasoning)...")
    run_step(["tools/evaluation/dojo/dojo_runner.py", variant_b, scenario_path, "--turns", "3"])
    
    log_b_dir = BASE_DIR / "dojo_logs" / variant_b
    latest_log_b = max(log_b_dir.glob("*.txt"), key=os.path.getctime)
    run_step(["tools/evaluation/dojo/dojo_scorer.py", str(latest_log_b), "--rubric", "legal"])
    score_b = get_latest_score(variant_b)
    
    # 4. Results
    print("\n=== A/B TEST RESULTS ===")
    print(f"Variant A (Baseline):  {score_a}/100")
    print(f"Variant B (Reasoning): {score_b}/100")
    
    diff = score_b - score_a
    if diff > 0:
        print(f"Winner: VARIANT B (+{diff} points)")
    elif diff < 0:
        print(f"Winner: VARIANT A (+{abs(diff)} points)")
    else:
        print("Result: DRAW")

if __name__ == "__main__":
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("client", help="Client slug")
    parser.add_argument("scenario", help="Path to scenario")
    args = parser.parse_args()
    
    run_ab_test(args.client, args.scenario)
