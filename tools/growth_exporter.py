"""
Growth Exporter - Phase G1.9
Generates CSV and JSONL exports for Growth Runs.

Outputs:
- leads.csv: User-friendly export
- leads.jsonl: Machine-readable full dump
- summary.json: Run stats
"""
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EXPORTS_DIR = Path(__file__).parent.parent / "growth" / "exports"

class GrowthExporter:
    def __init__(self):
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        
    def export_run(self, run_id: str, prospects: List[Dict], summary: Dict) -> str:
        """Generate exports for a run."""
        if not prospects:
            return ""
            
        # G5.0: Apply Scoring
        from lead_scorer import get_scorer
        scorer = get_scorer()
        for p in prospects:
            score_data = scorer.score_prospect(p)
            p.update(score_data)
            
        run_dir = EXPORTS_DIR / run_id
        run_dir.mkdir(exist_ok=True)
        
        # 1. JSONL (Full Dump)
        jsonl_path = run_dir / "leads.jsonl"
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for p in prospects:
                f.write(json.dumps(p) + "\n")
                
        # 2. CSV (User Friendly)
        csv_path = run_dir / "leads.csv"
        self._write_csv(csv_path, run_id, prospects)
        
        # 3. G3.0: Outbound Ready Artifacts
        self._write_outbound_csv(run_dir / "outbound_import.csv", prospects)
        self._write_campaign_notes(run_dir / "campaign_notes.md", run_id, summary)

        # 4. Summary
        with open(run_dir / "run_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"Exported run {run_id} to {run_dir}")
        return str(run_dir)

    def _write_outbound_csv(self, path: Path, prospects: List[Dict]):
        """Normalized CSV for outreach tools (e.g. Apollo, Instantly)."""
        # Minimal high-value fields
        keys = ["Company", "Website", "Phone", "Address", "City", "State", "Zip", "Variables"]
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for p in prospects:
                gbp = p.get("gbp_data", {})
                
                # Construct custom variables for personalization
                reason = p.get("relevance_reason", "High fit local business")
                
                writer.writerow({
                    "Company": p.get("name"),
                    "Website": (p.get("expanded_urls") or [""])[0],
                    "Phone": gbp.get("phone"),
                    "Address": p.get("formatted_address") or gbp.get("address"),
                    "City": "", # TODO parsing
                    "State": "",
                    "Zip": "",
                    "Variables": f"Persona:{p.get('persona', 'Generic')} | Reason:{reason}"
                })
                
    def _write_campaign_notes(self, path: Path, run_id: str, summary: Dict):
        """Human readable context file."""
        from datetime import datetime
        content = f"""# Campaign Context: {run_id}
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Total Candidates**: {summary.get('candidates')}
**Enriched**: {summary.get('enriched')}

## Strategy
- **Focus**: Local service providers
- **Context**: Detected via Google Places API (New)

## Key Value Props
1. **Missed Calls**: "I saw you might be missing calls..."
2. **Speed to Lead**: "We help you answer instantly..."
3. **Local Dominance**: "Dominate {summary.get('candidates')} competitors..."

## Next Steps
1. Import `outbound_import.csv` into dialer/sender.
2. Review 'Variables' column for personalization.
3. Mark status as 'contacted' in `ingest_outcomes` after campaign.
"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _write_csv(self, path: Path, run_id: str, prospects: List[Dict]):
        # Spec Columns
        fieldnames = [
            "run_id", "region_tag", "source_query", "place_id", "name",
            "category_primary", "formatted_address", "city", "state", "zip",
            "phone", "website", "rating", "user_ratings_total", "business_status",
            "score", "score_reason", "timestamp"
        ]
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for p in prospects:
                gbp = p.get("gbp_data", {})
                enrich = p.get("enrichment", {})
                types = gbp.get("types", [])
                
                # Try to parse city/state/zip from address if not explicit
                # This is rough, G1.9 v2 should use Geocoding if critical
                addr = gbp.get("address", "")
                
                writer.writerow({
                    "run_id": run_id,
                    "region_tag": p.get("region_tag", ""),
                    "source_query": (p.get("evidence") or [{}])[0].get("query", ""),
                    "place_id": gbp.get("place_id", ""),
                    "name": p.get("name"),
                    "category_primary": types[0] if types else "unknown",
                    "formatted_address": addr,
                    "city": "", # TODO: Parse
                    "state": "", # TODO: Parse
                    "zip": "", # TODO: Parse
                    "phone": gbp.get("phone") or enrich.get("phone"),
                    "website": (p.get("expanded_urls") or [""])[0],
                    "rating": 0, # Not in basic search response usually
                    "user_ratings_total": 0,
                    "business_status": "OPERATIONAL", # Assumed if found
                    "score": p.get("score", 0),
                    "score_reason": p.get("score_reason", ""),
                    "timestamp": p.get("discovered_at")
                })

def get_exporter() -> GrowthExporter:
    return GrowthExporter()
