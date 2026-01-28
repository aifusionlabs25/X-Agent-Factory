import os
import sys
import glob
import json

def verify_packaging(client_slug):
    print(f"--- Verifying G13.0 Packaging for {client_slug} ---")
    
    base_dir = f"agents/clients/{client_slug}"
    manifest_path = os.path.join(base_dir, "kb_manifest.json")
    upload_doc_path = os.path.join(base_dir, "exports", "tavus_kb_upload.md")
    kb_dir = os.path.join(base_dir, "kb")
    
    # 1. Manifest Check
    print("\n[Step 1] Manifest Validation...")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                json.load(f)
            print("  [OK] kb_manifest.json exists and is valid JSON.")
        except json.JSONDecodeError:
            print("  [FAIL] kb_manifest.json is Invalid JSON!")
            sys.exit(1)
    else:
        print("  [FAIL] kb_manifest.json Missing!")
        sys.exit(1)

    # 2. Upload Doc Check
    print("\n[Step 2] Upload Doc Check...")
    if os.path.exists(upload_doc_path):
        print("  [OK] tavus_kb_upload.md exists.")
    else:
        print("  [FAIL] tavus_kb_upload.md Missing!")
        sys.exit(1)

    # 3. MD File Cleanup Check
    print("\n[Step 3] Checking for rogue .md files in KB...")
    md_files = glob.glob(os.path.join(kb_dir, "*.md"))
    if md_files:
        print(f"  [FAIL] Found {len(md_files)} .md files! They must be deleted.")
        for f in md_files:
            print(f"    - {f}")
        sys.exit(1)
    else:
        print("  [OK] No .md files found in KB.")

    # 4. TXT File Sanity Check
    print("\n[Step 4] Checking for .txt files...")
    txt_files = glob.glob(os.path.join(kb_dir, "*.txt"))
    if len(txt_files) >= 9:
         print(f"  [OK] Found {len(txt_files)} .txt files.")
    else:
         print(f"  [WARN] Found only {len(txt_files)} .txt files. Expected ~9.")
    
    print("\nSUCCESS: G13.0 Packaging Verified.")

if __name__ == "__main__":
    verify_packaging("knowles_law_firm")
