import json
import os
from datetime import datetime

def load_env(filepath='.env.local'):
    """Simple .env loader."""
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                key = key.replace('\0', '')
                value = value.strip('"').strip("'").replace('\0', '')
                if key and value:
                    os.environ[key] = value

def load_json(filepath):
    """Loads a JSON file safely."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """Saves data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_timestamp():
    """Returns ISO 8601 timestamp."""
    return datetime.now().isoformat()

def ensure_directory(path):
    """Ensures a directory exists."""
    os.makedirs(path, exist_ok=True)
