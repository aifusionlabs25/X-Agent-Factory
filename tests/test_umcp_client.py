"""
Phase 19: UMCP Tool Bus Client Tests
Tests the UMCP client wrapper using mocked HTTP.

Usage:
    pytest tests/test_umcp_client.py -v
"""
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from umcp_client import UMCPClient, get_umcp_status


class MockResponse:
    """Mock HTTP response."""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data) if json_data else ""
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class TestUMCPClient:
    """Tests for UMCP Tool Bus client wrapper."""
    
    def test_client_initialization(self):
        """Test client initializes with default values."""
        client = UMCPClient(url="http://test:8026")
        
        assert client.url == "http://test:8026"
        assert client.timeout == 30
    
    def test_client_disabled_without_config(self):
        """Test client is disabled when not configured."""
        with patch.dict('os.environ', {}, clear=True):
            client = UMCPClient()
            assert client._enabled == False
    
    def test_client_enabled_with_url(self):
        """Test client is enabled when URL provided."""
        client = UMCPClient(url="http://test:8026")
        assert client._enabled == True
    
    @patch('umcp_client.requests')
    def test_ping_returns_true_on_healthy(self, mock_requests):
        """Test ping returns True when server is healthy."""
        mock_requests.request.return_value = MockResponse({"status": "ok"})
        
        client = UMCPClient(url="http://test:8026")
        assert client.ping() is True
    
    @patch('umcp_client.requests')
    def test_ping_returns_false_on_error(self, mock_requests):
        """Test ping returns False when server errors."""
        mock_requests.request.side_effect = Exception("Connection refused")
        
        client = UMCPClient(url="http://test:8026")
        assert client.ping() is False
    
    @patch('umcp_client.requests')
    def test_list_tools_returns_tools(self, mock_requests):
        """Test list_tools returns tool list."""
        mock_requests.request.return_value = MockResponse({
            "tools": [
                {"name": "tavus.create_video", "description": "Create video"},
                {"name": "elevenlabs.tts", "description": "Text to speech"}
            ]
        })
        
        client = UMCPClient(url="http://test:8026")
        tools = client.list_tools()
        
        assert len(tools) == 2
        assert tools[0]["name"] == "tavus.create_video"
    
    @patch('umcp_client.requests')
    def test_list_tools_caches_result(self, mock_requests):
        """Test list_tools caches and reuses result."""
        mock_requests.request.return_value = MockResponse({
            "tools": [{"name": "tool1", "description": "Test"}]
        })
        
        client = UMCPClient(url="http://test:8026")
        tools1 = client.list_tools()
        tools2 = client.list_tools()
        
        # Should only call once due to caching
        assert mock_requests.request.call_count == 1
        assert tools1 == tools2
    
    @patch('umcp_client.requests')
    def test_call_tool_formats_request(self, mock_requests):
        """Test call_tool formats request correctly."""
        mock_requests.request.return_value = MockResponse({
            "result": {"video_id": "vid123"}
        })
        
        client = UMCPClient(url="http://test:8026")
        result = client.call_tool("tavus.create_video", {
            "script": "Hello",
            "replica_id": "abc"
        })
        
        assert result["result"]["video_id"] == "vid123"
        
        # Verify request
        call_args = mock_requests.request.call_args
        assert call_args[0][0] == "POST"
        assert "/tools/call" in call_args[0][1]
        
        payload = call_args[1]["json"]
        assert payload["name"] == "tavus.create_video"
        assert payload["arguments"]["script"] == "Hello"
    
    @patch('umcp_client.requests')
    def test_get_tool_found(self, mock_requests):
        """Test get_tool returns tool when found."""
        mock_requests.request.return_value = MockResponse({
            "tools": [
                {"name": "tavus.create_video", "description": "Create video"}
            ]
        })
        
        client = UMCPClient(url="http://test:8026")
        tool = client.get_tool("tavus.create_video")
        
        assert tool is not None
        assert tool["name"] == "tavus.create_video"
    
    @patch('umcp_client.requests')
    def test_get_tool_not_found(self, mock_requests):
        """Test get_tool returns None when not found."""
        mock_requests.request.return_value = MockResponse({"tools": []})
        
        client = UMCPClient(url="http://test:8026")
        tool = client.get_tool("nonexistent.tool")
        
        assert tool is None
    
    @patch('umcp_client.requests')
    def test_get_tool_count(self, mock_requests):
        """Test get_tool_count returns correct count."""
        mock_requests.request.return_value = MockResponse({
            "tools": [
                {"name": "tool1"},
                {"name": "tool2"},
                {"name": "tool3"}
            ]
        })
        
        client = UMCPClient(url="http://test:8026")
        assert client.get_tool_count() == 3
    
    @patch('umcp_client.requests')
    def test_get_namespaces(self, mock_requests):
        """Test get_namespaces extracts unique namespaces."""
        mock_requests.request.return_value = MockResponse({
            "tools": [
                {"name": "tavus.create_video"},
                {"name": "tavus.get_status"},
                {"name": "elevenlabs.tts"},
                {"name": "salesforce.create_lead"}
            ]
        })
        
        client = UMCPClient(url="http://test:8026")
        namespaces = client.get_namespaces()
        
        assert namespaces == ["elevenlabs", "salesforce", "tavus"]
    
    def test_get_umcp_status_not_configured(self):
        """Test get_umcp_status when not configured."""
        with patch.dict('os.environ', {}, clear=True):
            status = get_umcp_status()
            assert status["connected"] == False
            assert status["reason"] == "not_configured"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
