"""
MCP Agent Mail Client
Lightweight wrapper for MCP Agent Mail coordination.

Usage:
    from agent_mail_client import AgentMailClient
    
    client = AgentMailClient()
    client.send_message(to="nova", subject="Test", body="Hello")
"""
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import requests
except ImportError:
    requests = None


# Default configuration
DEFAULT_AGENT_MAIL_URL = "http://localhost:8025"
DEFAULT_AGENT_ID = "factory_orchestrator"


class AgentMailClient:
    """Client for MCP Agent Mail server."""
    
    def __init__(self, url: Optional[str] = None, agent_id: Optional[str] = None):
        """
        Initialize Agent Mail client.
        
        Args:
            url: Agent Mail server URL (defaults to AGENT_MAIL_URL env var)
            agent_id: This agent's identity (defaults to factory_orchestrator)
        """
        self.url = url or os.environ.get("AGENT_MAIL_URL", DEFAULT_AGENT_MAIL_URL)
        self.agent_id = agent_id or os.environ.get("AGENT_ID", DEFAULT_AGENT_ID)
        self._enabled = bool(os.environ.get("AGENT_MAIL_URL") or url)
    
    @property
    def enabled(self) -> bool:
        """Check if Agent Mail is configured."""
        return self._enabled and requests is not None
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Agent Mail server."""
        if not self.enabled:
            return None
        
        try:
            url = f"{self.url.rstrip('/')}/{endpoint.lstrip('/')}"
            response = requests.request(method, url, timeout=5, **kwargs)
            response.raise_for_status()
            return response.json() if response.text else {}
        except Exception as e:
            # Silent fail for advisory notifications
            print(f"   ⚠️ Agent Mail: {e}")
            return None
    
    def ping(self) -> bool:
        """Health check for Agent Mail server."""
        result = self._request("GET", "/health")
        return result is not None and result.get("status") == "ok"
    
    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        tags: Optional[List[str]] = None,
        thread_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Send a message to another agent.
        
        Args:
            to: Recipient agent ID
            subject: Message subject
            body: Message body
            tags: Optional list of tags for searching
            thread_id: Optional thread ID to continue conversation
        
        Returns:
            Message ID if sent, None otherwise
        """
        payload = {
            "from": self.agent_id,
            "to": to,
            "subject": subject,
            "body": body,
            "tags": tags or [],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if thread_id:
            payload["thread_id"] = thread_id
        
        result = self._request("POST", "/messages", json=payload)
        return result.get("message_id") if result else None
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search message history.
        
        Args:
            query: Search query
            limit: Maximum results to return
        
        Returns:
            List of matching messages
        """
        result = self._request("GET", f"/messages/search?q={query}&limit={limit}")
        return result.get("messages", []) if result else []
    
    def list_threads(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List conversation threads.
        
        Args:
            limit: Maximum threads to return
        
        Returns:
            List of threads with latest message
        """
        result = self._request("GET", f"/threads?limit={limit}")
        return result.get("threads", []) if result else []
    
    def lease(self, files: List[str], ttl: int = 300) -> Optional[str]:
        """
        Create an advisory file lease.
        
        Args:
            files: List of file paths or glob patterns
            ttl: Time-to-live in seconds
        
        Returns:
            Lease ID if created, None otherwise
        """
        payload = {
            "agent_id": self.agent_id,
            "files": files,
            "ttl": ttl,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        result = self._request("POST", "/leases", json=payload)
        return result.get("lease_id") if result else None
    
    def release_lease(self, lease_id: str) -> bool:
        """
        Release an advisory file lease.
        
        Args:
            lease_id: Lease ID to release
        
        Returns:
            True if released, False otherwise
        """
        result = self._request("DELETE", f"/leases/{lease_id}")
        return result is not None


# Convenience functions for run_logger integration
def notify_intake_complete(url: str, industry: str, dossier_path: str, client_slug: str):
    """Notify that intake is complete."""
    client = AgentMailClient()
    if not client.enabled:
        return
    
    client.send_message(
        to="factory_coordinator",
        subject=f"Intake Complete: {client_slug}",
        body=f"""Intake completed for {client_slug}

URL: {url}
Industry: {industry}
Dossier: {dossier_path}
""",
        tags=["intake", "complete", client_slug, industry.lower()]
    )


def notify_build_complete(client_slug: str, artifacts: List[str], manifest_hash: str):
    """Notify that agent build is complete."""
    client = AgentMailClient()
    if not client.enabled:
        return
    
    client.send_message(
        to="factory_coordinator",
        subject=f"Build Complete: {client_slug}",
        body=f"""Build completed for {client_slug}

Artifacts: {len(artifacts)}
Manifest Hash: {manifest_hash}

Files:
""" + "\n".join(f"- {a}" for a in artifacts),
        tags=["build", "complete", client_slug]
    )


def notify_failure(run_id: str, error: str, tool: str):
    """Notify that a run failed."""
    client = AgentMailClient()
    if not client.enabled:
        return
    
    client.send_message(
        to="factory_coordinator",
        subject=f"Run Failed: {run_id}",
        body=f"""Run {run_id} failed

Tool: {tool}
Error: {error}
""",
        tags=["failure", "error", tool]
    )


if __name__ == "__main__":
    # Quick test
    client = AgentMailClient()
    print(f"Agent Mail URL: {client.url}")
    print(f"Enabled: {client.enabled}")
    
    if client.enabled:
        if client.ping():
            print("✅ Agent Mail server is healthy")
        else:
            print("❌ Agent Mail server not responding")
    else:
        print("ℹ️ Agent Mail not configured (set AGENT_MAIL_URL)")
