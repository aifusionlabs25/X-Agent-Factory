"""
TROY ARCHITECT v1.0 (Heuristic MVP)
Generates Change Order (CO) JSON based on Dojo Score Breakdown.
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Config
BASE_DIR = Path(__file__).parent
INPUTS_DIR = BASE_DIR / "inputs"
OUTPUTS_DIR = BASE_DIR / "outputs"

def generate_change_order(run_id, cycle=1):
    """
    Analyzes score and generates fixes.
    """
    # 1. Load Inputs
    run_dir = INPUTS_DIR / run_id
    score_path = run_dir / "score.json"
    sys_prompt_path = run_dir / "system_prompt.txt"
    
    if not score_path.exists():
        print(f"[ERROR] Score not found: {score_path}")
        return False
        
    with open(score_path, "r", encoding="utf-8") as f:
        score_data = json.load(f)
        
    breakdown = score_data.get("breakdown", {})
    changes = []
    
    # 2. Heuristic Logic (The "Brain")
    
    # FIX: Missing Disclaimer
    if breakdown.get("disclaimer_missing"):
        changes.append({
            "change_id": "FIX_DISCLAIMER",
            "target_file": "system_prompt.txt",
            "operation": "insert_after",
            "locator": {
                "type": "anchor_text",
                "text": "## 1. Who You Are"
            },
            "insertion": "CRITICAL INSTRUCTION: You MUST state 'I am not an attorney and cannot give legal advice' in your first turn.",
            "rationale": "Score failure: Disclaimer missing.",
            "expected_effect": { "score_delta_estimate": 30, "reduces_flags": ["disclaimer_missing"] },
            "risk": "Low"
        })
        
    # FIX: Leakage
    if breakdown.get("LEAKAGE_DETECTED"):
        changes.append({
            "change_id": "FIX_LEAKAGE",
            "target_file": "system_prompt.txt",
            "operation": "insert_before",
            "locator": {
                "type": "anchor_text",
                "text": "## 2. AUDIO-FIRST BEHAVIORAL PROTOCOLS"
            },
            "insertion": "SILENCE ENFORCEMENT: Never mention 'Dojo', 'Simulation', or 'Rules'. You are a real person on a real call.",
            "rationale": "Critical failure: Meta-leakage detected.",
            "expected_effect": { "score_delta_estimate": 50, "reduces_flags": ["LEAKAGE_DETECTED"] },
            "risk": "Low"
        })

    # FIX: Empathy Missing (Add if not present)
    if not breakdown.get("empathy") and not breakdown.get("LEAKAGE_DETECTED") and len(changes) == 0:
         # Only fix empathy if no critical failures
         changes.append({
            "change_id": "FIX_EMPATHY",
            "target_file": "system_prompt.txt",
            "operation": "insert_after",
            "locator": {
                "type": "anchor_text",
                "text": "Phase B — Story:"
            },
            "insertion": "EMPATHY RULE: After they describe the accident, say 'I am so sorry to hear that, it sounds stressful.'",
            "rationale": "Score improvement: Empathy signal missing.",
            "expected_effect": { "score_delta_estimate": 10, "reduces_flags": [] },
            "risk": "Low"
         })

    # FIX: Closing/Routing Missing (Common Level 3 Fail) - CLEAN VERSION
    if not breakdown.get("closing_routing") and len(changes) == 0:
         changes.append({
            "change_id": "FIX_CLOSING",
            "target_file": "system_prompt.txt",
            "operation": "insert_after",
            "locator": {
                "type": "anchor_text",
                "text": "Phase C — Vitals:"
            },
            "insertion": "Closing Rule: Once the caller is stable and you’ve collected basics, ask: 'Do you want me to schedule that consultation?' Do not repeat more than twice in the entire call.",
            "rationale": "Score improvement: Closing/Routing signal missing (Safe Protocol).",
            "expected_effect": { "score_delta_estimate": 30, "reduces_flags": ["closing_routing_missing"] },
            "risk": "Low"
         })

    # FIX: DOJO_MODE Pollution (Cleanup)
    # Check if snapshot contains "DOJO_MODE"
    with open(sys_prompt_path, "r", encoding="utf-8") as f:
        sys_content = f.read()
        
    if "DOJO_MODE" in sys_content and len(changes) == 0:
         changes.append({
            "change_id": "FIX_DOJO_REMOVE",
            "target_file": "system_prompt.txt",
            "operation": "delete",
            "locator": {
                "type": "regex",
                "pattern": "(?s)## 6\\. DOJO_MODE Toggle.*?In LIVE mode, do not speak.*?out loud\\."
            },
            "rationale": "Cleanup: Removed forbidden DOJO_MODE artifact.",
            "expected_effect": { "score_delta_estimate": 0, "reduces_flags": ["LEAKAGE_DETECTED"] },
            "risk": "Low"
         })

    if not changes:
        print("[TROY] No obvious heuristic fixes found.")
        return False
        
    # 3. Construct CO JSON
    co_data = {
      "schema_version": "co.v1",
      "run_id": run_id,
      "cycle": int(cycle),
      "agent_id": "unknown", # Could read from manifest
      "role_id": "unknown",
      "pack_id": "unknown",
      "level": "L1",
      "variant": "scratchpad",
      "created_at": datetime.now().isoformat(),
      "inputs": {
        "transcript_path": "transcript.txt",
        "score_path": "score.json",
        "system_prompt_snapshot_path": "system_prompt.txt",
        "persona_context_snapshot_path": "persona_context.md",
        "manifest_path": "manifest.json"
      },
      "constraints": {
        "hard_gates": ["no_advice"], # Default constraint to satisfy schema
        "banned_terms": [],
        "do_not_touch_blocks": []
      },
      "objective": {
        "target_verdict": "PASS",
        "target_score_min": 90,
        "must_pass_gates": list(breakdown.keys()), # Try to fix all flags?
        "notes": f"Troy Auto-Fix Cycle {cycle}"
      },
      "changes": changes,
      "tests": {
        "rerun_pack": True,
        "rerun_level": "L1",
        "max_turns": 10,
        "pass_if": ["fix_verified"]
      },
      "rollback": {
        "strategy": "discard_scratchpad",
        "notes": "Revert"
      }
    }
    
    # 4. Save
    output_path = OUTPUTS_DIR / f"CO_{run_id}_{cycle}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(co_data, f, indent=2)
        
    print(f"[TROY] Generated Change Order: {output_path}")
    return str(output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id", help="Run ID to analyze")
    parser.add_argument("--cycle", default=1, help="Cycle number")
    args = parser.parse_args()
    
    generate_change_order(args.run_id, args.cycle)
