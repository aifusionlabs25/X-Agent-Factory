"""
Gemini API Helper with Usage Logging
All Gemini calls should go through this helper to track usage.
"""
import os
import requests
import time
from usage_logger import log_gemini_call, estimate_tokens

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

def call_gemini(prompt: str, persona_context: str = "", max_retries: int = 3) -> str | None:
    """
    Make a Gemini API call with automatic usage logging.
    Returns the response text or None on failure.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found.")
        return None

    full_prompt = f"{persona_context}\n\n{prompt}" if persona_context else prompt
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}]
    }
    
    # Estimate input tokens
    input_tokens = estimate_tokens(full_prompt)
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{GEMINI_URL}?key={api_key}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 429:
                print(f"   ⚠️ Gemini Rate Limit (429). Waiting {2 * (attempt + 1)}s...")
                time.sleep(2 * (attempt + 1))
                continue
                
            response.raise_for_status()
            
            result = response.json()
            response_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Estimate output tokens and log
            output_tokens = estimate_tokens(response_text)
            
            # Try to get actual token counts from response if available
            usage_metadata = result.get('usageMetadata', {})
            if usage_metadata:
                input_tokens = usage_metadata.get('promptTokenCount', input_tokens)
                output_tokens = usage_metadata.get('candidatesTokenCount', output_tokens)
            
            log_gemini_call(
                model="gemini-2.0-flash-exp",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                success=True
            )
            
            return response_text
            
        except Exception as e:
            print(f"   ⚠️ Gemini Attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                # Log failed attempt
                log_gemini_call(
                    model="gemini-2.0-flash-exp",
                    input_tokens=input_tokens,
                    output_tokens=0,
                    success=False
                )
                print("❌ Gemini failed after max retries.")
                return None
    
    return None
