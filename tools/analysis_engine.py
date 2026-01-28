
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3

# Hacky relative import for now
import sys
sys.path.append(str(Path(__file__).parent))
from growth_db import GrowthDB

logger = logging.getLogger(__name__)

class AnalysisEngine:
    def __init__(self, db_path: Path = None):
        self.db = GrowthDB(db_path=db_path) if db_path else GrowthDB()

    def get_weekly_metrics(self) -> List[Dict]:
        """Aggregates metrics by week number."""
        with self.db._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Aggregate runs by week
            cursor.execute("""
            SELECT 
                strftime('%Y-%W', started_at) as week,
                COUNT(run_id) as total_runs,
                SUM(total_candidates) as candidates,
                SUM(total_exported) as exported,
                SUM(cost_estimate_usd) as cost
            FROM search_runs
            GROUP BY week
            ORDER BY week DESC
            LIMIT 12
            """)
            weeks = {row['week']: dict(row) for row in cursor.fetchall()}
            
            # Aggregate tasks/outcomes by week (using updated_at or completed_at)
            # This is an approximation based on when the lead status changed
            cursor.execute("""
            SELECT 
                strftime('%Y-%W', updated_at) as week,
                SUM(CASE WHEN status = 'contacted' THEN 1 ELSE 0 END) as contacted,
                SUM(CASE WHEN status = 'booked_meeting' THEN 1 ELSE 0 END) as meetings,
                SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins
            FROM place_status
            GROUP BY week
            ORDER BY week DESC
            LIMIT 12
            """)
            
            for row in cursor.fetchall():
                w = row['week']
                if w not in weeks:
                    weeks[w] = {"week": w, "total_runs": 0, "candidates": 0, "exported": 0, "cost": 0.0}
                weeks[w].update(dict(row))
                
            # Calculate rates
            results = []
            for w, data in weeks.items():
                exported = data.get('exported', 0)
                contacted = data.get('contacted', 0)
                meetings = data.get('meetings', 0)
                wins = data.get('wins', 0)
                
                data['contact_rate'] = (contacted / exported * 100) if exported > 0 else 0
                data['meeting_rate'] = (meetings / contacted * 100) if contacted > 0 else 0
                data['win_rate'] = (wins / meetings * 100) if meetings > 0 else 0
                results.append(data)
                
            # Filter out entries with None week and sort
            valid_results = [r for r in results if r['week']]
            return sorted(valid_results, key=lambda x: x['week'], reverse=True)

    def get_run_metrics(self, run_id: str) -> Dict:
        """Get detailed funnel for a specific run."""
        run = self.db.get_run(run_id)
        if not run:
            return {}
            
        leads = self.db.get_run_leads(run_id)
        
        counts = {
            "total": len(leads),
            "new": 0,
            "contacted": 0,
            "meetings": 0,
            "won": 0,
            "dead": 0
        }
        
        for l in leads:
            s = l.get('status', 'new')
            if s == 'new': counts['new'] += 1
            if s == 'contacted': counts['contacted'] += 1
            if s == 'booked_meeting': counts['meetings'] += 1
            if s == 'won': counts['won'] += 1
            if s == 'dead_end': counts['dead'] += 1
            
        # Funnel (cumulative logic can be applied if needed, but strict status is safer for now)
        # Assuming status moves strictly forward:
        # Actually in our DB status is a single state, so we just report current state counts.
        
        return {
            "run_id": run_id,
            "config": json.loads(run['config_json'] or '{}'),
            "counts": counts,
            "cost": run['cost_estimate_usd']
        }

    def get_operator_metrics(self) -> Dict:
        """Calculate operator efficiency metrics."""
        # Time to First Contact (approximate using task completion vs created_at)
        # Tasks Per Day
        
        with self.db._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Tasks completed in last 7 days
            cursor.execute("""
            SELECT COUNT(*) as recent_done 
            FROM lead_tasks 
            WHERE status='done' 
            AND completed_at > date('now', '-7 days')
            """)
            recent_done = cursor.fetchone()['recent_done']
            
            # Backlog Aging
            cursor.execute("""
            SELECT COUNT(*) as overdue 
            FROM lead_tasks 
            WHERE status='pending' 
            AND due_at < datetime('now')
            """)
            overdue = cursor.fetchone()['overdue']
            
            return {
                "tasks_last_7d": recent_done,
                "avg_tasks_per_day": round(recent_done / 7, 1),
                "backlog_overdue": overdue
            }

    def generate_report_file(self, report_type: str = 'weekly') -> str:
        """Generates a markdown report file."""
        metrics = self.get_weekly_metrics()
        op_stats = self.get_operator_metrics()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"growth_report_{report_type}_{timestamp}.md"
        out_path = Path(__file__).parent.parent / "growth" / "reports" / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# Growth Report: {report_type.upper()}\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            
            f.write("## 👷 Operator Health\n")
            f.write(f"- **Tasks (Last 7d)**: {op_stats['tasks_last_7d']}\n")
            f.write(f"- **Avg Tasks/Day**: {op_stats['avg_tasks_per_day']}\n")
            f.write(f"- **Overdue Backlog**: {op_stats['backlog_overdue']}\n\n")
            
            f.write("## 📊 Weekly Performance\n")
            f.write("| Week | Runs | Exported | Contacted | Rate | Wins | Rate |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            
            for w in metrics:
                f.write(f"| {w['week']} | {w['total_runs']} | {w.get('exported',0)} | {w.get('contacted',0)} | {w.get('contact_rate',0):.1f}% | {w.get('wins',0)} | {w.get('win_rate',0):.1f}% |\n")
                
        return str(out_path)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=['api', 'generate', 'debug'], default='debug')
    parser.add_argument("--type", default='weekly', help="Report type for generation")
    args = parser.parse_args()
    
    engine = AnalysisEngine()
    
    if args.mode == 'api':
        data = {
            "weekly": engine.get_weekly_metrics(),
            "operator": engine.get_operator_metrics()
        }
        print(json.dumps(data, indent=2))
        
    elif args.mode == 'generate':
        path = engine.generate_report_file(args.type)
        print(json.dumps({"success": True, "path": path}))
        
    else:
        # Debug / Raw print
        print("Weekly Metrics:")
        print(json.dumps(engine.get_weekly_metrics(), indent=2))
        print("\nOperator Metrics:")
        print(json.dumps(engine.get_operator_metrics(), indent=2))
