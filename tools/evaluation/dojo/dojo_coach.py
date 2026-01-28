"""
DOJO COACH v1.0
The Shadow Analyst.
Reads failed Dojo transcripts/scores and creates 'Shadow Change Orders' (JSON).
Does NOT edit agent files directly.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import requests

# Config
BASE_DIR = Path(__file__).parent
ORDERS_DIR = BASE_DIR / "shadow_orders"
OLLAMA_URL = "http://localhost:11434/api/generate"

def ensure_orders_dir(slug):
    path = ORDERS_DIR / slug
    path.mkdir(parents=True, exist_ok=True)
    return path

def analyze_failure(transcript, score, breakdown):
    """
    Use LLM to diagnose the failure based on transcript and score.
    """
    prompt = f"""You are an expert AGENT COACH specialized in legal intake and SDR bots.
    
    TRANSCRIPT:
    {transcript[:4000]}
    
    SCORE: {score}/100
    BREAKDOWN: {json.dumps(breakdown)}
    
    TASK:
    Analyze why the agent failed.
    Provide a concise diagnosis and a specific prompt fix.
    
    OUTPUT JSON ONLY:
    {{
        "diagnosis": "1 sentence on what went wrong.",
        "required_fix": "Specific instruction for the prompt architect.",
        "severity": "HIGH/MEDIUM/LOW"
    }}
    """
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": "llama3", "prompt": prompt, "stream": False, "options": {"temperature": 0.2}},
            timeout=60
        )
        if response.status_code == 200:
            raw = response.json().get("response", "")
            # Extract JSON
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0:
                return json.loads(raw[start:end])
    except Exception as e:
        print(f"[ERROR] LLM Diagnosis failed: {e}")
        
    return {
        "diagnosis": "Automated diagnosis failed.",
        "required_fix": "Manual review required.",
        "severity": "LOW"
    }

def run_coaching(log_path):
    log_path = Path(log_path)
    score_path = log_path.with_suffix('.score.json')
    
    if not log_path.exists() or not score_path.exists():
        print(f"[ERROR] Missing log or score file for {log_path.name}")
        return

    # Load Data
    with open(log_path, "r", encoding="utf-8") as f:
        transcript = f.read()
    
    with open(score_path, "r", encoding="utf-8") as f:
        score_data = json.load(f)
        
    score = score_data.get("score", 0)
    verdict = score_data.get("verdict", "FAIL")
    
    if verdict == "PASS":
        print(f"[SKIP] Agent passed ({score}/100). No coaching needed.")
        return

    print(f"--- COACHING: {log_path.name} ---")
    print(f"Score: {score} (FAIL)")
    
    # Analyze
    print("Consulting LLM for diagnosis...")
    diagnosis = analyze_failure(transcript, score, score_data.get("breakdown", {}))
    
    # Create Shadow Order
    # Extract client slug from parent dir name
    client_slug = log_path.parent.name
    
    order = {
        "id": f"CO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "agent": client_slug,
        "trigger_log": log_path.name,
        "score": score,
        "diagnosis": diagnosis["diagnosis"],
        "required_fix": diagnosis["required_fix"],
        "severity": diagnosis["severity"],
        "status": "PENDING_REVIEW"
    }
    
    # Save
    orders_dir = ensure_orders_dir(client_slug)
    order_path = orders_dir / f"{order['id']}.json"
    
    with open(order_path, "w", encoding="utf-8") as f:
        json.dump(order, f, indent=2)
        
    print(f"\n[SHADOW ORDER] Created: {order_path}")
    print(f"Diagnosis: {order['diagnosis']}")
    print(f"Fix: {order['required_fix']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", help="Path to transcript file")
    args = parser.parse_args()
    
    run_coaching(args.log_path)
