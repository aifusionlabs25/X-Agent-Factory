"""
Prompt Safety Screen
Detects prompt injection attacks with encoding normalization.

Usage:
    from prompt_safety_screen import screen_input, block_check
    
    result = block_check(user_text)
    if result["blocked"]:
        print(f"Blocked: {result['reason']}")
"""
import re
import base64
import codecs
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


# ============================================================
# INPUT NORMALIZATION
# ============================================================

def normalize_unicode_escapes(text: str) -> str:
    """
    Decode \\uXXXX sequences in text.
    Example: "\\u0049\\u0067\\u006e" -> "Ign"
    """
    try:
        # Handle \\uXXXX (escaped backslash-u)
        if '\\u' in text:
            # Use unicode_escape codec
            decoded = codecs.decode(text.replace('\\u', '\\u'), 'unicode_escape')
            return decoded
    except Exception:
        pass
    return text


def try_base64_decode(text: str) -> Optional[str]:
    """
    Attempt to decode base64 content from text.
    Returns decoded string if valid base64 found, else None.
    """
    # Look for base64-ish strings (at least 20 chars, valid base64 alphabet)
    base64_pattern = r'[A-Za-z0-9+/=]{20,}'
    
    for match in re.finditer(base64_pattern, text):
        candidate = match.group()
        # Pad if needed
        padding = 4 - (len(candidate) % 4)
        if padding != 4:
            candidate += '=' * padding
        
        try:
            decoded = base64.b64decode(candidate).decode('utf-8', errors='ignore')
            # Only return if it looks like readable text
            if re.search(r'[a-zA-Z]{3,}', decoded):
                return decoded
        except Exception:
            continue
    
    return None


def normalize_input(text: str) -> List[str]:
    """
    Normalize input for scanning, returning list of text variants to check.
    Always includes original, plus decoded versions if applicable.
    """
    variants = [text]
    
    # Try unicode escape decoding
    decoded_unicode = normalize_unicode_escapes(text)
    if decoded_unicode != text:
        variants.append(decoded_unicode)
    
    # Try base64 decoding
    decoded_base64 = try_base64_decode(text)
    if decoded_base64:
        variants.append(decoded_base64)
    
    return variants


# ============================================================
# DETECTION RULES
# ============================================================

# Each rule: (pattern, reason_code, description)
DETECTION_RULES = [
    # Instruction Override (sec_001, sec_002)
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?)", 
     "instruction_override", "Ignore instructions attack"),
    (r"disregard\s+(your|the|all)?\s*(system\s+)?prompt", 
     "instruction_override", "Disregard system prompt"),
    (r"disregard\s+.{0,30}(system|rules?|instructions?)", 
     "instruction_override", "Disregard attack variant"),
    
    # Role Hijacking (sec_003, sec_004)
    (r"\bdan\b.*no\s+restrictions?", 
     "role_hijack", "DAN jailbreak"),
    (r"you\s+are\s+dan\b", 
     "role_hijack", "DAN identity assignment"),
    (r"pretend\s+you\s+are\s+a?\s*different\s+ai", 
     "role_hijack", "Role reassignment"),
    (r"different\s+ai\s+without\s+(any\s+)?safety", 
     "role_hijack", "Safety bypass role"),
    (r"ai\s+without\s+(any\s+)?safety\s+guidelines?", 
     "role_hijack", "No safety guidelines"),
    
    # Exfiltration (sec_005, sec_006)
    (r"(print|show|give|tell|reveal|display)\s+.{0,20}(system\s+prompt|entire\s+prompt)", 
     "exfiltration", "System prompt exfiltration"),
    (r"(api[_\s]?key|password|secret|token|credential|private\s+key)", 
     "credential_request", "Credential request"),
    (r"environment\s+variable", 
     "credential_request", "Environment variable request"),
    
    # Tool Misuse (sec_007, sec_008)
    (r"(delete_all|drop\s+table|truncate|destroy)", 
     "dangerous_tool", "Dangerous operation"),
    (r"(rm\s+-rf|format\s+c:|del\s+/f|shutdown)", 
     "command_injection", "Command injection"),
    (r"execute\s*:\s*(rm|del|format|shutdown|kill)", 
     "command_injection", "Execute command"),
    
    # Fake System Messages (sec_011)
    (r"\[SYSTEM\]", 
     "fake_system_message", "Fake system tag"),
    (r"(new\s+)?priority\s+instructions?\s+from\s+admin", 
     "fake_system_message", "Fake admin instructions"),
    (r"admin\s*:\s*(disable|ignore|override)", 
     "fake_system_message", "Fake admin command"),
    
    # External References (sec_012)
    (r"(url|link)\s+contains?\s+(important\s+)?instructions?", 
     "external_reference", "External instruction reference"),
    (r"instructions?\s*:\s*https?://", 
     "external_reference", "URL-based instructions"),
    (r"follow\s+.{0,20}(instructions?\s+)?(at|from)\s+https?://", 
     "external_reference", "Follow external URL"),
]

# Patterns that indicate encoded payloads (sec_009, sec_010)
ENCODED_PATTERNS = [
    (r"\\u[0-9a-fA-F]{4}", "encoded_payload", "Unicode escape detected"),
    (r"\(base64\)", "encoded_payload", "Base64 marker"),
    (r"base64\s*:", "encoded_payload", "Base64 prefix"),
]


def check_patterns(text: str, patterns: List[Tuple], case_insensitive: bool = True) -> List[Dict[str, Any]]:
    """Check text against a list of patterns."""
    matches = []
    flags = re.IGNORECASE if case_insensitive else 0
    
    for pattern, reason, description in patterns:
        if re.search(pattern, text, flags):
            matches.append({
                "pattern": pattern,
                "reason": reason,
                "description": description,
            })
    
    return matches


# ============================================================
# MAIN API
# ============================================================

def block_check(text: str) -> Dict[str, Any]:
    """
    Check if input should be blocked.
    
    Returns:
        {"blocked": bool, "reason": str, "details": list}
    """
    all_matches = []
    
    # Get all text variants to scan
    variants = normalize_input(text)
    
    # Check for encoded patterns in original
    encoded_matches = check_patterns(text, ENCODED_PATTERNS)
    all_matches.extend(encoded_matches)
    
    # Check all variants against detection rules
    for variant in variants:
        matches = check_patterns(variant, DETECTION_RULES)
        all_matches.extend(matches)
    
    # Deduplicate by reason
    seen_reasons = set()
    unique_matches = []
    for m in all_matches:
        if m["reason"] not in seen_reasons:
            seen_reasons.add(m["reason"])
            unique_matches.append(m)
    
    if unique_matches:
        # Return first matched reason
        return {
            "blocked": True,
            "reason": unique_matches[0]["reason"],
            "details": unique_matches,
        }
    
    return {
        "blocked": False,
        "reason": None,
        "details": [],
    }


def screen_input(text: str, log_path: str = None) -> List[Dict[str, Any]]:
    """
    Screen user input for suspicious patterns.
    Legacy API - returns list of warnings for backward compatibility.
    
    Args:
        text: User input text to screen
        log_path: Optional path to log file for suspicious inputs
    
    Returns:
        List of warning dicts with pattern matches
    """
    result = block_check(text)
    
    warnings = []
    for detail in result.get("details", []):
        warnings.append({
            "type": "pattern_match",
            "description": detail["description"],
            "reason": detail["reason"],
            "pattern": detail["pattern"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    # Log if warnings found and log_path provided
    if warnings and log_path:
        log_suspicious_input(text, warnings, log_path)
    
    return warnings


def log_suspicious_input(text: str, warnings: List[Dict], log_path: str) -> None:
    """Log suspicious input to file for review."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Timestamp: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"Warnings: {len(warnings)}\n")
        for w in warnings:
            f.write(f"  - [{w.get('reason', 'unknown')}] {w['description']}\n")
        f.write(f"\nInput (truncated to 500 chars):\n{text[:500]}\n")
        f.write(f"{'='*60}\n")


def get_risk_level(warnings: List[Dict]) -> str:
    """
    Calculate risk level from warnings.
    
    Returns:
        "low", "medium", or "high"
    """
    if not warnings:
        return "low"
    
    # Any security-related warning is high risk
    high_risk_reasons = {
        "instruction_override", "role_hijack", "exfiltration",
        "credential_request", "dangerous_tool", "command_injection",
        "fake_system_message", "external_reference", "encoded_payload"
    }
    
    for w in warnings:
        if w.get("reason") in high_risk_reasons:
            return "high"
    
    if len(warnings) >= 2:
        return "medium"
    
    return "low"


# CLI usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python prompt_safety_screen.py <text_to_screen>")
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    result = block_check(text)
    
    if result["blocked"]:
        print(f"🚫 BLOCKED: {result['reason']}")
        for detail in result["details"]:
            print(f"   - {detail['description']}")
    else:
        print("✅ No suspicious patterns detected.")
