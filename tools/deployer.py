#!/usr/bin/env python3
"""
Deployer - Deploy agents to staging/production environments.

Usage:
    python tools/deployer.py --deploy agents/<slug> --env staging
    python tools/deployer.py --deploy agents/<slug> --env production
    python tools/deployer.py --list  # List all deployable agents

Features:
- Uses UMCP tool bus for Tavus/ElevenLabs if configured
- Writes deployment.json to agent folder
- Integrates with run_logger for tracking
- Dry-run mode when UMCP not available
"""
import os
import sys
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add tools directory to path
TOOLS_DIR = Path(__file__).parent
PROJECT_ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

try:
    from run_logger import RunLogger
except ImportError:
    RunLogger = None

try:
    from umcp_client import UMCPClient
except ImportError:
    UMCPClient = None


class Deployer:
    """Deploy agents to staging/production environments."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize deployer.
        
        Args:
            dry_run: If True, simulate deployment without making actual calls
        """
        self.dry_run = dry_run
        self.umcp = UMCPClient() if UMCPClient else None
        self.umcp_available = self.umcp and self.umcp.enabled and self.umcp.ping()
        
        if not self.umcp_available:
            print("ℹ️  UMCP not available - running in dry-run mode")
            self.dry_run = True
    
    def _compute_manifest_hash(self, manifest: Dict[str, Any]) -> str:
        """Compute SHA256 hash of manifest for change detection."""
        manifest_str = json.dumps(manifest, sort_keys=True)
        return hashlib.sha256(manifest_str.encode()).hexdigest()[:16]
    
    def _load_manifest(self, agent_path: Path) -> Optional[Dict[str, Any]]:
        """Load agent manifest.json."""
        manifest_path = agent_path / "manifest.json"
        if not manifest_path.exists():
            print(f"❌ No manifest.json found in {agent_path}")
            return None
        
        with open(manifest_path, 'r') as f:
            return json.load(f)
    
    def _load_deployment(self, agent_path: Path) -> Optional[Dict[str, Any]]:
        """Load existing deployment.json if present."""
        deployment_path = agent_path / "deployment.json"
        if deployment_path.exists():
            with open(deployment_path, 'r') as f:
                return json.load(f)
        return None
    
    def _save_deployment(self, agent_path: Path, deployment: Dict[str, Any]) -> None:
        """Save deployment.json to agent folder."""
        deployment_path = agent_path / "deployment.json"
        with open(deployment_path, 'w') as f:
            json.dump(deployment, f, indent=2)
        print(f"   ✅ Saved: {deployment_path}")
    
    def _deploy_to_tavus(self, agent_path: Path, manifest: Dict[str, Any], env: str) -> Dict[str, Any]:
        """
        Deploy agent to Tavus via UMCP.
        
        Returns:
            Dict with replica_id, conversation_url or error
        """
        # Read system prompt
        system_prompt_path = agent_path / "system_prompt.txt"
        if not system_prompt_path.exists():
            return {"success": False, "error": "No system_prompt.txt found"}
        
        with open(system_prompt_path, 'r') as f:
            system_prompt = f.read()
        
        # Read kb_seed if present
        kb_path = agent_path / "kb_seed.md"
        kb_content = ""
        if kb_path.exists():
            with open(kb_path, 'r') as f:
                kb_content = f.read()
        
        if self.dry_run:
            # Simulate successful deployment
            return {
                "success": True,
                "replica_id": f"dry_run_{manifest.get('client_slug', 'agent')}_{env}",
                "conversation_url": f"https://tavus.io/demo/dry_run_{env}",
                "dry_run": True
            }
        
        # Call Tavus via UMCP
        try:
            result = self.umcp.call_tool("tavus.create_replica", {
                "name": f"{manifest.get('client_slug', 'agent')}_{env}",
                "system_prompt": system_prompt,
                "knowledge_base": kb_content,
                "environment": env
            })
            
            if result and result.get("success"):
                return {
                    "success": True,
                    "replica_id": result.get("replica_id"),
                    "conversation_url": result.get("conversation_url")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown UMCP error") if result else "UMCP call failed"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def deploy(self, agent_path: Path, env: str = "staging", run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Deploy an agent to specified environment.
        
        Args:
            agent_path: Path to agent folder (e.g., agents/nexgen_hvac)
            env: Environment to deploy to (staging or production)
            run_id: Optional run ID for logging
        
        Returns:
            Deployment result dict
        """
        agent_path = Path(agent_path)
        
        if not agent_path.exists():
            return {"success": False, "error": f"Agent path not found: {agent_path}"}
        
        print(f"\n🚀 DEPLOYING: {agent_path.name}")
        print(f"   Environment: {env}")
        print(f"   Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        
        # Load manifest
        manifest = self._load_manifest(agent_path)
        if not manifest:
            return {"success": False, "error": "Failed to load manifest"}
        
        manifest_hash = self._compute_manifest_hash(manifest)
        print(f"   Manifest hash: {manifest_hash}")
        
        # Check existing deployment
        existing = self._load_deployment(agent_path)
        if existing and existing.get("manifest_hash") == manifest_hash and existing.get("env") == env:
            print(f"   ⏭️  Already deployed (same manifest hash)")
            return {"success": True, "skipped": True, "reason": "already_deployed"}
        
        # Deploy to Tavus
        print(f"   📡 Deploying to Tavus...")
        tavus_result = self._deploy_to_tavus(agent_path, manifest, env)
        
        # Collect artifacts deployed
        artifacts_deployed = []
        for artifact in manifest.get("artifacts", []):
            artifact_path = agent_path / artifact.get("path", "")
            if artifact_path.exists():
                artifacts_deployed.append(artifact.get("path"))
        
        # Build deployment record
        deployment = {
            "env": env,
            "deployed_at": datetime.utcnow().isoformat() + "Z",
            "success": tavus_result.get("success", False),
            "external_ids": {
                "tavus_replica_id": tavus_result.get("replica_id"),
                "conversation_url": tavus_result.get("conversation_url")
            },
            "artifacts_deployed": artifacts_deployed,
            "manifest_hash": manifest_hash,
            "run_id": run_id,
            "dry_run": self.dry_run
        }
        
        if not tavus_result.get("success"):
            deployment["error"] = tavus_result.get("error")
            print(f"   ❌ Deployment failed: {tavus_result.get('error')}")
        else:
            print(f"   ✅ Tavus replica: {tavus_result.get('replica_id')}")
            if tavus_result.get("conversation_url"):
                print(f"   🔗 URL: {tavus_result.get('conversation_url')}")
        
        # Save deployment.json
        self._save_deployment(agent_path, deployment)
        
        return deployment
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents with their deployment status."""
        agents_dir = PROJECT_ROOT / "agents"
        agents = []
        
        if not agents_dir.exists():
            return agents
        
        for agent_folder in agents_dir.iterdir():
            if not agent_folder.is_dir():
                continue
            
            manifest = self._load_manifest(agent_folder)
            deployment = self._load_deployment(agent_folder)
            
            agents.append({
                "slug": agent_folder.name,
                "has_manifest": manifest is not None,
                "deployed": deployment is not None and deployment.get("success", False),
                "env": deployment.get("env") if deployment else None,
                "deployed_at": deployment.get("deployed_at") if deployment else None
            })
        
        return agents


def main():
    parser = argparse.ArgumentParser(description="Deploy agents to staging/production")
    parser.add_argument("--deploy", metavar="PATH", help="Agent path to deploy (e.g., agents/nexgen_hvac)")
    parser.add_argument("--env", choices=["staging", "production"], default="staging", help="Target environment")
    parser.add_argument("--dry-run", action="store_true", help="Simulate deployment without making calls")
    parser.add_argument("--list", action="store_true", help="List all agents and deployment status")
    parser.add_argument("--no-log", action="store_true", help="Disable run logging")
    
    args = parser.parse_args()
    
    if args.list:
        deployer = Deployer(dry_run=True)
        agents = deployer.list_agents()
        
        print("\n📦 AGENT DEPLOYMENT STATUS")
        print("=" * 50)
        
        for agent in agents:
            status = "✅ DEPLOYED" if agent["deployed"] else "⬜ NOT DEPLOYED"
            env = f"({agent['env']})" if agent["env"] else ""
            print(f"   {agent['slug']}: {status} {env}")
        
        deployed = sum(1 for a in agents if a["deployed"])
        print(f"\n   Total: {len(agents)} agents, {deployed} deployed")
        return
    
    if not args.deploy:
        parser.print_help()
        return
    
    # Normalize path
    agent_path = Path(args.deploy)
    if not agent_path.is_absolute():
        agent_path = PROJECT_ROOT / agent_path
    
    # Initialize deployer
    deployer = Deployer(dry_run=args.dry_run)
    
    # Run with logging
    if RunLogger and not args.no_log:
        with RunLogger("deployer", disabled=False) as logger:
            logger.log(f"Deploying {agent_path.name} to {args.env}")
            result = deployer.deploy(agent_path, args.env, run_id=logger.run_id)
            logger.set_output("deployment", result)
            
            if result.get("success"):
                logger.log(f"✅ Deployment successful")
            else:
                logger.log(f"❌ Deployment failed: {result.get('error')}")
    else:
        result = deployer.deploy(agent_path, args.env)
    
    # Exit code based on success
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
