import os
import sys
import json
import subprocess

def verify_alignment(client_slug):
    print(f"--- Verifying G13.2 Tavus API Alignment for {client_slug} ---")
    
    base_dir = f"agents/clients/{client_slug}"
    manifest_path = os.path.join(base_dir, "kb_manifest.json")
    
    # 1. Manifest Tag Structure Check
    print("\n[Step 1] Manifest Namespaced Tags Check...")
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    global_tags = manifest['project_info'].get('global_tags', [])
    if "client:knowles" in global_tags:
        print(f"  [OK] Found global namespace tag: client:knowles")
    else:
        print(f"  [FAIL] Missing global namespace tags.")
        sys.exit(1)
        
    files = manifest.get('files', [])
    first_file = files[0]
    tags = first_file.get('tags', [])
    
    has_priority = any(t.startswith("priority:") for t in tags)
    has_type = any(t.startswith("type:") for t in tags)
    
    if has_priority and has_type:
        print(f"  [OK] Found namespaced tags in file entry (priority:*, type:*).")
    else:
        print(f"  [FAIL] Missing namespaced tags in first file entry: {tags}")
        sys.exit(1)

    # 2. Sync Tool Execution Check (Dry Run)
    print("\n[Step 2] Running Sync Tool (Dry Run)...")
    try:
        result = subprocess.run(
            [sys.executable, "tools/tavus_kb_sync.py", "--client", client_slug, "--dry-run"],
            capture_output=True,
            text=True,
            check=True
        )
        if "[DRY RUN] POST /v2/documents" in result.stdout:
            print("  [OK] Sync tool ran successfully in dry-run mode.")
        else:
            print("  [FAIL] Sync tool output did not match expectation.")
            print(result.stdout)
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"  [FAIL] Sync tool execution failed: {e}")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)

    print("\nSUCCESS: G13.2 Alignment Verified.")

if __name__ == "__main__":
    verify_alignment("knowles_law_firm")
