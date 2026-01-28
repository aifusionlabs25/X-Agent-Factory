import zipfile
import os
import argparse
from pathlib import Path

def zip_kb(slug):
    run_id = "local-run-001"
    output_filename = f"kb-pack-{run_id}-{slug}.zip"
    
    # Base directory is current workspace
    base_dir = Path(".")
    target_dir = base_dir / "agents" / slug / "kb"
    
    if not target_dir.exists():
        print(f"❌ Target directory not found: {target_dir}")
        return

    print(f"📦 Packaging QA Bundle: {output_filename}")
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk the directory
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                file_path = Path(root) / file
                # Preserve path starting from 'agents/'
                # root is e.g. 'agents/slug/kb'
                # We want the archive to have 'agents/slug/kb/file.md'
                archive_name = file_path.relative_to(base_dir)
                zipf.write(file_path, archive_name)
                print(f"  + {archive_name}")
                
    print(f"✅ Created {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()
    zip_kb(args.slug)
