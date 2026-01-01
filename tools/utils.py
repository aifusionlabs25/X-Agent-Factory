import json
import os
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
