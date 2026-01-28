import os
import glob

def cleanup_md():
    kb_dir = "agents/clients/knowles_law_firm/kb/"
    md_files = glob.glob(os.path.join(kb_dir, "*.md"))
    
    print(f"Found {len(md_files)} .md files to delete.")
    for f in md_files:
        try:
            os.remove(f)
            print(f"Deleted: {f}")
        except Exception as e:
            print(f"Error deleting {f}: {e}")

if __name__ == "__main__":
    cleanup_md()
