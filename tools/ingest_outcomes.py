"""
Ingest Outcomes - Phase G2.0 (LeadOps Loop)
Ingests outcome CSVs to update prospect statuses in growth.db.

Usage:
  python tools/ingest_outcomes.py --db growth/db/growth.db --file growth/outcomes/outcomes_YYYYMMDD.csv
"""
import sys
import csv
import json
import logging
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from urllib.parse import urlparse

# Import DB
sys.path.append(str(Path(__file__).parent))
from growth_db import GrowthDB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OutcomeIngester:
    def __init__(self, db_path: str):
        self.db = GrowthDB(db_path=Path(db_path))
        
    def ingest(self, file_path: Path):
        logger.info(f"Ingesting outcomes from {file_path}")
        
        matches = {
            "file": file_path.name,
            "total": 0,
            "matched_id": 0,
            "matched_domain": 0,
            "matched_phone": 0,
            "matched_fuzzy": 0,
            "unmatched": 0,
            "outcomes": {}
        }
        
        candidates = self._load_csv(file_path)
        matches["total"] = len(candidates)
        
        for row in candidates:
            pid = self._match_place(row)
            outcome = row.get("outcome", "unknown").lower()
            
            # Stats
            matches["outcomes"][outcome] = matches["outcomes"].get(outcome, 0) + 1
            
            if pid:
                if row.get("match_method"):
                    matches[f"matched_{row['match_method']}"] += 1
                    
                # Update DB
                self.db.update_outcome(
                    place_id=pid,
                    outcome=outcome,
                    notes=row.get("notes", ""),
                    source=f"ingest_{file_path.name}"
                )
            else:
                matches["unmatched"] += 1
                logger.warning(f"Unmatched outcome: {row}")
                
        return matches

    def batch_ingest(self, inbox_dir: Path, processed_dir: Path, reports_dir: Path):
        """Process all CSVs in inbox."""
        inbox_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        files = list(inbox_dir.glob("*.csv"))
        if not files:
            logger.info("No files in inbox.")
            return

        overall_report = []
        
        for f in files:
            report = self.ingest(f)
            overall_report.append(report)
            
            # Archive
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{f.stem}_{timestamp}{f.suffix}"
            f.rename(processed_dir / new_name)
            
        # Emit Rollup Report
        report_path = reports_dir / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(overall_report, f, indent=2)
            
        logger.info(f"Batch complete. Processed {len(files)} files. Report: {report_path}")
        print(json.dumps(overall_report, indent=2))

    def _load_csv(self, path: Path) -> List[Dict]:
        rows = []
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
        return rows
        
    def _match_place(self, row: Dict) -> str:
        """
        Matching Priority:
        1. Place ID
        2. Website Domain
        3. Phone
        4. Name + Address (Fuzzy-ish)
        """
        conn = self.db._get_conn()
        cursor = conn.cursor()
        
        # 1. Place ID
        if row.get("place_id"):
            cursor.execute("SELECT place_id FROM places WHERE place_id = ?", (row["place_id"],))
            if cursor.fetchone():
                row["match_method"] = "id"
                return row["place_id"]
                
        # 2. Domain
        if row.get("website"):
            domain = self._extract_domain(row["website"])
            if domain:
                cursor.execute("SELECT place_id FROM places WHERE website LIKE ?", (f"%{domain}%",))
                res = cursor.fetchone()
                if res:
                    row["match_method"] = "domain"
                    return res[0]
                    
        # 3. Phone
        if row.get("phone"):
            phone = self._clean_phone(row["phone"])
            if phone:
                # This is tricky without normalized numbers in DB. 
                # Assuming exact match or simple contains for now.
                cursor.execute("SELECT place_id FROM places WHERE phone LIKE ?", (f"%{phone}%",))
                res = cursor.fetchone()
                if res:
                    row["match_method"] = "phone"
                    return res[0]
        
        # 4. Name (Simple Fallback)
        if row.get("name"):
             cursor.execute("SELECT place_id FROM places WHERE name LIKE ?", (f"%{row['name']}%",))
             res = cursor.fetchone()
             if res:
                 row["match_method"] = "fuzzy"
                 # Verify city if possible? Keeping it simple for G2.0 Alpha
                 return res[0]
                 
        return None
        
    def _extract_domain(self, url: str) -> str:
        try:
            if not url.startswith("http"): url = "http://" + url
            return urlparse(url).netloc.replace("www.", "")
        except:
            return None
            
    def _clean_phone(self, phone: str) -> str:
        return "".join([c for c in phone if c.isdigit()])[-10:] # Last 10 digits

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--file", help="Single file ingest")
    parser.add_argument("--batch", action="store_true", help="Batch ingest from inbox")
    args = parser.parse_args()
    
    ingester = OutcomeIngester(args.db)
    
    if args.batch:
        root = Path(args.db).parent.parent # growth/db/growth.db -> growth/
        ingester.batch_ingest(
            root / "outcomes" / "inbox",
            root / "outcomes" / "processed",
            root / "outcomes" / "reports"
        )
    elif args.file:
        res = ingester.ingest(Path(args.file))
        print(json.dumps(res, indent=2))
    else:
        print("Specify --file or --batch")
