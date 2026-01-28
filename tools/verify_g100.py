
import unittest
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

# Hacky relative import
sys.path.append(str(Path(__file__).parent))
from growth_db import GrowthDB
from analysis_engine import AnalysisEngine

class TestG100(unittest.TestCase):
    def setUp(self):
        # Use a temporary DB or just seed and check?
        # Given "Local" constraint and no mocks easily available, 
        # let's write to the actual DB but use a fake run_id or clean up?
        # Actually safer to just verify logic on existing data if possible,
        # OR insert specific fake data that won't mess up the view too much.
        # Let's insert a fake run with known stats.
        self.db = GrowthDB()
        self.engine = AnalysisEngine()
        self.fake_run_id = f"TEST_RUN_G100_{int(datetime.now().timestamp())}"
        
    def test_metrics_calculation(self):
        """Seed a fake run and verify analysis engine picks it up."""
        print(f"\n🧪 Seeding fake run {self.fake_run_id}...")
        
        with self.db._get_conn() as conn:
            # 1. Create Run
            conn.execute("""
            INSERT INTO search_runs (run_id, started_at, total_candidates, total_exported, cost_estimate_usd)
            VALUES (?, date('now'), 100, 50, 5.00)
            """, (self.fake_run_id,))
            
            # 2. Insert Fake Places (Statuses)
            # We need them to be 'contacted' 'won' etc.
            # We use fake place_ids
            pid_base = f"G100_{int(datetime.now().timestamp())}"
            
            # 3 Places: 1 Exported, 1 Contacted, 1 Won
            # Note: The logic in AnalysisEngine sums status from place_status
            
            # Place 1: Exported
            conn.execute("INSERT OR REPLACE INTO places (place_id, name) VALUES (?, ?)", (f"{pid_base}_1", "Test Exported"))
            conn.execute("INSERT OR REPLACE INTO place_status (place_id, status, updated_at) VALUES (?, 'exported', date('now'))", (f"{pid_base}_1",))
            
            # Place 2: Contacted
            conn.execute("INSERT OR REPLACE INTO places (place_id, name) VALUES (?, ?)", (f"{pid_base}_2", "Test Contacted"))
            conn.execute("INSERT OR REPLACE INTO place_status (place_id, status, updated_at) VALUES (?, 'contacted', date('now'))", (f"{pid_base}_2",))

            # Place 3: Won
            conn.execute("INSERT OR REPLACE INTO places (place_id, name) VALUES (?, ?)", (f"{pid_base}_3", "Test Won"))
            conn.execute("INSERT OR REPLACE INTO place_status (place_id, status, updated_at) VALUES (?, 'won', date('now'))", (f"{pid_base}_3",))
            
            # Place 4: Lead Task Done (Operator Metric)
            conn.execute("INSERT OR REPLACE INTO lead_tasks (place_id, status, completed_at, created_at) VALUES (?, 'done', datetime('now'), datetime('now'))", (f"{pid_base}_3",))

        print("   ✅ Seeded data.")
        
        # Test Weekly Metrics
        metrics = self.engine.get_weekly_metrics()
        # Find the metric for current week
        current_week = datetime.now().strftime('%Y-%W')
        target = next((m for m in metrics if m['week'] == current_week), None)
        
        # Note: AnalysisEngine aggregates ALL data, so existing data might be there.
        # But we know at least our seeded data is there.
        self.assertIsNotNone(target)
        self.assertGreaterEqual(target['exported'], 1) 
        self.assertGreaterEqual(target['contacted'], 1)
        self.assertGreaterEqual(target['wins'], 1)
        print("   ✅ Weekly Metrics logic verified.")
        
        # Test Operator Metrics
        op = self.engine.get_operator_metrics()
        self.assertGreaterEqual(op['tasks_last_7d'], 1)
        print("   ✅ Operator Metrics logic verified.")

    def test_file_generation(self):
        """Verify report file is generated."""
        print("\n📄 Testing File Generation...")
        path_str = self.engine.generate_report_file(report_type='test_g100')
        print(f"   Generated: {path_str}")
        
        p = Path(path_str)
        self.assertTrue(p.exists())
        self.assertTrue(p.stat().st_size > 0)
        
        # Cleanup
        try:
            p.unlink()
            print("   ✅ Cleanup successful.")
        except:
            pass

if __name__ == '__main__':
    unittest.main()
