"""
GRANDMASTER UTILS
Utilities for the Grandmaster Loop: Validation and Patching.
"""

import json
import jsonschema
import sys
import shutil
import re
from pathlib import Path
from datetime import datetime

# Config
BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "co_schema.json"

import hashlib

def load_schema():
    if not SCHEMA_PATH.exists():
        print(f"[ERROR] Schema not found: {SCHEMA_PATH}")
        sys.exit(1)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_change_order(co_path):
    """
    Validates a Change Order JSON against co_schema.json.
    """
    co_path = Path(co_path)
    if not co_path.exists():
        print(f"[FAIL] CO file not found: {co_path}")
        return False

    try:
        with open(co_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        schema = load_schema()
        jsonschema.validate(instance=data, schema=schema)
        # print(f"[PASS] Schema Validation: {co_path.name}")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"[FAIL] Schema Validation Failed: {e.message}")
        print(f"Path: {e.path}")
        return False
    except json.JSONDecodeError:
        print(f"[FAIL] Invalid JSON: {co_path.name}")
        return False
    except Exception as e:
        print(f"[FAIL] Check Error: {e}")
        return False

def get_file_hash(path):
    if not path.exists(): return "MISSING"
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def preview_change_order(co_path, target_dir):
    """
    Previews changes defined in CO JSON without applying them.
    """
    co_path = Path(co_path)
    target_dir = Path(target_dir)
    
    if not validate_change_order(co_path):
        print("[ABORT] Invalid Change Order.")
        return False
        
    with open(co_path, "r", encoding="utf-8") as f:
        co_data = json.load(f)
        
    print(f"\n=== PREVIEW: {co_path.name} ===")
    print(f"Goal: {co_data.get('objective', {}).get('notes', 'N/A')}")
    print(f"Cycle: {co_data.get('cycle')}")
    
    changes = co_data.get("changes", [])
    print(f"--- {len(changes)} PENDING CHANGES ---")
    
    for change in changes:
        target_file_name = change["target_file"]
        target_file_path = target_dir / target_file_name
        op = change["operation"]
        
        print(f"\n[Change {change['change_id']}]")
        print(f"Target: {target_file_name}")
        print(f"Operation: {op}")
        print(f"Rationale: {change['rationale']}")
        
        if not target_file_path.exists():
            print(f"WARNING: Target file missing: {target_file_path}")
            continue
            
        content = target_file_path.read_text(encoding="utf-8")
        
        # simple check for locator
        locator = change["locator"]
        found = False
        if locator["type"] == "anchor_text":
            if locator["text"] in content: found = True
        elif locator["type"] == "regex":
            if re.search(locator["pattern"], content): found = True
        elif locator["type"] == "line_range":
            lines = content.splitlines()
            if locator["line_start"] <= len(lines): found = True
            
        print(f"Locator Found: {found}")
        
    print("\n[PREVIEW COMPLETE] No changes applied.")
    return True

def apply_change_order(co_path, target_dir):
    """
    Applies changes defined in CO JSON to files in target_dir.
    Target files must exist (scratchpad copies).
    """
    co_path = Path(co_path)
    target_dir = Path(target_dir)
    
    if not validate_change_order(co_path):
        print("[ABORT] Cannot apply invalid Change Order.")
        return False
        
    with open(co_path, "r", encoding="utf-8") as f:
        co_data = json.load(f)
        
    changes = co_data.get("changes", [])
    print(f"--- APPLYING {len(changes)} CHANGES ---")
    
    applied_record = []
    
    for change in changes:
        target_file_name = change["target_file"] # e.g. system_prompt.txt
        target_file_path = target_dir / target_file_name
        
        if not target_file_path.exists():
            print(f"[SKIP] Target file missing: {target_file_name}")
            continue
            
        content = target_file_path.read_text(encoding="utf-8")
        original_content = content
        
        op = change["operation"]
        locator = change["locator"]
        
        # Locate Target
        start_idx = -1
        end_idx = -1
        
        if locator["type"] == "anchor_text":
            anchor = locator["text"]
            start_idx = content.find(anchor)
            if start_idx == -1:
                print(f"[FAIL] Anchor text not found in {target_file_name}: '{anchor[:20]}...'")
                continue
            end_idx = start_idx + len(anchor)
            
        elif locator["type"] == "regex":
            # Simple regex search
            match = re.search(locator["pattern"], content)
            if not match:
                print(f"[FAIL] Regex not found in {target_file_name}")
                continue
            start_idx = match.start()
            end_idx = match.end()
            
        elif locator["type"] == "line_range":
            lines = content.splitlines(keepends=True)
            l_start = locator["line_start"] - 1 # 1-based to 0-based
            l_end = locator["line_end"] # Exclusive in python slice? No, schema says line_end inclusive usually?
            # Let's assume inclusive for user friendliness
            l_end_idx = l_end 
            
            if l_start < 0 or l_end_idx > len(lines):
                 print(f"[FAIL] Line range out of bounds: {l_start+1}-{l_end}")
                 continue
                 
            # Reconstruct indices from lines?
            # This is hard with simple string manipulation.
            # Easier strategy: modify lines list.
            pass
            
        # Apply Operation (String based for now)
        new_content = content
        
        if op == "replace":
            replacement = change["replacement"]
            new_content = content[:start_idx] + replacement + content[end_idx:]
            
        elif op == "insert_after":
            insertion = change["insertion"]
            new_content = content[:end_idx] + "\n" + insertion + content[end_idx:]
            
        elif op == "insert_before":
            insertion = change["insertion"]
            new_content = content[:start_idx] + insertion + "\n" + content[start_idx:]
            
        elif op == "delete":
            new_content = content[:start_idx] + content[end_idx:]
            
        # Save
        if new_content != original_content:
            target_file_path.write_text(new_content, encoding="utf-8")
            print(f"[OK] Applied {change['change_id']} ({op}) to {target_file_name}")
            applied_record.append(change['change_id'])
        else:
            print(f"[WARN] No change resulted for {change['change_id']}")
    
    # Generate Cycle Manifest
    if applied_record:
        manifest = {
            "schema_version": "cycle_manifest.v1",
            "run_id": co_data["run_id"],
            "cycle": co_data["cycle"],
            "applied_at": datetime.now().isoformat(),
            "co_file": co_path.name,
            "co_hash": get_file_hash(co_path),
            "changes_applied": applied_record,
            "files": {}
        }
        
        for ch in changes:
            tf = ch["target_file"]
            if (target_dir / tf).exists():
                manifest["files"][tf] = get_file_hash(target_dir / tf)
                
        manifest_path = target_dir / "cycle_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"[MANIFEST] Suggested Cycle Manifest written to {manifest_path}")
            
    print("[DONE] Change Order applied.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python grandmaster_utils.py <validate|preview|apply> <file_path> [target_dir]")
        sys.exit(1)
        
    mode = sys.argv[1]
    path_arg = sys.argv[2]
    
    if mode == "validate":
        valid = validate_change_order(path_arg)
        sys.exit(0 if valid else 1)
        
    elif mode == "preview":
        if len(sys.argv) < 4:
            print("Error: Target directory required for preview.")
            sys.exit(1)
        target_arg = sys.argv[3]
        success = preview_change_order(path_arg, target_arg)
        sys.exit(0 if success else 1)
        
    elif mode == "apply":
        if len(sys.argv) < 4:
            print("Error: Target directory required for apply.")
            sys.exit(1)
        target_arg = sys.argv[3]
        success = apply_change_order(path_arg, target_arg)
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
