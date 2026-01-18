"""
Phase 16: CM Memory Pack Tests
Tests memory pack generation from run logs.

Usage:
    pytest tests/test_memory_builder.py -v
"""
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))


class TestMemoryBuilder:
    """Tests for CM Memory Pack Builder."""
    
    PROJECT_ROOT = Path(__file__).parent.parent
    RUNS_DIR = PROJECT_ROOT / "runs"
    MEMORY_DIR = PROJECT_ROOT / "memory"
    TEST_CLIENT = "test_client_memory"
    
    @classmethod
    def setup_class(cls):
        """Create a test run log for memory pack testing."""
        # Create test run directory
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        run_id = "test123456789"
        cls.test_run_dir = cls.RUNS_DIR / date_str / run_id
        cls.test_run_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test run metadata
        metadata = {
            "run_id": run_id,
            "tool": "factory_orchestrator",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "end_time": datetime.utcnow().isoformat() + "Z",
            "duration_seconds": 1.5,
            "success": True,
            "command": "python tools/factory_orchestrator.py",
            "args": {
                "mode": "build-agent",
                "dossier": f"ingested_clients/{cls.TEST_CLIENT}/dossier.json"
            },
            "outputs": {
                "client_slug": cls.TEST_CLIENT,
                "success": True
            },
            "errors": []
        }
        
        with open(cls.test_run_dir / "run_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        with open(cls.test_run_dir / "run_summary.md", 'w') as f:
            f.write(f"# Test Run Summary\nClient: {cls.TEST_CLIENT}\n")
    
    @classmethod
    def teardown_class(cls):
        """Clean up test run directory."""
        if cls.test_run_dir.exists():
            shutil.rmtree(cls.test_run_dir.parent)
        
        # Clean up test client memory
        test_memory_dir = cls.MEMORY_DIR / "clients" / cls.TEST_CLIENT
        if test_memory_dir.exists():
            shutil.rmtree(test_memory_dir)
    
    def test_memory_builder_imports(self):
        """Test that memory_builder imports correctly."""
        from memory_builder import (
            load_all_runs,
            build_all_memory_packs,
            build_single_client
        )
        assert callable(load_all_runs)
        assert callable(build_all_memory_packs)
        assert callable(build_single_client)
    
    def test_load_all_runs_finds_test_run(self):
        """Test that load_all_runs finds our test run."""
        from memory_builder import load_all_runs
        
        runs = load_all_runs()
        
        # Find our test run
        test_runs = [r for r in runs if r.get('run_id') == 'test123456789']
        assert len(test_runs) >= 1, "Test run not found in runs"
    
    def test_build_all_memory_packs_succeeds(self):
        """Test that build_all_memory_packs runs without error."""
        from memory_builder import build_all_memory_packs
        
        result = build_all_memory_packs()
        assert result is True
    
    def test_global_playbook_exists(self):
        """Test that global factory_playbook.md is created."""
        playbook_path = self.MEMORY_DIR / "global" / "factory_playbook.md"
        assert playbook_path.exists(), f"Playbook not found: {playbook_path}"
        assert playbook_path.stat().st_size > 0, "Playbook is empty"
    
    def test_global_gotchas_exists(self):
        """Test that global gotchas.md is created."""
        gotchas_path = self.MEMORY_DIR / "global" / "gotchas.md"
        assert gotchas_path.exists(), f"Gotchas not found: {gotchas_path}"
        assert gotchas_path.stat().st_size > 0, "Gotchas is empty"
    
    def test_client_memory_pack_exists(self):
        """Test that client memory_pack.md is created."""
        pack_path = self.MEMORY_DIR / "clients" / self.TEST_CLIENT / "memory_pack.md"
        assert pack_path.exists(), f"Memory pack not found: {pack_path}"
        assert pack_path.stat().st_size > 0, "Memory pack is empty"
    
    def test_client_build_notes_exists(self):
        """Test that client build_notes.md is created."""
        notes_path = self.MEMORY_DIR / "clients" / self.TEST_CLIENT / "build_notes.md"
        assert notes_path.exists(), f"Build notes not found: {notes_path}"
        assert notes_path.stat().st_size > 0, "Build notes is empty"
    
    def test_memory_pack_contains_client_slug(self):
        """Test that memory pack contains the client slug."""
        pack_path = self.MEMORY_DIR / "clients" / self.TEST_CLIENT / "memory_pack.md"
        content = pack_path.read_text(encoding='utf-8')
        assert self.TEST_CLIENT in content, "Client slug not found in memory pack"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
