"""
Phase 17: ACIP Integration Tests
Tests prompt-injection hardening with --acip flag.

Usage:
    pytest tests/test_acip_integration.py -v
"""
import sys
import subprocess
import shutil
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

PROJECT_ROOT = Path(__file__).parent.parent


class TestACIPIntegration:
    """Tests for ACIP prompt-injection hardening."""
    
    DOSSIER_PATH = PROJECT_ROOT / "ingested_clients" / "example_domain" / "dossier.json"
    AGENT_OUTPUT = PROJECT_ROOT / "agents" / "nexgen_hvac"
    
    def test_acip_flag_produces_hardened_prompt(self):
        """Test that --acip flag produces system_prompt_with_acip.txt."""
        # Run build with --acip --no-log
        result = subprocess.run(
            [sys.executable, "tools/factory_orchestrator.py", 
             "--build-agent", str(self.DOSSIER_PATH), 
             "--acip", "--no-log"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        
        # Check ACIP prompt exists
        acip_path = self.AGENT_OUTPUT / "system_prompt_with_acip.txt"
        assert acip_path.exists(), f"ACIP prompt not found: {acip_path}"
    
    def test_acip_prompt_contains_marker(self):
        """Test that ACIP prompt contains the ACIP marker."""
        acip_path = self.AGENT_OUTPUT / "system_prompt_with_acip.txt"
        
        if not acip_path.exists():
            # Run build first
            subprocess.run(
                [sys.executable, "tools/factory_orchestrator.py", 
                 "--build-agent", str(self.DOSSIER_PATH), 
                 "--acip", "--no-log"],
                cwd=str(PROJECT_ROOT),
                capture_output=True
            )
        
        content = acip_path.read_text(encoding='utf-8')
        
        # Check for ACIP marker
        assert "ACIP_MARKER" in content, "ACIP marker not found in hardened prompt"
    
    def test_acip_prompt_is_nonempty(self):
        """Test that ACIP prompt is non-empty and larger than base prompt."""
        acip_path = self.AGENT_OUTPUT / "system_prompt_with_acip.txt"
        base_path = self.AGENT_OUTPUT / "system_prompt.txt"
        
        assert acip_path.exists(), "ACIP prompt not found"
        assert base_path.exists(), "Base prompt not found"
        
        acip_size = acip_path.stat().st_size
        base_size = base_path.stat().st_size
        
        assert acip_size > 0, "ACIP prompt is empty"
        assert acip_size > base_size, "ACIP prompt should be larger than base prompt"
    
    def test_acip_prompt_contains_security_guidelines(self):
        """Test that ACIP prompt contains security guidelines."""
        acip_path = self.AGENT_OUTPUT / "system_prompt_with_acip.txt"
        content = acip_path.read_text(encoding='utf-8')
        
        # Check for key security sections
        assert "Prompt Injection Defense" in content, "Security section not found"
        assert "Defensive Markers" in content, "Defensive markers section not found"
    
    def test_baseline_unchanged_without_acip(self):
        """Test that baseline output is unchanged when --acip is not used."""
        # Run build WITHOUT --acip
        result = subprocess.run(
            [sys.executable, "tools/factory_orchestrator.py", 
             "--build-agent", str(self.DOSSIER_PATH), 
             "--no-log"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        
        # Check base prompt exists
        base_path = self.AGENT_OUTPUT / "system_prompt.txt"
        assert base_path.exists(), "Base prompt not found"
        
        # Verify base prompt does NOT contain ACIP marker
        content = base_path.read_text(encoding='utf-8')
        assert "ACIP_MARKER" not in content, "ACIP marker should not be in base prompt"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
