"""
Usage Logger Utility
Tracks API usage locally for Tavus and Gemini.
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path

USAGE_DIR = Path(__file__).parent.parent / "intelligence" / "usage"

def ensure_usage_dir():
    USAGE_DIR.mkdir(parents=True, exist_ok=True)

def log_gemini_call(model: str, input_tokens: int, output_tokens: int, success: bool = True):
    """Log a Gemini API call with token counts."""
    ensure_usage_dir()
    log_file = USAGE_DIR / "gemini_log.json"
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "success": success
    }
    
    # Read existing log
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
    
    logs.append(entry)
    
    # Write back
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
    
    return entry

def log_tavus_start(replica_id: str, client_slug: str, conversation_id: str = None):
    """Log when a Tavus conversation starts."""
    ensure_usage_dir()
    log_file = USAGE_DIR / "tavus_log.json"
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "replica_id": replica_id,
        "client_slug": client_slug,
        "conversation_id": conversation_id,
        "status": "started",
        "duration_seconds": None
    }
    
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
    
    logs.append(entry)
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
    
    return len(logs) - 1  # Return index for updating later

def log_tavus_end(conversation_id: str, duration_seconds: int):
    """Log when a Tavus conversation ends."""
    ensure_usage_dir()
    log_file = USAGE_DIR / "tavus_log.json"
    
    if not log_file.exists():
        return
    
    with open(log_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    # Find and update the matching conversation
    for entry in reversed(logs):
        if entry.get('conversation_id') == conversation_id and entry.get('status') == 'started':
            entry['status'] = 'ended'
            entry['duration_seconds'] = duration_seconds
            entry['ended_at'] = datetime.now().isoformat()
            break
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)

def get_gemini_usage_summary():
    """Get summary of Gemini usage from local logs."""
    log_file = USAGE_DIR / "gemini_log.json"
    
    if not log_file.exists():
        return {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "successful_calls": 0,
            "failed_calls": 0
        }
    
    with open(log_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    total_input = sum(e.get('input_tokens', 0) for e in logs)
    total_output = sum(e.get('output_tokens', 0) for e in logs)
    total_tokens = total_input + total_output
    successful = sum(1 for e in logs if e.get('success', True))
    
    # Gemini Flash pricing: ~$0.35 per 1M input tokens, ~$1.05 per 1M output tokens
    cost = (total_input * 0.35 / 1_000_000) + (total_output * 1.05 / 1_000_000)
    
    return {
        "total_calls": len(logs),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(cost, 4),
        "successful_calls": successful,
        "failed_calls": len(logs) - successful
    }

def get_tavus_usage_summary():
    """Get summary of Tavus usage from local logs."""
    log_file = USAGE_DIR / "tavus_log.json"
    
    if not log_file.exists():
        return {
            "total_calls": 0,
            "total_minutes": 0,
            "completed_calls": 0,
            "active_calls": 0
        }
    
    with open(log_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    completed = [e for e in logs if e.get('status') == 'ended']
    active = [e for e in logs if e.get('status') == 'started']
    
    # Sum durations, rounding each call up to minimum 1 minute
    total_seconds = sum(e.get('duration_seconds', 0) for e in completed)
    # Round up each call to nearest minute for billing
    total_minutes = sum(max(1, (e.get('duration_seconds', 60) + 59) // 60) for e in completed if e.get('duration_seconds'))
    
    return {
        "total_calls": len(logs),
        "total_minutes": total_minutes,
        "total_seconds": total_seconds,
        "completed_calls": len(completed),
        "active_calls": len(active)
    }

# Estimate tokens from text (rough approximation: ~4 chars per token)
def estimate_tokens(text: str) -> int:
    return len(text) // 4

if __name__ == "__main__":
    # Test logging
    print("Testing Gemini Logger...")
    log_gemini_call("gemini-2.0-flash-exp", 500, 200)
    print(get_gemini_usage_summary())
    
    print("\nTesting Tavus Logger...")
    log_tavus_start("replica_123", "desert_diamond_air", "conv_abc")
    print(get_tavus_usage_summary())
