import os
import sys
import glob
import json

def verify_guardrails(client_slug):
    print(f"--- Verifying G13.1 Compliance Hardening for {client_slug} ---")
    
    base_dir = f"agents/clients/{client_slug}"
    kb_dir = os.path.join(base_dir, "kb")
    guard_dir = os.path.join(kb_dir, "guardrails")
    manifest_path = os.path.join(base_dir, "kb_manifest.json")
    
    # 1. Guardrail Files Check
    print("\n[Step 1] Guardrail Files Validation...")
    required_guardrails = [
        "compliance_disclaimers.txt",
        "prohibited_responses.txt",
        "recording_and_privacy.txt",
        "emergency_protocols.txt"
    ]
    
    all_ok = True
    for f in required_guardrails:
        path = os.path.join(guard_dir, f)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            print(f"  [OK] guardrails/{f}")
        else:
            print(f"  [FAIL] guardrails/{f} Missing/Empty!")
            all_ok = False
            
    if not all_ok:
        sys.exit(1)

    # 2. Surgical Edits Check
    print("\n[Step 2] Surgical Edits Validation...")
    
    # Intake Playbook
    playbook_path = os.path.join(kb_dir, "intake_playbook.txt")
    with open(playbook_path, 'r') as f:
        content = f.read()
        if "compliance_disclaimers.txt" in content:
            print("  [OK] intake_playbook.txt references mandatory disclaimer.")
        else:
            print("  [FAIL] intake_playbook.txt missing disclaimer cross-ref.")
            sys.exit(1)

    # FAQ
    faq_path = os.path.join(kb_dir, "faq_objections.txt")
    with open(faq_path, 'r') as f:
        content = f.read()
        if "Is this conversation confidential?" in content:
            print("  [OK] faq_objections.txt contains confidential Q.")
        else:
             print("  [FAIL] faq_objections.txt missing confidential Q.")
             sys.exit(1)

    # Escalations
    routing_path = os.path.join(kb_dir, "routing_escalations.txt")
    with open(routing_path, 'r') as f:
        content = f.read()
        if "emergency_protocols.txt" in content:
            print("  [OK] routing_escalations.txt references emergency protocols.")
        else:
             print("  [FAIL] routing_escalations.txt missing emergency cross-ref.")
             sys.exit(1)
             
    # 3. Manifest Priority Check
    print("\n[Step 3] Manifest Priority Check...")
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        first_file = manifest['files'][0]
        if "guardrails" in first_file['filename']:
             print(f"  [OK] First manifest file is a guardrail: {first_file['filename']}")
        else:
             print(f"  [FAIL] First manifest file is NOT a guardrail: {first_file['filename']}")
             sys.exit(1)

    print("\nSUCCESS: G13.1 Compliance Hardening Verified.")

if __name__ == "__main__":
    verify_guardrails("knowles_law_firm")
