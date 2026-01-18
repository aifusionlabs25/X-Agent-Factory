"""
Prompt Safety Screen
Advisory helper that logs suspicious inputs for review.

Usage:
    from prompt_safety_screen import screen_input
    
    warnings = screen_input(user_text)
    if warnings:
        log_suspicious_activity(warnings)
"""
import re
from datetime import datetime
from pathlib import Path


# Suspicious patterns that may indicate prompt injection
SUSPICIOUS_PATTERNS = [
    (r"ignore\s+(previous|prior|above)\s+instructions?", "Instruction override attempt"),
    (r"disregard\s+(your|the)\s+system\s+prompt", "System prompt override attempt"),
    (r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions?", "Restriction bypass attempt"),
    (r"pretend\s+you\s+are\s+a?\s*different\s+ai", "Identity hijack attempt"),
    (r"forget\s+everything\s+(you\s+know|above)", "Memory wipe attempt"),
    (r"you\s+are\s+(now|actually)\s+", "Role reassignment attempt"),
    (r"your\s+new\s+instructions?\s+(are|is)", "New instructions injection"),
    (r"base64\s*:", "Base64 encoded content"),
    (r"\\u[0-9a-fA-F]{4}", "Unicode escape sequences"),
    (r"\x00|\x7f", "Control characters detected"),
]

# High-risk keywords
HIGH_RISK_KEYWORDS = [
    "api key", "api_key", "apikey",
    "password", "secret", "token",
    "credential", "private key",
    "environment variable", "env var",
]


def screen_input(text, log_path=None):
    """
    Screen user input for suspicious patterns.
    
    Args:
        text: User input text to screen
        log_path: Optional path to log file for suspicious inputs
    
    Returns:
        List of warning dicts with pattern matches
    """
    warnings = []
    text_lower = text.lower()
    
    # Check for suspicious patterns
    for pattern, description in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            warnings.append({
                "type": "pattern_match",
                "description": description,
                "pattern": pattern,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
    
    # Check for high-risk keywords
    for keyword in HIGH_RISK_KEYWORDS:
        if keyword in text_lower:
            warnings.append({
                "type": "high_risk_keyword",
                "description": f"High-risk keyword detected: {keyword}",
                "keyword": keyword,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
    
    # Check for unusually long input (potential payload)
    if len(text) > 10000:
        warnings.append({
            "type": "length_warning",
            "description": f"Unusually long input: {len(text)} characters",
            "length": len(text),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    # Log if warnings found and log_path provided
    if warnings and log_path:
        log_suspicious_input(text, warnings, log_path)
    
    return warnings


def log_suspicious_input(text, warnings, log_path):
    """Log suspicious input to file for review."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Timestamp: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"Warnings: {len(warnings)}\n")
        for w in warnings:
            f.write(f"  - {w['description']}\n")
        f.write(f"\nInput (truncated to 500 chars):\n{text[:500]}\n")
        f.write(f"{'='*60}\n")


def get_risk_level(warnings):
    """
    Calculate risk level from warnings.
    
    Returns:
        "low", "medium", or "high"
    """
    if not warnings:
        return "low"
    
    pattern_matches = sum(1 for w in warnings if w["type"] == "pattern_match")
    high_risk_keywords = sum(1 for w in warnings if w["type"] == "high_risk_keyword")
    
    if pattern_matches >= 2 or high_risk_keywords >= 1:
        return "high"
    elif pattern_matches >= 1:
        return "medium"
    else:
        return "low"


# CLI usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python prompt_safety_screen.py <text_to_screen>")
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    warnings = screen_input(text)
    
    if warnings:
        print(f"⚠️ {len(warnings)} warning(s) found:")
        for w in warnings:
            print(f"  - {w['description']}")
        print(f"\nRisk Level: {get_risk_level(warnings).upper()}")
    else:
        print("✅ No suspicious patterns detected.")
