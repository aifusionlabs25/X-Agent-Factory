"""
Run Orchestrator - Phase G3.0
Executes a sequence of Growth runs defined in a YAML queue file.
Local-safe, sequential execution.

Usage:
  python tools/run_orchestrator.py --queue growth/runs/run_queue.yaml
"""
import sys
import yaml
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_orchestrator(queue_path: str):
    queue_file = Path(queue_path)
    if not queue_file.exists():
        logger.error(f"Queue file not found: {queue_file}")
        sys.exit(1)
        
    with open(queue_file, 'r') as f:
        queue = yaml.safe_load(f)
        
    runs = queue.get("runs", [])
    logger.info(f"Loaded {len(runs)} runs from {queue_file.name}")
    
    enabled_runs = [r for r in runs if r.get("enabled", False)]
    logger.info(f"Found {len(enabled_runs)} enabled runs.")
    
    success_count = 0
    fail_count = 0
    
    for i, run in enumerate(enabled_runs):
        name = run.get("name", "Unnamed Run")
        config_path = run.get("config")
        
        logger.info(f"[{i+1}/{len(enabled_runs)}] Starting Run: {name}")
        logger.info(f"Config: {config_path}")
        
        # Validate config path
        # Assume config path is relative to repo root if not absolute
        root_dir = Path(".").resolve()
        full_config_path = (root_dir / config_path).resolve() if not Path(config_path).is_absolute() else Path(config_path)
        
        if not full_config_path.exists():
            logger.error(f"Config file missing: {full_config_path}")
            fail_count += 1
            continue
            
        # Execute Growth Runner
        cmd = [sys.executable, "tools/growth_runner.py", "--config", str(full_config_path)]
        
        try:
            # Check Gmaps API Key presence (Guardrail)
            # This is also checked in growth_runner but good to fail fast if we can, 
            # though growth_runner is the authority. 
            # We'll rely on growth_runner's exit code.
            
            start_time = datetime.now()
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = datetime.now() - start_time
            
            if result.returncode == 0:
                logger.info(f"Run '{name}' PASSED in {duration}")
                success_count += 1
                # Log outcome?
            else:
                logger.error(f"Run '{name}' FAILED in {duration}")
                logger.error(result.stderr)
                fail_count += 1
                
        except Exception as e:
            logger.error(f"Exception executing run '{name}': {e}")
            fail_count += 1
            
    logger.info("="*30)
    logger.info(f"Orchestration Complete. Success: {success_count}, Failed: {fail_count}")
    
    if fail_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True, help="Path to run_queue.yaml")
    args = parser.parse_args()
    
    run_orchestrator(args.queue)
