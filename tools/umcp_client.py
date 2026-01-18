"""
UMCP Tool Bus Client
Client wrapper for Ultimate MCP Server tool bus.

Usage:
    from umcp_client import UMCPClient
    
    client = UMCPClient()
    tools = client.list_tools()
    result = client.call_tool("tool_name", {"arg": "value"})
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
DEFAULT_UMCP_URL = "http://localhost:8026"
DEFAULT_TIMEOUT = 30


class UMCPClient:
    """Client for Ultimate MCP Server tool bus."""
    
    def __init__(self, url: Optional[str] = None, timeout: Optional[int] = None):
        """
        Initialize UMCP client.
        
        Args:
            url: UMCP server URL (defaults to UMCP_URL env var)
            timeout: Request timeout in seconds
        """
        self.url = url or os.environ.get("UMCP_URL", DEFAULT_UMCP_URL)
        self.timeout = timeout or int(os.environ.get("UMCP_TIMEOUT", DEFAULT_TIMEOUT))
        self._enabled = bool(os.environ.get("UMCP_URL") or url)
        self._tools_cache = None
    
    @property
    def enabled(self) -> bool:
        """Check if UMCP is configured."""
        return self._enabled and requests is not None
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to UMCP server."""
        if not self.enabled:
            return None
        
        try:
            url = f"{self.url.rstrip('/')}/{endpoint.lstrip('/')}"
            response = requests.request(
                method, url, 
                timeout=self.timeout, 
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except Exception as e:
            print(f"   ⚠️ UMCP: {e}")
            return None
    
    def ping(self) -> bool:
        """Health check for UMCP server."""
        result = self._request("GET", "/health")
        return result is not None and result.get("status") == "ok"
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the tool bus.
        
        Returns:
            List of tool definitions with name, description, parameters
        """
        if self._tools_cache is not None:
            return self._tools_cache
        
        result = self._request("GET", "/tools")
        if result and "tools" in result:
            self._tools_cache = result["tools"]
            return self._tools_cache
        return []
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tool by name.
        
        Args:
            name: Tool name (e.g., "tavus.create_video")
        
        Returns:
            Tool definition or None
        """
        tools = self.list_tools()
        for tool in tools:
            if tool.get("name") == name:
                return tool
        return None
    
    def call_tool(self, name: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Call a tool on the tool bus.
        
        Args:
            name: Tool name (e.g., "tavus.create_video")
            args: Tool arguments
        
        Returns:
            Tool result or None on error
        """
        payload = {
            "name": name,
            "arguments": args,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        result = self._request("POST", "/tools/call", json=payload)
        return result
    
    def get_tool_count(self) -> int:
        """Get count of available tools."""
        tools = self.list_tools()
        return len(tools)
    
    def get_namespaces(self) -> List[str]:
        """Get unique tool namespaces."""
        tools = self.list_tools()
        namespaces = set()
        for tool in tools:
            name = tool.get("name", "")
            if "." in name:
                namespaces.add(name.split(".")[0])
        return sorted(namespaces)


def get_umcp_status() -> Dict[str, Any]:
    """
    Get UMCP connection status for run_logger integration.
    
    Returns:
        Status dict with connected, tool_count, namespaces
    """
    client = UMCPClient()
    
    if not client.enabled:
        return {"connected": False, "reason": "not_configured"}
    
    if not client.ping():
        return {"connected": False, "reason": "not_responding"}
    
    return {
        "connected": True,
        "tool_count": client.get_tool_count(),
        "namespaces": client.get_namespaces(),
        "url": client.url
    }


if __name__ == "__main__":
    # Quick status check
    client = UMCPClient()
    print(f"UMCP URL: {client.url}")
    print(f"Enabled: {client.enabled}")
    
    if client.enabled:
        if client.ping():
            print("✅ UMCP server is healthy")
            tools = client.list_tools()
            print(f"📦 Available tools: {len(tools)}")
            for tool in tools[:5]:
                print(f"   - {tool.get('name', 'unknown')}")
            if len(tools) > 5:
                print(f"   ... and {len(tools) - 5} more")
        else:
            print("❌ UMCP server not responding")
    else:
        print("ℹ️ UMCP not configured (set UMCP_URL)")
