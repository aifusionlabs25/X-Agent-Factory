import argparse
import json
import sys
from pathlib import Path

# Add parent dir to path to import tools
sys.path.append(str(Path(__file__).parent.parent))
from tools.growth_db import GrowthDB

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_id", help="Run ID to scan", required=True)
    args = parser.parse_args()
    
    db = GrowthDB()
    tasks_created = db.auto_create_tasks(args.run_id)
    
    print(json.dumps({
        "status": "success",
        "tasks_created": tasks_created,
        "message": f"Auto-created {tasks_created} tasks."
    }))

if __name__ == "__main__":
    main()
