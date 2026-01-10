#!/usr/bin/env python3
"""
Batch Deep Researcher - Run multiple queries sequentially overnight
Usage: python batch_research.py
"""

import subprocess
import time
import os
from datetime import datetime

# Configuration
AGENT_ID = "luna_veterinary"
MAX_DEPTH = 3
MAX_PAGES = 100

# All research queries for Luna KB
QUERIES = [
    "pet poison control toxic foods dogs cats chocolate xylitol grapes raisins onion garlic antifreeze",
    "when to go emergency vet urgent symptoms dog cat life threatening signs",
    "dog cat vomiting diarrhea lethargy not eating when serious vet visit",
    "pet first aid bleeding wounds cuts burns choking CPR emergency home care",
    "dog bloat symptoms seizures difficulty breathing collapse unresponsive emergency",
    "cat urinary blockage straining symptoms emergency male cat not peeing",
    "puppy kitten sick symptoms emergency when to call vet young pet",
    "after hours vet care pet emergency overnight animal hospital triage",
]

def run_research(query: str, job_num: int):
    """Run a single research job"""
    job_id = f"batch_{int(time.time())}_{job_num}"
    output_dir = os.path.join(os.path.dirname(__file__), "..", "intelligence", "research", job_id)
    script_path = os.path.join(os.path.dirname(__file__), "deep_researcher.py")
    
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] JOB {job_num + 1}/{len(QUERIES)}")
    print(f"Query: {query[:60]}...")
    print(f"{'='*60}")
    
    cmd = [
        "python", script_path,
        "--job-id", job_id,
        "--query", query,
        "--agent", AGENT_ID,
        "--max-depth", str(MAX_DEPTH),
        "--max-pages", str(MAX_PAGES),
        "--output", output_dir
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode == 0:
            print(f"[OK] Job {job_num + 1} complete")
        else:
            print(f"[WARN] Job {job_num + 1} finished with code {result.returncode}")
    except Exception as e:
        print(f"[ERROR] Job {job_num + 1} failed: {e}")
    
    # Small delay between jobs
    time.sleep(2)

def main():
    print("\n" + "="*60)
    print("  LUNA OVERNIGHT RESEARCH - BATCH MODE")
    print(f"  {len(QUERIES)} queries queued")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    for i, query in enumerate(QUERIES):
        run_research(query, i)
    
    print("\n" + "="*60)
    print("  ALL JOBS COMPLETE!")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    main()
