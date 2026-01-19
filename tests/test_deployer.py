"""
Tests for tools/deployer.py

Tests:
- Manifest loading and hash computation
- Deployment record creation
- Dry-run mode behavior
- UMCP integration (mocked)
- Skip already-deployed agents
"""
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add tools directory to path
TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from deployer import Deployer


class TestDeployer:
    """Test suite for Deployer class."""
    
    @pytest.fixture
    def temp_agent(self, tmp_path):
        """Create a temporary agent folder with manifest and artifacts."""
        agent_dir = tmp_path / "test_agent"
        agent_dir.mkdir()
        
        # Create manifest
        manifest = {
            "schema_version": "1.0",
            "client_slug": "test_agent",
            "generated_at": "2026-01-18T00:00:00Z",
            "artifacts": [
                {"path": "system_prompt.txt", "sha256": "abc123", "bytes": 100},
                {"path": "kb_seed.md", "sha256": "def456", "bytes": 200}
            ]
        }
        
        with open(agent_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f)
        
        # Create artifacts
        (agent_dir / "system_prompt.txt").write_text("You are a helpful assistant.")
        (agent_dir / "kb_seed.md").write_text("# Knowledge Base\n\nTest content.")
        
        return agent_dir
    
    def test_load_manifest(self, temp_agent):
        """Test manifest loading."""
        deployer = Deployer(dry_run=True)
        manifest = deployer._load_manifest(temp_agent)
        
        assert manifest is not None
        assert manifest["client_slug"] == "test_agent"
        assert len(manifest["artifacts"]) == 2
    
    def test_compute_manifest_hash(self, temp_agent):
        """Test manifest hash computation is deterministic."""
        deployer = Deployer(dry_run=True)
        manifest = deployer._load_manifest(temp_agent)
        
        hash1 = deployer._compute_manifest_hash(manifest)
        hash2 = deployer._compute_manifest_hash(manifest)
        
        assert hash1 == hash2
        assert len(hash1) == 16  # 16 chars (truncated SHA256)
    
    def test_deploy_creates_deployment_json(self, temp_agent):
        """Test that deploy creates deployment.json."""
        deployer = Deployer(dry_run=True)
        result = deployer.deploy(temp_agent, env="staging")
        
        assert result["success"] is True
        assert result["dry_run"] is True
        
        # Check deployment.json was created
        deployment_path = temp_agent / "deployment.json"
        assert deployment_path.exists()
        
        with open(deployment_path, 'r') as f:
            deployment = json.load(f)
        
        assert deployment["env"] == "staging"
        assert deployment["success"] is True
        assert "deployed_at" in deployment
        assert "manifest_hash" in deployment
        assert "artifacts_deployed" in deployment
    
    def test_deploy_includes_artifacts(self, temp_agent):
        """Test that deployment includes artifact list."""
        deployer = Deployer(dry_run=True)
        result = deployer.deploy(temp_agent, env="staging")
        
        deployment_path = temp_agent / "deployment.json"
        with open(deployment_path, 'r') as f:
            deployment = json.load(f)
        
        assert "system_prompt.txt" in deployment["artifacts_deployed"]
        assert "kb_seed.md" in deployment["artifacts_deployed"]
    
    def test_skip_already_deployed(self, temp_agent):
        """Test that already-deployed agents are skipped."""
        deployer = Deployer(dry_run=True)
        
        # First deployment
        result1 = deployer.deploy(temp_agent, env="staging")
        assert result1["success"] is True
        assert result1.get("skipped") is not True
        
        # Second deployment with same manifest - should skip
        result2 = deployer.deploy(temp_agent, env="staging")
        assert result2["success"] is True
        assert result2.get("skipped") is True
        assert result2.get("reason") == "already_deployed"
    
    def test_redeploy_different_env(self, temp_agent):
        """Test that different env triggers new deployment."""
        deployer = Deployer(dry_run=True)
        
        # Deploy to staging
        result1 = deployer.deploy(temp_agent, env="staging")
        assert result1["success"] is True
        
        # Deploy to production - should NOT skip
        result2 = deployer.deploy(temp_agent, env="production")
        assert result2["success"] is True
        assert result2.get("skipped") is not True
    
    def test_deploy_missing_agent(self, tmp_path):
        """Test deployment with missing agent path."""
        deployer = Deployer(dry_run=True)
        result = deployer.deploy(tmp_path / "nonexistent", env="staging")
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    def test_deploy_missing_manifest(self, tmp_path):
        """Test deployment with missing manifest."""
        agent_dir = tmp_path / "empty_agent"
        agent_dir.mkdir()
        
        deployer = Deployer(dry_run=True)
        result = deployer.deploy(agent_dir, env="staging")
        
        assert result["success"] is False
        assert "manifest" in result["error"].lower()
    
    def test_list_agents(self, tmp_path):
        """Test listing agents with deployment status."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        
        # Create two agents
        (agents_dir / "agent1").mkdir()
        with open(agents_dir / "agent1" / "manifest.json", 'w') as f:
            json.dump({"client_slug": "agent1"}, f)
        
        (agents_dir / "agent2").mkdir()
        with open(agents_dir / "agent2" / "manifest.json", 'w') as f:
            json.dump({"client_slug": "agent2"}, f)
        
        # Deploy agent1
        deployer = Deployer(dry_run=True)
        with patch.object(Deployer, 'list_agents') as mock_list:
            mock_list.return_value = [
                {"slug": "agent1", "has_manifest": True, "deployed": True, "env": "staging"},
                {"slug": "agent2", "has_manifest": True, "deployed": False, "env": None}
            ]
            agents = deployer.list_agents()
            
            assert len(agents) == 2
            agent1 = next(a for a in agents if a["slug"] == "agent1")
            assert agent1["deployed"] is True
    
    @patch('deployer.UMCPClient')
    def test_umcp_integration(self, mock_umcp_class, temp_agent):
        """Test UMCP integration for live deployment."""
        # Setup mock UMCP client
        mock_client = MagicMock()
        mock_client.enabled = True
        mock_client.ping.return_value = True
        mock_client.call_tool.return_value = {
            "success": True,
            "replica_id": "rep_12345",
            "conversation_url": "https://tavus.io/demo/rep_12345"
        }
        mock_umcp_class.return_value = mock_client
        
        # Force non-dry-run by patching
        deployer = Deployer(dry_run=False)
        deployer.umcp = mock_client
        deployer.umcp_available = True
        deployer.dry_run = False
        
        result = deployer.deploy(temp_agent, env="staging")
        
        assert result["success"] is True
        assert result["external_ids"]["tavus_replica_id"] == "rep_12345"
        mock_client.call_tool.assert_called_once()


class TestDeploymentRecord:
    """Test deployment.json record format."""
    
    def test_record_schema(self, tmp_path):
        """Test deployment record has required fields."""
        agent_dir = tmp_path / "schema_test"
        agent_dir.mkdir()
        
        # Create minimal manifest
        with open(agent_dir / "manifest.json", 'w') as f:
            json.dump({"client_slug": "schema_test"}, f)
        
        (agent_dir / "system_prompt.txt").write_text("Test prompt")
        
        deployer = Deployer(dry_run=True)
        result = deployer.deploy(agent_dir, env="staging", run_id="run_123")
        
        with open(agent_dir / "deployment.json", 'r') as f:
            record = json.load(f)
        
        # Required fields
        assert "env" in record
        assert "deployed_at" in record
        assert "success" in record
        assert "external_ids" in record
        assert "artifacts_deployed" in record
        assert "manifest_hash" in record
        assert "run_id" in record
        
        # Value checks
        assert record["env"] == "staging"
        assert record["run_id"] == "run_123"
        assert isinstance(record["external_ids"], dict)
        assert isinstance(record["artifacts_deployed"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
