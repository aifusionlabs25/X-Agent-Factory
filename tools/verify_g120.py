import os
import sys
import hashlib

def verify_overlay():
    print("--- Verifying G12.0 Knowles Law Firm Overlay (Hardened) ---")
    
    # 1. Verify Base Template Integrity
    base_files = [
        "agents/attorney_intake/system_prompt.txt",
        "agents/attorney_intake/persona_context.md"
    ]
    print("\n[Step 1] Verifying Base Template Integrity...")
    for f in base_files:
        if os.path.exists(f):
            print(f"  [OK] {f}")
        else:
            print(f"  [MISSING] {f}")
            sys.exit(1)

    # 2. Strict String Checks on Overlay
    prompt_path = "agents/clients/knowles_law_firm/system_prompt.txt"
    with open(prompt_path, 'r') as f:
        content = f.read()
        
    required_strings = [
        "(602) 702-5431",
        "Phoenix", "Mesa", "Scottsdale", # Offices
        "legal advice", # Disclaimer part
        "attorney-client relationship", # Disclaimer part
        "911", # Emergency
        "In Custody", "Court < 72h", # Priorities
        "Preferred Contact Method",
        "Consent"
    ]
    
    print("\n[Step 2] Hardened String Checks (System Prompt)...")
    all_ok = True
    for s in required_strings:
        if s in content:
            print(f"  [OK] Found: '{s}'")
        else:
            print(f"  [FAIL] Missing: '{s}'")
            all_ok = False
            
    if not all_ok:
        print("CRITICAL: Overlay missing required hardened strings!")
        sys.exit(1)

    print("\nSUCCESS: G12.0 Hardening Verified.")

if __name__ == "__main__":
    verify_overlay()
