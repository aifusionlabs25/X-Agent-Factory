"""
Coverage Loader - Growth Department (Phase G1.9)
Loads Coverage Packs and Vertical Packs to generate nationwide query batches.

Functions:
- load_coverage_pack(pack_id)
- load_vertical_pack(pack_id)
- generate_queries(coverage, vertical)
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PACKS_DIR = Path(__file__).parent.parent / "growth" / "packs"

class CoverageLoader:
    def __init__(self):
        pass
        
    def _load_yaml(self, path: Path) -> Dict:
        if not path.exists():
            logger.error(f"Pack file not found: {path}")
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load pack {path}: {e}")
            return {}

    def load_coverage_pack(self, pack_name: str) -> Dict:
        """Load a Coverage Pack by filename (without extension)."""
        # Look in coverage folder
        path = PACKS_DIR / "coverage" / f"{pack_name}.yaml"
        return self._load_yaml(path)

    def load_vertical_pack(self, pack_name: str) -> Dict:
        """Load a Vertical Pack by filename (without extension)."""
        # Look in vertical folder
        path = PACKS_DIR / "vertical" / f"{pack_name}.yaml"
        return self._load_yaml(path)

    def generate_queries(self, coverage_pack: Dict, vertical_pack: Dict) -> List[Dict]:
        """
        Generate query batch by crossing Regions x Trades x Templates.
        
        Returns list of Query dicts:
        {
            "region_tag": str,
            "text": str,
            "trade_id": str,
            "template_id": str,
            "max_results": int
        }
        """
        queries = []
        
        regions = coverage_pack.get("regions", [])
        trades = vertical_pack.get("trades", [])
        templates = vertical_pack.get("query_templates", [])
        
        max_queries_per_region = vertical_pack.get("max_queries_per_region", 50)
        default_max_results = vertical_pack.get("max_results_per_query", 20)
        
        # print(f"DEBUG: Regions: {len(regions)}")
        for region in regions:
            region_tag = region.get("region_tag")
            city = region.get("city")
            state = region.get("state")
            metro = region.get("metro", city) # fallback
            zip_code = region.get("zip", "")
            
            region_queries = []
            
            for trade in trades:
                trade_name = trade.get("display_name")
                trade_id = trade.get("trade_id")
                
                for template in templates:
                    template_text = template.get("text", "")
                    service_keywords = template.get("service_keywords", [""])
                    
                    # print(f"DEBUG: Template: {template_text} Keywords: {service_keywords}")
                    
                    for svc in service_keywords:
                        # Render query
                        # Handle optional {service_keyword}
                        if "{service_keyword}" in template_text and not svc:
                            continue # Skip if template needs svc keyword but none provided
                            
                        # Format mapping
                        fmt_map = {
                            "trade": trade_name,
                            "city": city,
                            "state": state,
                            "metro": metro,
                            "zip": zip_code,
                            "service_keyword": svc
                        }
                        
                        try:
                            # partial cleaning of empty spaces if vars missing
                            q_text = template_text.format(**fmt_map)
                            q_text = q_text.replace("  ", " ").strip()
                            # print(f"DEBUG: Generated: {q_text}")
                            
                            region_queries.append({
                                "region_tag": region_tag,
                                "text": q_text,
                                "trade_id": trade_id,
                                "template_id": template.get("template_id"),
                                "max_results": default_max_results
                            })
                        except KeyError as e:
                            # Template required a field this region misses (e.g. {zip})
                            pass
                            
            # Enforce max queries per region
            if len(region_queries) > max_queries_per_region:
                # Simple truncation or prioritization could happen here
                # For now, just take top N
                region_queries = region_queries[:max_queries_per_region]
                
            queries.extend(region_queries)
            
        logger.info(f"Generated {len(queries)} queries across {len(regions)} regions.")
        return queries

if __name__ == "__main__":
    # Smoke test
    loader = CoverageLoader()
    cp = loader.load_coverage_pack("coverage_pack_v1_top_msas")
    vp = loader.load_vertical_pack("vertical_pack_home_services_v1")
    qs = loader.generate_queries(cp, vp)
    if qs:
        print(f"Sample Query: {qs[0]}")
