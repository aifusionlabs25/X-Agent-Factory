"""
Phase 12: Happy Path Smoke Test
Validates that the build-agent pipeline produces all required artifacts.

Usage:
    pytest tests/test_happy_path.py -v
"""
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

# Add tools to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))


class TestHappyPath:
    """Smoke tests for the Factory Operational Baseline."""
    
    # Test configuration
    DOSSIER_PATH = Path(__file__).parent.parent / "ingested_clients" / "example_domain" / "dossier.json"
    AGENTS_ROOT = Path(__file__).parent.parent / "agents"
    EXPECTED_SLUG = "nexgen_hvac"
    
    @classmethod
    def setup_class(cls):
        """Clean up any existing test artifacts before running."""
        output_dir = cls.AGENTS_ROOT / cls.EXPECTED_SLUG
        if output_dir.exists():
            shutil.rmtree(output_dir)
    
    @classmethod
    def teardown_class(cls):
        """Optionally clean up after tests (disabled to allow inspection)."""
        # Uncomment to enable cleanup:
        # output_dir = cls.AGENTS_ROOT / cls.EXPECTED_SLUG
        # if output_dir.exists():
        #     shutil.rmtree(output_dir)
        pass
    
    def test_01_dossier_exists(self):
        """Verify the canonical example dossier exists."""
        assert self.DOSSIER_PATH.exists(), f"Dossier not found: {self.DOSSIER_PATH}"
    
    def test_02_dossier_is_valid(self):
        """Validate dossier against JSON Schema."""
        from schema_validator import validate_dossier
        valid, error = validate_dossier(str(self.DOSSIER_PATH))
        assert valid, f"Dossier validation failed: {error}"
    
    def test_03_build_agent_succeeds(self):
        """Run the build-agent command and verify exit code 0."""
        result = subprocess.run(
            [sys.executable, "tools/factory_orchestrator.py", "--build-agent", str(self.DOSSIER_PATH)],
            cwd=str(Path(__file__).parent.parent),
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Build failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    
    def test_04_manifest_exists(self):
        """Verify manifest.json was created."""
        manifest_path = self.AGENTS_ROOT / self.EXPECTED_SLUG / "manifest.json"
        assert manifest_path.exists(), f"Manifest not found: {manifest_path}"
    
    def test_05_manifest_is_valid_json(self):
        """Verify manifest.json is valid JSON with required fields."""
        manifest_path = self.AGENTS_ROOT / self.EXPECTED_SLUG / "manifest.json"
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        assert "schema_version" in manifest, "Missing schema_version"
        assert "client_slug" in manifest, "Missing client_slug"
        assert "generated_at" in manifest, "Missing generated_at"
        assert "input_dossier_sha256" in manifest, "Missing input_dossier_sha256"
        assert "artifacts" in manifest, "Missing artifacts"
        assert isinstance(manifest["artifacts"], list), "Artifacts should be a list"
        assert len(manifest["artifacts"]) >= 3, f"Expected at least 3 artifacts, got {len(manifest['artifacts'])}"
    
    def test_06_all_artifacts_exist_and_nonempty(self):
        """Verify every artifact in manifest exists and is non-empty."""
        manifest_path = self.AGENTS_ROOT / self.EXPECTED_SLUG / "manifest.json"
        output_dir = self.AGENTS_ROOT / self.EXPECTED_SLUG
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        for artifact in manifest["artifacts"]:
            artifact_path = output_dir / artifact["path"]
            assert artifact_path.exists(), f"Artifact not found: {artifact_path}"
            assert artifact_path.stat().st_size > 0, f"Artifact is empty: {artifact_path}"
            assert artifact_path.stat().st_size == artifact["bytes"], \
                f"Size mismatch for {artifact['path']}: expected {artifact['bytes']}, got {artifact_path.stat().st_size}"
    
    def test_07_system_prompt_contains_client_name(self):
        """Verify system_prompt.txt contains the client name."""
        system_prompt_path = self.AGENTS_ROOT / self.EXPECTED_SLUG / "system_prompt.txt"
        content = system_prompt_path.read_text(encoding='utf-8')
        assert "NexGen HVAC" in content, "Client name not found in system prompt"
    
    def test_08_kb_seed_contains_pain_points(self):
        """Verify kb_seed.md contains expected pain points."""
        kb_path = self.AGENTS_ROOT / self.EXPECTED_SLUG / "kb_seed.md"
        content = kb_path.read_text(encoding='utf-8')
        assert "Emergency repair costs" in content, "Pain point not found in KB"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
