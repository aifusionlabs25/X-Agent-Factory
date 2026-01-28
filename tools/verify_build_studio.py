import os
import sys
import json
import shutil
import subprocess

def verify_build_studio():
    client_slug = "test_build_studio_client"
    print(f"--- Verifying G14.0 Build Studio Logic ({client_slug}) ---")
    
    # Clean up previous run
    target_dir = f"agents/clients/{client_slug}"
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    # 1. Execute Generate Script
    print("\n[Step 1] Running generate_sku_build.py...")
    payload = {
        "clientName": "Test Build Studio",
        "clientSlug": client_slug,
        "domain": "testbuild.com",
        "region": "Phoenix, AZ",
        "agentName": "Test Agent",
        "roleTitle": "Tester",
        "tavusPersona": "DEFAULT_TEST",
        "pace": "Fast",
        "emotion": "Happy"
    }
    
    try:
        subprocess.run(
            [sys.executable, "tools/generate_sku_build.py", "--json", json.dumps(payload)],
            check=True,
            capture_output=True,
            text=True
        )
        print("  [OK] Script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"  [FAIL] Script execution failed: {e.stderr}")
        sys.exit(1)

    # 2. Verify Artifacts
    print("\n[Step 2] Verifying Artifacts...")
    
    required_files = [
        "client_profile.json",
        "persona_profile.json",
        "build_meta.json",
        "kb_manifest.json",
        "persona_context.txt",
        "system_prompt.txt",
        "exports/tavus_pack.md",
        "kb/guardrails/compliance_disclaimers.txt",
        "kb/firm_facts.txt"
    ]
    
    all_ok = True
    for f in required_files:
        path = os.path.join(target_dir, f)
        if os.path.exists(path):
             print(f"  [OK] Found {f}")
        else:
             print(f"  [FAIL] Missing {f}")
             all_ok = False
             
    if not all_ok:
        sys.exit(1)
        
    # 3. Verify Meta Content
    print("\n[Step 3] Verifying Meta State...")
    with open(os.path.join(target_dir, "build_meta.json"), 'r') as f:
        meta = json.load(f)
        if meta.get("status") == "DRAFT":
            print("  [OK] Status is DRAFT")
        else:
            print(f"  [FAIL] Status IS NOT DRAFT: {meta.get('status')}")
            sys.exit(1)

    print("\nSUCCESS: Build Studio Logic Verified.")
    
    # 4. ICC Check on New Build
    print("\n[Step 4] Running ICC on New Build...")
    try:
        subprocess.run(
            [sys.executable, "tools/verify_icc.py", "--client", client_slug],
            check=True,
            capture_output=True,
            text=True
        )
        print("  [OK] New Build Passed ICC.")
    except subprocess.CalledProcessError as e:
        print(f"  [FAIL] New Build FAILED ICC: {e.stderr}")
        sys.exit(1)

    # Cleanup
    # shutil.rmtree(target_dir) 
    print(f"(kept {target_dir} for inspection)")

if __name__ == "__main__":
    verify_build_studio()
