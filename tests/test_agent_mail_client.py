"""
Phase 18: Agent Mail Client Tests
Tests the Agent Mail client wrapper using mocked HTTP.

Usage:
    pytest tests/test_agent_mail_client.py -v
"""
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from agent_mail_client import (
    AgentMailClient,
    notify_intake_complete,
    notify_build_complete,
    notify_failure
)


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


class TestAgentMailClient:
    """Tests for Agent Mail client wrapper."""
    
    def test_client_initialization(self):
        """Test client initializes with default values."""
        client = AgentMailClient(url="http://test:8025")
        
        assert client.url == "http://test:8025"
        assert client.agent_id == "factory_orchestrator"
    
    def test_client_disabled_without_config(self):
        """Test client is disabled when not configured."""
        # Clear env to simulate unconfigured state
        with patch.dict('os.environ', {}, clear=True):
            client = AgentMailClient()
            # Without explicit URL and no env var, should be disabled
            assert client._enabled == False
    
    def test_client_enabled_with_url(self):
        """Test client is enabled when URL provided."""
        client = AgentMailClient(url="http://test:8025")
        # Should be enabled when explicit URL provided
        assert client._enabled == True
    
    @patch('agent_mail_client.requests')
    def test_send_message_formats_correctly(self, mock_requests):
        """Test send_message formats the request correctly."""
        mock_requests.request.return_value = MockResponse({"message_id": "msg123"})
        
        client = AgentMailClient(url="http://test:8025")
        result = client.send_message(
            to="nova",
            subject="Test Subject",
            body="Test Body",
            tags=["test", "unit"]
        )
        
        assert result == "msg123"
        
        # Verify request was called
        mock_requests.request.assert_called_once()
        call_args = mock_requests.request.call_args
        
        assert call_args[0][0] == "POST"  # Method
        assert "/messages" in call_args[0][1]  # Endpoint
        
        # Check payload
        payload = call_args[1]["json"]
        assert payload["to"] == "nova"
        assert payload["subject"] == "Test Subject"
        assert payload["body"] == "Test Body"
        assert payload["tags"] == ["test", "unit"]
    
    @patch('agent_mail_client.requests')
    def test_search_returns_messages(self, mock_requests):
        """Test search returns message list."""
        mock_requests.request.return_value = MockResponse({
            "messages": [
                {"id": "msg1", "subject": "Test 1"},
                {"id": "msg2", "subject": "Test 2"}
            ]
        })
        
        client = AgentMailClient(url="http://test:8025")
        results = client.search("test query")
        
        assert len(results) == 2
        assert results[0]["id"] == "msg1"
    
    @patch('agent_mail_client.requests')
    def test_lease_returns_lease_id(self, mock_requests):
        """Test lease creates and returns lease ID."""
        mock_requests.request.return_value = MockResponse({"lease_id": "lease123"})
        
        client = AgentMailClient(url="http://test:8025")
        lease_id = client.lease(["agents/**", "runs/**"], ttl=600)
        
        assert lease_id == "lease123"
        
        # Verify request
        call_args = mock_requests.request.call_args
        payload = call_args[1]["json"]
        assert payload["files"] == ["agents/**", "runs/**"]
        assert payload["ttl"] == 600
    
    @patch('agent_mail_client.requests')
    def test_release_lease_succeeds(self, mock_requests):
        """Test release_lease calls correct endpoint."""
        mock_requests.request.return_value = MockResponse({})
        
        client = AgentMailClient(url="http://test:8025")
        result = client.release_lease("lease123")
        
        assert result is True
        
        call_args = mock_requests.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "lease123" in call_args[0][1]
    
    @patch('agent_mail_client.requests')
    def test_ping_returns_true_on_healthy(self, mock_requests):
        """Test ping returns True when server is healthy."""
        mock_requests.request.return_value = MockResponse({"status": "ok"})
        
        client = AgentMailClient(url="http://test:8025")
        assert client.ping() is True
    
    @patch('agent_mail_client.requests')
    def test_ping_returns_false_on_error(self, mock_requests):
        """Test ping returns False when server errors."""
        mock_requests.request.side_effect = Exception("Connection refused")
        
        client = AgentMailClient(url="http://test:8025")
        assert client.ping() is False
    
    def test_convenience_functions_handle_disabled_client(self):
        """Test convenience functions gracefully handle disabled client."""
        # Should not raise even when not configured
        with patch.dict('os.environ', {}, clear=True):
            notify_intake_complete("http://example.com", "HVAC", "/path", "test")
            notify_build_complete("test", ["file1"], "hash123")
            notify_failure("run123", "error", "tool")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
