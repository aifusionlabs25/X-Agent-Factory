"""
DOJO RUNNER v1.0
Agent-agnostic simulation harness.
Executes multi-turn conversations between an X-Agent and a specific Scenario Persona.
"""

import requests
import json
import time
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Import Adapter & Scorer
try:
    from dojo_agent_loader import load_agent_data
    from dojo_scorer import run_scoring
except ImportError:
    # Fallback for direct execution testing
    import sys
    sys.path.append(str(Path(__file__).parent))
    from dojo_agent_loader import load_agent_data
    from dojo_scorer import run_scoring

# Configuration
BASE_DIR = Path(__file__).parent
FACTORY_ROOT = BASE_DIR.parent.parent.parent
LOGS_DIR = BASE_DIR / "dojo_logs"
SCENARIOS_DIR = BASE_DIR / "scenarios"
OLLAMA_URL = "http://localhost:11434/api/generate"

def ensure_logs_dir(slug):
    path = LOGS_DIR / slug
    path.mkdir(parents=True, exist_ok=True)
    return path

def chat_with_ollama(system_prompt, user_message, history, agent_name, context_str="", stop_tokens=None):
    """
    Send message to Ollama with strict harness.
    """
    if stop_tokens is None:
        stop_tokens = ["PROSPECT:", "USER:", "SYSTEM:", "Assistant:", f"{agent_name}:"]

    # Construct History
    chat_history = ""
    for msg in history:
        role_label = "PROSPECT" if msg["role"] == "user" else agent_name.upper()
        chat_history += f"{role_label}: {msg['content']}\n"
        
    final_prompt = f"""{system_prompt}

[SIMULATION CONTEXT]
You are currently in a live interaction.
Current Conversation:
{chat_history}
PROSPECT: {user_message}

{agent_name.upper()}:"""

    payload = {
        "model": "llama3", # Default, can be overridden
        "prompt": final_prompt,
        "stream": False,
        "options": {
            "stop": stop_tokens,
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            return f"[ERROR] Ollama Status {response.status_code}"
    except Exception as e:
        return f"[ERROR] Connection failed: {e}"

def generate_opponent_response(scenario_persona, agent_last_msg, turn, total_turns):
    """
    Generates the User/Prospect response based on the scenario.
    """
    safety_preamble = "You are a roleplay actor in a business simulation."
    
    prompt = f"""{safety_preamble}

YOUR CHARACTER:
{scenario_persona}

CURRENT SITUATION:
You are in Turn {turn} of {total_turns}.
The Agent just said: "{agent_last_msg}"

TASK:
Respond naturally as your character.
- Keep it under 50 words.
- Be realistic (if skeptical, stay skeptical).
- Do not output actions (e.g. *hangs up*), only dialogue.

YOUR RESPONSE:"""

    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "").strip().replace('"', '')
        return "..."
    except:
        return "..."

def run_simulation():
    """
    Main simulation loop.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("client", help="Client slug (e.g. knowles_law_firm)")
    parser.add_argument("scenario", help="Path to scenario JSON")
    parser.add_argument("--turns", type=int, default=10, help="Max turns")
    parser.add_argument("--scratchpad_sys", help="Path to temporary system prompt file", default=None)
    parser.add_argument("--scratchpad_persona", help="Path to temporary persona context file", default=None)
    parser.add_argument("--run_id", help="Force a specific Run ID", default=None)
    args = parser.parse_args()
    
    # Resolve Paths
    agent_dir = FACTORY_ROOT / "agents" / "clients" / args.client
    if not agent_dir.exists():
        print(f"[ERROR] Agent not found: {args.client}")
        sys.exit(1)
        
    # Load Scenario
    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        # Try relative to scenarios dir
        scenario_path = FACTORY_ROOT / "tools" / "evaluation" / "dojo" / "scenarios" / args.scenario
        if not scenario_path.exists():
             print(f"[ERROR] Scenario not found: {args.scenario}")
             sys.exit(1)
             
    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario = json.load(f)
        
    # Load Agent (Normal or Scratchpad)
    # 1. System Prompt
    if args.scratchpad_sys:
        print(f"[INFO] Using Scratchpad System Prompt: {args.scratchpad_sys}")
        with open(args.scratchpad_sys, "r", encoding="utf-8") as f:
            sys_prompt_content = f.read()
    else:
        with open(agent_dir / "system_prompt.txt", "r", encoding="utf-8") as f:
            sys_prompt_content = f.read()

    # SYSTEM: Preflight Scope Check
    firm_scope_path = agent_dir / "firm_scope.json"
    if firm_scope_path.exists():
        with open(firm_scope_path, "r", encoding="utf-8") as f:
            firm_scope = json.load(f)
            
        scenario_meta = scenario.get("metadata")
        
        # Check 0: Metadata Existence (Strictness)
        if not scenario_meta or "topic_tags" not in scenario_meta:
             print(f"[ABORT] SCENARIO INVALID: Missing metadata/topic_tags.")
             log_dir = ensure_logs_dir(args.client)
             if args.run_id: run_id = args.run_id
             else: run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{scenario.get('id', 'sim')}"
             
             log_path = log_dir / f"{run_id}.txt"
             with open(log_path, "w", encoding="utf-8") as f:
                 f.write(f"SIMULATION: {scenario.get('id', 'sim')}\nVERDICT: SCENARIO_METADATA_INVALID\nREASON: Missing metadata block.\n")
             
             score_path = log_dir / f"{run_id}.score.json"
             with open(score_path, "w", encoding="utf-8") as f:
                 # Score null = Void
                 json.dump({"score": None, "verdict": "SCENARIO_METADATA_INVALID", "breakdown": {"error": "Missing metadata"}}, f)
             sys.exit(0)

        scenario_tags = scenario_meta.get("topic_tags", [])
        allowed_topics = firm_scope.get("allowed_topics", [])
        disallowed_topics = firm_scope.get("disallowed_topics", [])
        
        # Check 1: Disallowed
        for tag in scenario_tags:
            if tag in disallowed_topics:
                print(f"[ABORT] SCENARIO MISMATCH: Topic '{tag}' is disallowed.")
                log_dir = ensure_logs_dir(args.client)
                if args.run_id: run_id = args.run_id
                else: run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{scenario.get('id', 'sim')}"
                
                log_path = log_dir / f"{run_id}.txt"
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"SIMULATION: {scenario.get('id', 'sim')}\nVERDICT: SCENARIO_MISMATCH\nREASON: Topic '{tag}' disallowed.\n")
                
                score_path = log_dir / f"{run_id}.score.json"
                with open(score_path, "w", encoding="utf-8") as f:
                    json.dump({"score": None, "verdict": "SCENARIO_MISMATCH", "breakdown": {"mismatch": f"Topic '{tag}' disallowed"}}, f)
                sys.exit(0) # Exit clean so API sees artifacts

        # Check 2: Allowed Overlap
        if allowed_topics and scenario_tags:
             if not any(tag in allowed_topics for tag in scenario_tags):
                print(f"[ABORT] SCENARIO MISMATCH: No topic overlap.")
                log_dir = ensure_logs_dir(args.client)
                if args.run_id: run_id = args.run_id
                else: run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{scenario.get('id', 'sim')}"
                
                log_path = log_dir / f"{run_id}.txt"
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"SIMULATION: {scenario.get('id', 'sim')}\nVERDICT: SCENARIO_MISMATCH\nREASON: No topic overlap.\n")
                
                score_path = log_dir / f"{run_id}.score.json"
                with open(score_path, "w", encoding="utf-8") as f:
                    json.dump({"score": None, "verdict": "SCENARIO_MISMATCH", "breakdown": {"mismatch": "No topic overlap"}}, f)
                sys.exit(0)

    # 2. Persona Context (Optional - used for Dojo Mode rules often)
    persona_content = ""
    if args.scratchpad_persona:
         print(f"[INFO] Using Scratchpad Persona Context: {args.scratchpad_persona}")
         with open(args.scratchpad_persona, "r", encoding="utf-8") as f:
            persona_content = f.read()
    elif (agent_dir / "persona_context.txt").exists():
         with open(agent_dir / "persona_context.txt", "r", encoding="utf-8") as f:
            persona_content = f.read()
            
    # VALIDATION
    if "Persona Context" in sys_prompt_content and len(sys_prompt_content) > 500:
        print("[WARN] Your System Prompt appears to contain a full Persona Context.")
        print("       (This is valid for 'Hybrid' prompts, but verify your export expectations.)")
        
    if not persona_content or len(persona_content) < 50:
        print("[WARN] Persona Context is empty or stub. If this is intentional (Hybrid), ignore.")
        
    # Combine for Runner
    agent_data = {
        "system_prompt": sys_prompt_content,
        "name": "James" # Dynamic?
    }
    
    agent_name = agent_data.get("name", "Agent")
    
    # Prepare Log Directory Early (to save snapshots and stream)
    log_dir = ensure_logs_dir(args.client)
    
    if args.run_id:
        run_id = args.run_id
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"{timestamp}_{scenario.get('id', 'sim')}"
        
    log_name = f"{run_id}.txt"
    log_path = log_dir / log_name
    
    # PRE-EXECUTION VALIDATION
    if "id" not in scenario:
         print("[ABORT] SCENARIO INVALID: Missing 'id' field.")
         sys.exit(1)
         
    if "opponent_persona" not in scenario:
         print("[ABORT] SCENARIO INVALID: Missing 'opponent_persona' field.")
         sys.exit(1)

    # Initialize Log File (Stream Start)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"SIMULATION: {scenario['id']}\nAGENT: {args.client}\nDATE: {datetime.now()}\n\n")
        
    # Streaming Helper
    def log_append(text):
        print(text) # Stdout for debug
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    
    log_append(f"--- DOJO RUNNER v1 (Phase SX) ---")
    log_append(f"Agent: {args.client}")
    log_append(f"Scenario ID: {scenario['id']}")
    log_append(f"Scenario Path: {args.scenario}")
    
    # Metadata Logging
    meta = scenario.get("metadata", {})
    tags = meta.get("topic_tags", [])
    log_append(f"Topics: {tags}")
    
    op = scenario['opponent_persona']
    role_name = op if isinstance(op, str) else op.get('name', 'Unknown')
    log_append(f"Opponent Role: {role_name}")
    log_append("----------------------\n")
    
    history = []
    
    opener = scenario.get("opener")
    # Strict: If no opener, fail? Or allow silent start? 
    # User asked for strictness. Let's warn but not fail opener, as some scenarios might be agent-first?
    # But usually user speaks first in these calls.
    if not opener:
        log_append("[WARN] No 'opener' defined in scenario.")
        
    turns = args.turns
    turns = args.turns
    
    agent_msg = "" # Initialize for safety
    
    # State Tracking
    empathy_used = False
    exit_state = False
    exit_line_count = 0
    
    # SNAPSHOT INTERCEPT
    snapshot_sys = log_dir / f"{run_id}.system_prompt.txt"
    snapshot_persona = log_dir / f"{run_id}.persona_context.txt"
    
    with open(snapshot_sys, "w", encoding="utf-8") as f:
        f.write(sys_prompt_content)
    
    if persona_content:
        with open(snapshot_persona, "w", encoding="utf-8") as f:
            f.write(persona_content)
            
    log_append("\n=== STARTING SIMULATION ===\n")
    
    for i in range(1, turns + 1):
        log_append(f"\n[TURN {i}/{turns}]")
        
        # Opponent Turn
        if i == 1 and opener:
             user_msg = opener
        else:
             user_msg = generate_opponent_response(scenario.get("opponent_persona", ""), agent_msg, i, turns)
             
        log_append(f"PROSPECT: {user_msg}")
        history.append({"role": "user", "content": user_msg})
        
        time.sleep(0.5)
        
        # Agent Turn
        # 1. Base Injection (The "Tiny Snippet")
        # SILENT HARNESS: Explicitly forbid mentioning the mode.
        dojo_flag = (
            "SYSTEM OVERRIDE: DOJO_MODE=true. "
            "You are in a high-fidelity simulation. "
            "Adhere strictly to DOJO_MODE rules in your context, BUT "
            "UNDER NO CIRCUMSTANCES should you mention 'Dojo', 'Simulation', 'Testing', or 'Mode' to the user. "
            "Act exactly as if this is a real call. "
            "If you fail this silence check, you fail the simulation."
        )
        
        # Prepend to system prompt
        current_system_prompt = f"{dojo_flag}\n\n{agent_data['system_prompt']}"
        
        # 2. Empathy Lock Prompt
        if empathy_used:
             current_system_prompt += "\n\n[DOJO INSTRUCTION] You have already empathized. Move to routing."
             
        agent_msg = chat_with_ollama(current_system_prompt, user_msg, history, agent_name)
        
        # --- CODE GUARDRAILS (HARD GATES) ---
        
        # 1. EMPATHY GUARDRAIL
        if empathy_used:
             prefixes = ["I hear you.", "I understand.", "I apologize.", "I am sorry.", "I hear you,", "I understand,", "I apologize,"]
             original_msg = agent_msg
             for p in prefixes:
                 if p in agent_msg:
                     agent_msg = agent_msg.replace(p, "").strip()
             if not agent_msg:
                 agent_msg = "I can't put a dollar value on that."
        
        # 2. EXIT GUARDRAIL
        if exit_state:
             allowed_exits = [
                 "Understood. Without a consult, I can’t take this further. If you change your mind, call us back.",
                 "Understood. We'll end here. If you change your mind, call us back."
             ]
             if agent_msg.strip() not in allowed_exits:
                 agent_msg = allowed_exits[0]
                 log_append("[GUARDRAIL]: Overwrote output to enforce Exit State.")
        
        log_append(f"{agent_name.upper()}: {agent_msg}")
        history.append({"role": "assistant", "content": agent_msg})
        
        # State Update Checks
        agent_msg_lower = agent_msg.lower()
        
        if not empathy_used:
            if any(x in agent_msg_lower for x in ["hear you", "understand", "sorry", "apologize"]):
                empathy_used = True
             
        if "without a consult" in agent_msg_lower or "end here" in agent_msg_lower:
             exit_state = True
             exit_line_count += 1
             
        if exit_line_count >= 2:
             log_append("\n[LOOP BREAK] Exit line repeated 2 times. Ending simulation.")
             log_append("[SYSTEM]: Loop broken due to repeated exit lines.")
             break
        
        time.sleep(0.5)

    log_append("\n=== SIMULATION COMPLETE ===")
    
    # Run Scorer
    rubric = scenario.get("rubric", "legal") 
    log_append(f"\n[AUTO-SCORING] Rubric: {rubric}")
    try:
        run_scoring(log_dir / log_name, rubric)
    except Exception as e:
        log_append(f"[SCORING ERROR] {e}")
        
    return log_dir / log_name

if __name__ == "__main__":
    run_simulation()
