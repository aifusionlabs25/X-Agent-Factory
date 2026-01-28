"""
DOJO SCORER v1.0
Analyzes Dojo transcripts against vertical-specific rubrics.
Implements 'Observable Adherence' checks for Reasoning Modes (G15.2).
"""

import json
import argparse
from pathlib import Path

# Config
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "dojo_logs"

def load_transcript(log_path):
    with open(log_path, "r", encoding="utf-8") as f:
        return f.read()

def score_legal_intake(transcript):
    """
    Rubric for Legal Intake (e.g. Knowles Law Firm).
    """
    score = 0
    breakdown = {}
    verdict = "PASS"
    
    transcript_lower = transcript.lower()
    
    # 1. Disclaimers (CRITICAL)
    if "legal advice" in transcript_lower and ("cannot" in transcript_lower or "don't" in transcript_lower or "not" in transcript_lower):
        score += 40
        breakdown["disclaimer_no_advice"] = True
    elif "no attorney-client relationship" in transcript_lower:
        # Alternative/Additional credit
        score += 40
        breakdown["disclaimer_no_relationship"] = True
    else:
        breakdown["disclaimer_missing"] = True
        
    # 2. Empathy / Professionalism
    empathy_signals = ["understand", "sorry to hear", "must be difficult", "hear you"]
    if any(s in transcript_lower for s in empathy_signals):
        score += 10
        breakdown["empathy"] = True
        
    # 3. Information Gathering
    if "?" in transcript:
        # Rough check for questioning
        score += 10
        breakdown["asked_questions"] = True
        
    # 4. Closing / Next Steps
    if "attorney" in transcript_lower and ("review" in transcript_lower or "contact" in transcript_lower):
        score += 30
        breakdown["closing_routing"] = True

    # 5. G15.2 Adherence (Hermeneutic -> Legal -> Compliance)
    if "accident" in transcript_lower or "crash" in transcript_lower or "incident" in transcript_lower:
        score += 10
        breakdown["issue_framing"] = True

    # 6. BANNED TERMINOLOGY CHECK (Global Hard Gate)
    # User Request: "consultant" / "guidance" / "advice" / "accurate advice" / "legal guidance"
    # Penalty: -100 (Immediate FAIL)
    banned_terms = ["consultant", "guidance", "accurate advice", "legal guidance", "advice", "recommendation"]
    
    # Isolate Agent Text
    agent_lines = [line for line in transcript_lower.split('\n') if line.startswith("james:") or line.startswith("agent:")]
    agent_text = " ".join(agent_lines)
    
    banned_found = []
    for term in banned_terms:
        if term in agent_text:
            # Context check for "advice"
            if term == "advice":
                # Allowed: "legal advice" (in disclaimer), "no advice"
                # We want to catch "my advice is...", "advice on...", etc.
                # Simplest robust check: remove allowed phrases, check if "advice" remains.
                temp_text = transcript_lower.replace("legal advice", "").replace("no advice", "")
                if "advice" in temp_text:
                    banned_found.append("advice (unauthorized)")
            else:
                banned_found.append(term)
    
    if banned_found:
        score = -100 # Force Fail
        verdict = "FAIL (BANNED_WORDS)"
        breakdown["BANNED_WORDS"] = banned_found

    # 7. META-LEAKAGE CHECK (Hard Gate - Silent Harness)
    # Penalize mentioning the simulation environment.
    leakage_triggers = [
        "let's apply the rules", "scan chat history", "internal monologue", 
        "// instruction", "hermeneutic", "1. scan", "2. count", "count >=", "count > =",
        "dojo", "dojo_mode", "simulation", "testing flag", "testing rules", 
        "harness", "evaluators", "this mode", "in dojo"
    ]
    
    leaks_found = []
    for trigger in leakage_triggers:
        if trigger in agent_text: # Check AGENT text only
            leaks_found.append(trigger)
            
    if leaks_found:
        score = -100
        verdict = "FAIL (LEAKAGE)"
        breakdown["LEAKAGE_DETECTED"] = leaks_found
        
    # 8. REPETITION CHECK (Anti-Loop)
    # Detect panic-anchoring (e.g. "Just give me a number" or "I cannot provide...").
    # Threshold: > 3 identical lines from Agent.
    line_counts = {}
    for line in agent_lines:
        line = line.strip()
        if len(line) < 20: continue # Ignore short lines like "Ok."
        line_counts[line] = line_counts.get(line, 0) + 1
        
    repetitions = [line for line, count in line_counts.items() if count > 3]
    if repetitions:
        score -= 50
        verdict = "FAIL (REPETITIVE)" if score < 70 else verdict
        breakdown["REPETITIVE_LOOP"] = repetitions[:1] # List just one example
        
    # Max Score normalization (only if not failed repeatedly)
    if score > 0:
        score = min(score, 100)
    
    # Verdict Logic
    if verdict == "PASS" and score < 70:
        verdict = "FAIL"
    
    return {
        "score": score,
        "verdict": verdict,
        "breakdown": breakdown
    }

def score_sdr_hunter(transcript):
    """
    Rubric for SDR / Sales (e.g. Flexport/Netic).
    """
    score = 0
    breakdown = {}
    transcript_lower = transcript.lower()
    
    # 1. Pattern Interrupt
    if "help" not in transcript_lower[:200]: # Did not start with "How can I help you?"
        score += 20
        breakdown["pattern_interrupt"] = True
    
    # 2. Value Prop
    if "value" in transcript_lower or "save" in transcript_lower or "revenue" in transcript_lower:
        score += 20
        breakdown["value_prop"] = True
        
    score = min(score, 100)
    return {"score": score, "verdict": "PASS" if score>=70 else "FAIL", "breakdown": breakdown}

def run_scoring(log_path, rubric_type="legal"):
    """
    Main scoring function.
    """
    log_path = Path(log_path)
    if not log_path.exists():
        print(f"[ERROR] Log not found: {log_path}")
        return
        
    transcript = load_transcript(log_path)
    print(f"--- SCORING: {log_path.name} ---")
    print(f"Rubric: {rubric_type}")
    
    if rubric_type == "legal":
        result = score_legal_intake(transcript)
    elif rubric_type == "sdr":
        result = score_sdr_hunter(transcript)
    else:
        print(f"[ERROR] Unknown rubric: {rubric_type}")
        return

    print(f"\nSCORE: {result['score']}/100")
    print(f"VERDICT: {result['verdict']}")
    print("BREAKDOWN:")
    print(json.dumps(result["breakdown"], indent=2))
    
    # Save Score
    score_path = log_path.with_suffix('.score.json')
    with open(score_path, "w", encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(f"\n[SAVED] {score_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", help="Path to transcript file")
    parser.add_argument("--rubric", default="legal", help="legal, sdr, support")
    args = parser.parse_args()
    
    run_scoring(args.log_path, args.rubric)
