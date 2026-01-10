import json
import os
import re
from datetime import datetime

def load_env():
    """Load environment variables using python-dotenv."""
    from dotenv import load_dotenv
    # Try loading .env first, then .env.local
    load_dotenv('.env')
    load_dotenv('.env.local')  # Does not override existing

def load_json(filepath):
    """Loads a JSON file safely."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """Saves data to a JSON file and indexes it in the Knowledge Vault."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    # Hook: Auto-Index to Librarian's Knowledge Vault
    try:
        import subprocess
        # Assumes COMMAND folder is at ../COMMAND relative to this utils.py (which is in tools/)
        # X Agent Factory/tools/utils.py -> X Agent Factory/COMMAND/vault_index.py
        command_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "COMMAND", "vault_index.py")
        if os.path.exists(command_script):
            # Run in background/detached? Or wait? 
            # User said "automatically send". 
            # We'll run it synchronously for reliability or assume the user wants it done then.
            # Using current python interpreter
            subprocess.run(["python", command_script, "--file", filepath], check=False)
            print(f"[LIBRARIAN] Indexed {os.path.basename(filepath)} to Vault.")
    except Exception as e:
        print(f"[LIBRARIAN] Indexing failed: {e}")

def get_timestamp():
    """Returns ISO 8601 timestamp."""
    return datetime.now().isoformat()

def ensure_directory(path):
    """Ensures a directory exists."""
    os.makedirs(path, exist_ok=True)

def extract_json_from_text(text):
    """
    Robustly extracts JSON object or array from a string polluted with conversational text.
    Handles ```json blocks and raw { } structures.
    """
    if not text:
        return None
        
    # 1. Try to find a code block first (Most reliable)
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(code_block_pattern, text, re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass # Fallthrough if block contents aren't valid JSON

    # 2. Try to find the first outer-most JSON object {...}
    # This regex balances braces to some extent, but a simple greedy match often works for LLM output
    # if we assume the JSON is the largest block.
    
    # Simple brace finding: Find first { and last }
    start_brace = text.find('{')
    end_brace = text.rfind('}')
    
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        json_str = text[start_brace : end_brace + 1]
        try:
            return json.loads(json_str)
        except:
            pass
            
    # 3. Try to find the first array [...]
    start_bracket = text.find('[')
    end_bracket = text.rfind(']')
    
    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        json_str = text[start_bracket : end_bracket + 1]
        try:
            return json.loads(json_str)
        except:
            pass

    return None
