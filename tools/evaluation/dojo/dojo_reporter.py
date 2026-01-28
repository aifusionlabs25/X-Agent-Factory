"""
DOJO REPORTER
Generates a "Winner Package" for a specific simulation run.
Usage: python dojo_reporter.py <run_log_path_or_id> --out <export_dir>
"""

import argparse
import sys
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Config
BASE_DIR = Path(__file__).parent
FACTORY_ROOT = BASE_DIR.parent.parent.parent
LOGS_DIR = BASE_DIR / "dojo_logs"

def find_log(identifier):
    # If path, exist?
    p = Path(identifier)
    if p.exists():
        return p
    
    # Else search logs
    # Identifier could be "run_id" or "timestamp"
    # Recursive search?
    for client_dir in LOGS_DIR.iterdir():
        if client_dir.is_dir():
            for f in client_dir.glob("*.txt"):
                if identifier in f.name:
                    return f
    return None

def generate_report(log_path, output_dir):
    log_path = Path(log_path)
    if not log_path.exists():
        print(f"[FAIL] Log not found: {log_path}")
        sys.exit(1)

    # 1. Gather Artifacts
    run_id = log_path.stem # e.g. 20260123_120000_legal_intake
    base_dir = log_path.parent
    
    score_file = base_dir / f"{run_id}.score.json"
    sys_snapshot = base_dir / f"{run_id}.system_prompt.txt"
    persona_snapshot = base_dir / f"{run_id}.persona_context.txt"
    
    # CRITICAL: Score Check
    if not score_file.exists():
        print(f"[FAIL] Score file missing: {score_file}")
        print("       (Please re-run the simulation or run 'dojo_scorer.py' manually first.)")
        sys.exit(1)
        
    # 2. Read Data
    transcript = log_path.read_text(encoding='utf-8')
    score_data = json.loads(score_file.read_text(encoding='utf-8'))
        
    sys_content = "N/A (Snapshot missing)"
    if sys_snapshot.exists():
        sys_content = sys_snapshot.read_text(encoding='utf-8')
        
    persona_content = "N/A (Snapshot missing)"
    if persona_snapshot.exists():
        persona_content = persona_snapshot.read_text(encoding='utf-8')
        
    # 3. Create Manifest (Chain of Custody)
    manifest = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "verdict": score_data.get("verdict", "UNKNOWN"),
        "score": score_data.get("score", 0),
        "files": {
            "log": log_path.name,
            "score": score_file.name,
            "system_prompt": "system_prompt.txt",
            "persona_context": "persona_context.md" 
        }
    }
    
    # 4. Create Report Markdown
    report_md = f"""# Dojo Match Report: {run_id}

## Match Metadata
- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Run ID**: `{run_id}`
- **Source Log**: `{log_path.name}`

## Outcome
- **Verdict**: {score_data.get('verdict', 'UNKNOWN')}
- **Score**: {score_data.get('score', 'N/A')}
"""

    if score_data.get('breakdown'):
        report_md += "\n## Breakdown\n"
        for k, v in score_data['breakdown'].items():
            report_md += f"- **{k}**: {v}\n"
            
    if score_data.get('artifacts'):
        report_md += "\n## Artifacts Generated\n"
        for k, v in score_data['artifacts'].items():
            report_md += f"- `{k}`: {v}\n"

    report_md += f"""
## Configuration (Winner Payload)

### System Prompt (Copy-Paste)
```text
{sys_content}
```

### Persona Context (Copy-Paste)
```text
{persona_content}
```
"""

    # 5. Export
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    report_file = out / "dojo_match_report.md"
    report_file.write_text(report_md, encoding='utf-8')
    print(f"[REPORT] Generated: {report_file}")
    
    manifest_file = out / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    
    # 6. Zip Package
    zip_path = out / f"winner_package_{run_id}.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(report_file, arcname="dojo_match_report.md")
        zf.write(manifest_file, arcname="manifest.json")
        zf.write(log_path, arcname=f"logs/{log_path.name}")
        zf.write(score_file, arcname=f"logs/{score_file.name}")
        
        # Export logic: Rename extensions for clarity
        if sys_snapshot.exists():
            zf.write(sys_snapshot, arcname="system_prompt.txt")
        if persona_snapshot.exists():
            # Export as MD even if snapshot is TXT
            zf.write(persona_snapshot, arcname="persona_context.md")
            
    print(f"[PACKAGE] Zipped: {zip_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("identifier", help="Run ID or Log Path")
    parser.add_argument("--out", help="Output directory", default="./dojo_export")
    args = parser.parse_args()
    
    log = find_log(args.identifier)
    if log:
        generate_report(log, args.out)
    else:
        print(f"[FAIL] Could not find log for: {args.identifier}")
        sys.exit(1)
