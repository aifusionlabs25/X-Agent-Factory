import os
import json
import argparse
import sys
import subprocess

def sync_kb(client_slug, api_key, dry_run=True):
    print(f"--- Tavus KB Sync: {client_slug} (Dry Run: {dry_run}) ---")
    
    base_dir = f"agents/clients/{client_slug}"
    manifest_path = os.path.join(base_dir, "kb_manifest.json")

    print(f"--- Linking Tavus KB for: {client_slug} ---")
    
    # 1. Check G15 Master Gate (Release Ready)
    print("  [GATE] Verifying Release Readiness (G15)...")
    try:
        subprocess.run(
            [sys.executable, "tools/verify_release_ready.py", "--client", client_slug],
            check=True,
            stdout=subprocess.DEVNULL, # Silence output unless error
            stderr=subprocess.PIPE
        )
        print("    [PASS] Verification Gate Passed.")
    except subprocess.CalledProcessError:
        print("    [FAIL] Verification Gate Failed. Run 'python tools/verify_release_ready.py' for details.")
        sys.exit(1)

    # 2. Check Owner Approval
    meta_path = os.path.join(base_dir, "build_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            meta = json.load(f)
            status = meta.get("status", "DRAFT")
            if status != "APPROVED_FOR_DEPLOY":
                 print(f"    [FAIL] Build Status is '{status}'. Must be 'APPROVED_FOR_DEPLOY'.")
                 print("    Update status in build_meta.json or via Dashboard.")
                 sys.exit(1)
            print("    [PASS] Owner Approval Verified.")
    else:
        print("    [FAIL] build_meta.json missing.")
        sys.exit(1)

    # 3. Load Runtime Profile (for Secrets)
    runtime_path = os.path.join(base_dir, "runtime_profile.json")
    if not os.path.exists(runtime_path):
        print("    [FAIL] runtime_profile.json missing.")
        sys.exit(1)
        
    with open(runtime_path, 'r') as f:
        runtime = json.load(f)
    
    # Resolve API Key
    tavus_ref = runtime.get("secrets", {}).get("tavus_api_key_ref")
    api_key = None
    if tavus_ref and tavus_ref.startswith("ENV:"):
        env_var = tavus_ref.split(":")[1]
        api_key = os.environ.get(env_var)
        # Attempt to load from .env.local if missing
        if not api_key:
             # Simple parser
             if os.path.exists("dashboard/.env.local"):
                 with open("dashboard/.env.local") as df:
                     for line in df:
                         if line.startswith(f"{env_var}="):
                             api_key = line.split("=",1)[1].strip()
    
    if not api_key:
        print("    [FAIL] Tavus API Key not found in Environment or .env.local.")
        sys.exit(1)
        
    print(f"  [INFO] Authenticaticating to Tavus with key ref: {tavus_ref}")
        
    if not os.path.exists(manifest_path):
        print(f"Error: Manifest not found at {manifest_path}")
        sys.exit(1)
        
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    project_info = manifest.get('project_info', {})
    global_tags = project_info.get('global_tags', [])
    files = manifest.get('files', [])
    
    print(f"Project: {project_info.get('tavus_project_name')}")
    print(f"Global Tags: {global_tags}")
    print(f"Files to Sync: {len(files)}")
    
    for file_entry in files:
        filename = file_entry['filename']
        local_path = os.path.join(base_dir, "kb", filename)
        
        # Combine global and file-specific tags
        file_tags = file_entry.get('tags', [])
        combined_tags = global_tags + file_tags
        
        # In a real implementation, we would upload the file to a URL accessible by Tavus
        # For now, we mock the API payload
        payload = {
            "document_name": filename,
            "document_url": f"https://repo.url/raw/.../{filename}", # Mock URL
            "tags": combined_tags
        }
        
        if dry_run:
            print(f"\n[DRY RUN] POST /v2/documents")
            print(f"  File: {local_path}")
            print(f"  Payload: {json.dumps(payload, indent=2)}")
        else:
            # TODO: Implement actual API call
            print(f"Skipping actual API call (Not implemented in this phase)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync KB to Tavus")
    parser.add_argument("--client", required=True, help="Client slug (e.g. knowles_law_firm)")
    parser.add_argument("--api-key", help="Tavus API Key")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Perform a dry run")
    
    args = parser.parse_args()
    
    sync_kb(args.client, args.api_key, args.dry_run)
