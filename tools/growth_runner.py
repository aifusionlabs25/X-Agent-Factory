"""
Growth Runner - Growth Department Orchestrator (Phase G1.9)
Nationwide Sourcing Engine.

G1.9 ADDITIONS:
- Coverage/Vertical Pack Loading
- Batch Execution via PlacesScout
- SQLite Persistence & Exports
"""
import os
import json
import logging
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from growth_db import GrowthDB
from coverage_loader import CoverageLoader
from places_scout import get_scout as get_places_scout
from growth_exporter import get_exporter
from prospect_enricher import get_enricher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GrowthRunner:
    """
    Phase G1.9: Nationwide Orchestrator.
    """
    
    def __init__(self):
        self.db = GrowthDB()
        self.loader = CoverageLoader()
        self.exporter = get_exporter()
        self.enricher = get_enricher()
        self.places_scout = get_places_scout()
        
        # G3.0 Guardrail
        if not os.getenv("GMAPS_API_KEY"):
            logger.error("CRITICAL: GMAPS_API_KEY missing from environment.")
            raise ValueError("GMAPS_API_KEY is required.")
        
    def run_nationwide(self, coverage_pack: str, vertical_pack: str) -> Dict:
        """Execute a nationwide sourcing run."""
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting Nationwide Run {run_id} ({coverage_pack} x {vertical_pack})")
        
        # 1. Load Packs & Generator Queries
        cp = self.loader.load_coverage_pack(coverage_pack)
        vp = self.loader.load_vertical_pack(vertical_pack)
        
        if not cp or not vp:
            logger.error("Failed to load packs.")
            return {"status": "failed"}
            
        queries = self.loader.generate_queries(cp, vp)
        
        # Log Run Start with Traceability
        self.db.log_run_start({
            "run_id": run_id, 
            "coverage_pack": coverage_pack,
            "vertical_pack_id": vp.get("vertical_pack_id"),
            "config": {
                "vertical": vertical_pack, 
                "max_queries": len(queries)
            }
        })
        
        # 2. Batch Execution (Stage 1)
        # Pass traceability info (pack IDs) to scout via query objects
        for q in queries:
            q["coverage_pack_id"] = cp.get("pack_id")
            q["vertical_pack_id"] = vp.get("vertical_pack_id")
        
        logger.info(f"Executing {len(queries)} queries...")
        prospects = self.places_scout.search_batch(queries, run_id)
        logger.info(f"Discovered {len(prospects)} new candidates.")
        
        # 3. Enrichment (Stage 3 - Selective)
        # G1.9 Alpha: Enrich ALL new candidates (up to global limit)
        # Real production: Pick top scoring only
        enriched_count = 0
        MAX_ENRICH = 50 # Safe default
        
        for p in prospects[:MAX_ENRICH]:
            pid = p.get("gbp_data", {}).get("place_id")
            if pid:
                details = self.places_scout.enrich_place(pid)
                if details:
                    # Update prospect object
                    p["gbp_data"]["phone"] = details.get("nationalPhoneNumber")
                    # Could perform ProspectEnricher website scan here too
                    enriched_count += 1
        
        # 4. Export
        try:
            export_path = self.exporter.export_run(run_id, prospects, {
                "run_id": run_id,
                "total_queries": len(queries),
                "candidates": len(prospects),
                "enriched": enriched_count
            })
            if export_path:
                logger.info(f"Export successful: {export_path}")
            else:
                logger.warning("Export returned empty path (no prospects?)")
        except Exception as e:
            logger.error(f"Export Failed: {e}", exc_info=True)
            export_path = ""
        
        # Log Run End
        self.db.log_run_end(run_id, {
            "candidates": len(prospects),
            "enriched": enriched_count,
            "exported": len(prospects) if export_path else 0,
            "cost_usd": 0.0 # TODO: Calculate
        })
        
        return {
            "run_id": run_id,
            "status": "success",
            "candidates": len(prospects),
            "export_path": export_path
        }

def main():
    parser = argparse.ArgumentParser(description="Growth Radar Runner (G1.9)")
    parser.add_argument("--coverage", help="Coverage pack name")
    parser.add_argument("--vertical", help="Vertical pack name")
    parser.add_argument("--config", help="Path to run config YAML")
    
    args = parser.parse_args()
    
    coverage = args.coverage
    vertical = args.vertical
    
    # Load from Config if provided
    if args.config:
        try:
            with open(args.config, 'r') as f:
                cfg = yaml.safe_load(f)
                if not coverage:
                    coverage = cfg.get("coverage_pack")
                if not vertical:
                    vertical = cfg.get("vertical_pack")
        except Exception as e:
            logger.error(f"Failed to load config {args.config}: {e}")
            exit(1)
    
    if not coverage or not vertical:
        logger.error("Error: Must provide coverage and vertical packs via args or config.")
        exit(1)
        
    runner = GrowthRunner()
    result = runner.run_nationwide(coverage, vertical)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
