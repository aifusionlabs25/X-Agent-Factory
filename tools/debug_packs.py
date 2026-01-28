"""
Debug Packs
"""
from coverage_loader import CoverageLoader

def debug():
    loader = CoverageLoader()
    cp = loader.load_coverage_pack("coverage_pack_smoke_v1")
    vp = loader.load_vertical_pack("vertical_pack_smoke_v1")
    
    print(f"CP Regions: {len(cp.get('regions', []))}")
    for r in cp.get('regions', []):
        print(f"  - {r.get('region_tag')} (P: {r.get('priority')})")
        
    print(f"VP Trades: {len(vp.get('trades', []))}")
    for t in vp.get('trades', []):
        print(f"  - {t.get('trade_id')}")
        print(f"    Templates: {len(t.get('query_templates', []))}")
        
    # Generate
    qs = loader.generate_queries(cp, vp)
    print(f"Generated Queries: {len(qs)}")
    for q in qs:
        print(f"  Q: {q['text']}")

if __name__ == "__main__":
    debug()
