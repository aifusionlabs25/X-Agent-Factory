"""
Gemini Helper -> OLLAMA Helper (Local Compute Version)
Redirects all 'Cloud' requests to the fast, local RTX 5080.
"""
import os
import time
import json
import datetime
import requests
from pathlib import Path
from usage_logger import log_gemini_call, estimate_tokens

# --- CONFIGURATION ---
# We keep the variable names compatible, but they point to LOCALHOST.
MODEL_NAME = "llama3"
API_URL = "http://localhost:11434/api/generate"
FORENSIC_LOG_DIR = Path("intelligence/forensic_logs")

# Ensure log dir exists
FORENSIC_LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_forensic(context: str, prompt: str, response_object: dict, start_time: float):
    """
    Saves the full prompt and response to a JSON file for debugging.
    """
    duration = time.time() - start_time
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = FORENSIC_LOG_DIR / f"log_{timestamp}_{context}.json"
    
    log_entry = {
        "timestamp": timestamp,
        "context": context,
        "model": MODEL_NAME,
        "duration_seconds": round(duration, 2),
        "input": {
            "prompt": prompt
        },
        "output": response_object
    }
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Forensic Log Failed: {e}")

def call_gemini(prompt: str, persona_context: str = "", context_label: str = "generic", max_retries: int = 3) -> str | None:
    """
    Acts as a drop-in replacement for the Google API, but uses OLLAMA.
    """
    full_prompt = f"{persona_context}\n\n{prompt}" if persona_context else prompt
    
    # Ollama API Payload
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_ctx": 4096 
        }
    }
    
    # Estimate input tokens (rough)
    input_tokens = estimate_tokens(full_prompt)
    start_time = time.time()

    for attempt in range(max_retries):
        try:
            # Call Localhost
            response = requests.post(API_URL, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Forensic Log
            log_forensic(context_label, full_prompt, result, start_time)
            
            # Parse Text (Ollama format is simple)
            response_text = result.get('response', '')
            
            # Estimate output tokens
            output_tokens = estimate_tokens(response_text)
            
            # Usage Log (Fake 'success' for compatibility)
            log_gemini_call(
                model=MODEL_NAME,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                success=True
            )
            
            return response_text
            
        except Exception as e:
            print(f"   ⚠️ Ollama Attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1) # Local is fast, no need for long backoff
            else:
                log_gemini_call(MODEL_NAME, input_tokens, 0, False)
                return None
    
    return None
