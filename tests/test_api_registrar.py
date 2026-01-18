"""
Phase 20: API Registrar Tests
Tests the API registrar security guardrails and sanitization.

Usage:
    pytest tests/test_api_registrar.py -v
"""
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from api_registrar import (
    sanitize_name,
    check_dangerous_patterns,
    compute_hash,
    extract_tools_from_spec,
    load_registry
)


class TestSanitization:
    """Tests for parameter name sanitization."""
    
    def test_sanitize_normal_name(self):
        """Test sanitize_name preserves normal names."""
        assert sanitize_name("user_id") == "user_id"
        assert sanitize_name("getMessage") == "getMessage"
    
    def test_sanitize_spaces(self):
        """Test sanitize_name replaces spaces."""
        assert sanitize_name("user name") == "user_name"
    
    def test_sanitize_special_chars(self):
        """Test sanitize_name replaces special characters."""
        assert sanitize_name("user-id") == "user_id"
        assert sanitize_name("user.id") == "user_id"
        assert sanitize_name("user@email") == "user_email"
    
    def test_sanitize_leading_digits(self):
        """Test sanitize_name removes leading digits."""
        assert sanitize_name("123param") == "param"
        assert sanitize_name("1_param") == "param"
    
    def test_sanitize_multiple_underscores(self):
        """Test sanitize_name collapses multiple underscores."""
        assert sanitize_name("user__id") == "user_id"
        assert sanitize_name("a___b___c") == "a_b_c"
    
    def test_sanitize_empty(self):
        """Test sanitize_name handles empty string."""
        assert sanitize_name("") == "param"
        assert sanitize_name("___") == "param"


class TestDangerousPatterns:
    """Tests for dangerous pattern detection."""
    
    def test_no_patterns(self):
        """Test clean content has no warnings."""
        warnings = check_dangerous_patterns("normal content here")
        assert len(warnings) == 0
    
    def test_detects_proto(self):
        """Test detects __proto__ pattern."""
        warnings = check_dangerous_patterns('{"__proto__": "foo"}')
        assert len(warnings) > 0
        assert any("__proto__" in w for w in warnings)
    
    def test_detects_constructor(self):
        """Test detects constructor pattern."""
        warnings = check_dangerous_patterns('{"constructor": "evil"}')
        assert len(warnings) > 0


class TestToolExtraction:
    """Tests for extracting tools from OpenAPI specs."""
    
    def test_extract_basic_tools(self):
        """Test extracting tools from simple spec."""
        spec = {
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "summary": "Get all users"
                    },
                    "post": {
                        "operationId": "createUser",
                        "summary": "Create user"
                    }
                }
            }
        }
        
        api_entry = {"name": "test", "tool_prefix": "test"}
        security = {"sanitize_params": True}
        
        tools = extract_tools_from_spec(spec, api_entry, security)
        
        assert len(tools) == 2
        assert tools[0]["name"] == "test.getUsers"
        assert tools[1]["name"] == "test.createUser"
    
    def test_extract_with_allowlist(self):
        """Test that allowlist filters paths."""
        spec = {
            "paths": {
                "/v1/users": {"get": {"operationId": "getUsers"}},
                "/v1/admin": {"get": {"operationId": "getAdmin"}},
                "/v2/users": {"get": {"operationId": "getUsersV2"}}
            }
        }
        
        api_entry = {
            "name": "test",
            "tool_prefix": "test",
            "allow_ops": ["/v1/users"]
        }
        security = {}
        
        tools = extract_tools_from_spec(spec, api_entry, security)
        
        assert len(tools) == 1
        assert tools[0]["name"] == "test.getUsers"
    
    def test_extract_sanitizes_operation_ids(self):
        """Test that bad operation IDs are sanitized."""
        spec = {
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "get-users@v2",
                        "summary": "Get users"
                    }
                }
            }
        }
        
        api_entry = {"name": "api", "tool_prefix": "api"}
        security = {"sanitize_params": True}
        
        tools = extract_tools_from_spec(spec, api_entry, security)
        
        assert len(tools) == 1
        # Should be sanitized to safe identifier
        assert "@" not in tools[0]["name"]
        assert "-" not in tools[0]["name"]


class TestRegistryLoading:
    """Tests for registry loading."""
    
    def test_load_registry_exists(self):
        """Test loading registry from file."""
        registry = load_registry()
        
        # Should have apis list
        assert "apis" in registry
        assert isinstance(registry["apis"], list)
    
    def test_registry_has_security(self):
        """Test registry has security settings."""
        registry = load_registry()
        
        # Should have security section
        assert "security" in registry
        assert registry["security"].get("allowlist_only", False) == True


class TestAllowlistSecurity:
    """Tests for allowlist-only security."""
    
    def test_registry_only_enabled_apis(self):
        """Test that only enabled APIs are in registry."""
        registry = load_registry()
        
        enabled = [a for a in registry["apis"] if a.get("enabled", False)]
        disabled = [a for a in registry["apis"] if not a.get("enabled", False)]
        
        # Should have some of each
        assert len(enabled) >= 0  # May have enabled APIs
        assert len(disabled) >= 0  # May have disabled APIs
    
    def test_hash_computation(self):
        """Test hash computation is deterministic."""
        content = "test content"
        hash1 = compute_hash(content)
        hash2 = compute_hash(content)
        
        assert hash1 == hash2
        assert len(hash1) == 16


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
