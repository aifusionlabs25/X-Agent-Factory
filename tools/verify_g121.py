import os
import sys

def verify_kb_pack(client_slug):
    print(f"--- Verifying G12.1 KB Pack for {client_slug} ---")
    
    kb_dir = f"agents/clients/{client_slug}/kb/"
    required_files = [
        "firm_facts.txt",
        "practice_areas.txt",
        "intake_playbook.txt",
        "faq_objections.txt",
        "routing_escalations.txt",
        "compliance_disclaimers.txt",
        "tone_snippets.txt",
        "kb_seed.txt",
        "intake_fields.txt"
    ]
    
    print("\n[Step 1] File Existence Check...")
    all_files_ok = True
    for f in required_files:
        path = os.path.join(kb_dir, f)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            print(f"  [OK] {f}")
        else:
            print(f"  [MISSING/EMPTY] {f}")
            all_files_ok = False
            
    if not all_files_ok:
        print("CRITICAL: Missing KB files!")
        sys.exit(1)
        
    print("\n[Step 2] Content Logic Check...")
    # Check for "No Legal Advice" in compliance dicts
    comp_path = os.path.join(kb_dir, "compliance_disclaimers.txt")
    with open(comp_path, 'r') as f:
        content = f.read()
        if "No Legal Advice" in content:
             print("  [OK] 'No Legal Advice' present in compliance docs.")
        else:
             print("  [FAIL] 'No Legal Advice' MISSING via compliance docs.")
             sys.exit(1)

    print("\nSUCCESS: G12.1 KB Pack Verified.")

if __name__ == "__main__":
    verify_kb_pack("knowles_law_firm")
