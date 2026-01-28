"""
Generate Growth Report - Phase G3.0
Generates a weekly markdown report of the Growth Engine's performance.

Usage:
  python tools/generate_report.py --db growth/db/growth.db --out growth/reports/weekly_report.md
"""
import sys
import json
import logging
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# Import DB (hacky relative import, assuming standard layout)
sys.path.append(str(Path(__file__).parent))
from growth_db import GrowthDB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_report(db_path: Path, out_path: Path):
    db = GrowthDB(db_path=db_path)
    stats = db.get_weekly_stats()
    
    # Calculate conversion rates
    exported = stats.get("total_exported", 0)
    contacted = stats.get("total_contacted", 0)
    meetings = stats.get("meetings", 0)
    won = stats.get("won", 0)
    
    contact_rate = (contacted / exported * 100) if exported > 0 else 0
    meeting_rate = (meetings / contacted * 100) if contacted > 0 else 0
    win_rate = (won / meetings * 100) if meetings > 0 else 0
    
    report_content = f"""# Weekly Growth Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Pipeline Summary
| Stage | Count | Rate |
|-------|-------|------|
| **Exported** | {exported} | - |
| **Contacted** | {contacted} | {contact_rate:.1f}% (of exported) |
| **Meetings** | {meetings} | {meeting_rate:.1f}% (of contacted) |
| **Won** | {won} | {win_rate:.1f}% (of meetings) |

## Health Metrics
- **Suppressed Candidates**: {stats.get('suppressed', 0)}
- **Database Path**: `{db_path}`

## Key Actions
- [ ] Review `campaign_notes.md` for recent runs.
- [ ] Process outcome inbox (`python tools/ingest_outcomes.py --batch ...`)
"""
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    logger.info(f"Report generated: {out_path}")
    print(report_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    
    generate_report(Path(args.db), Path(args.out))
