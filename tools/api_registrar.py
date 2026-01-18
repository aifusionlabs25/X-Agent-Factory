"""
API Registrar
Registers OpenAPI specs from registry.yaml into UMCP Tool Bus.

Security:
- Allowlist-only: Only APIs in registry.yaml can be registered
- Pin versions: Local specs preferred, remote specs are snapshotted
- NEVER logs secrets: Only env var names, not values
- Sanitizes parameter names to prevent crashes

Usage:
    python tools/api_registrar.py --all          # Register all enabled APIs
    python tools/api_registrar.py --name tavus   # Register specific API
    python tools/api_registrar.py --list         # List registry status
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

try:
    import yaml
except ImportError:
    yaml = None

try:
    import requests
except ImportError:
    requests = None


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / "apis" / "registry.yaml"
SPECS_DIR = PROJECT_ROOT / "apis" / "specs"

# Dangerous patterns to reject
DANGEROUS_PATTERNS = [
    r"\x00",  # Null bytes
    r"__proto__",  # Prototype pollution
    r"constructor",  # Constructor injection
]


def load_registry() -> Dict[str, Any]:
    """Load API registry from YAML file."""
    if yaml is None:
        print("❌ PyYAML not installed. Run: pip install pyyaml")
        return {"apis": [], "security": {}}
    
    if not REGISTRY_PATH.exists():
        print(f"❌ Registry not found: {REGISTRY_PATH}")
        return {"apis": [], "security": {}}
    
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def compute_hash(content: str) -> str:
    """Compute SHA256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def sanitize_name(name: str) -> str:
    """
    Sanitize a parameter/operation name to a safe identifier.
    
    Security: Prevents crashes from weird OpenAPI parameter names.
    """
    # Replace non-alphanumeric with underscore
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    # Remove leading digits
    safe = re.sub(r'^[0-9]+', '', safe)
    
    # Collapse multiple underscores
    safe = re.sub(r'_+', '_', safe)
    
    # Strip leading/trailing underscores
    safe = safe.strip('_')
    
    # Ensure not empty
    return safe or "param"


def check_dangerous_patterns(content: str) -> List[str]:
    """Check content for dangerous patterns."""
    warnings = []
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            warnings.append(f"Dangerous pattern found: {pattern}")
    return warnings


def fetch_remote_spec(url: str) -> Optional[str]:
    """Fetch OpenAPI spec from remote URL."""
    if requests is None:
        print(f"   ⚠️ requests not installed, cannot fetch {url}")
        return None
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"   ⚠️ Failed to fetch {url}: {e}")
        return None


def load_spec(api_entry: Dict[str, Any], security: Dict[str, Any]) -> Tuple[Optional[Dict], str, str]:
    """
    Load OpenAPI spec from local or remote source.
    
    Returns:
        (spec_dict, source_type, spec_hash)
    """
    name = api_entry['name']
    local_path = api_entry.get('local')
    remote_url = api_entry.get('openapi')
    
    spec_content = None
    source_type = "unknown"
    
    # Try local first (preferred for reproducibility)
    if local_path:
        local_file = PROJECT_ROOT / local_path
        if local_file.exists():
            with open(local_file, 'r', encoding='utf-8') as f:
                spec_content = f.read()
            source_type = "local"
    
    # Fetch remote if no local (and allowed)
    if spec_content is None and remote_url:
        if security.get('require_local_spec', False):
            print(f"   ⚠️ Remote specs disabled by security policy")
            return None, "blocked", ""
        
        spec_content = fetch_remote_spec(remote_url)
        if spec_content:
            source_type = "remote"
            
            # Pin to local for reproducibility
            pin_path = SPECS_DIR / f"{name}.yaml"
            with open(pin_path, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            print(f"   📌 Pinned to {pin_path}")
    
    if spec_content is None:
        return None, "not_found", ""
    
    # Check for dangerous patterns
    warnings = check_dangerous_patterns(spec_content)
    if warnings:
        print(f"   ⚠️ Security warnings: {warnings}")
        if security.get('sanitize_params', True):
            print(f"   🛡️ Proceeding with sanitization enabled")
        else:
            return None, "rejected", ""
    
    # Parse spec
    spec_hash = compute_hash(spec_content)
    
    try:
        if spec_content.strip().startswith('{'):
            spec = json.loads(spec_content)
        else:
            if yaml is None:
                print(f"   ❌ PyYAML required to parse YAML spec")
                return None, "parse_error", ""
            spec = yaml.safe_load(spec_content)
    except Exception as e:
        print(f"   ❌ Failed to parse spec: {e}")
        return None, "parse_error", ""
    
    return spec, source_type, spec_hash


def extract_tools_from_spec(
    spec: Dict[str, Any],
    api_entry: Dict[str, Any],
    security: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract tool definitions from OpenAPI spec.
    
    Applies:
    - Tool prefix
    - Operation allowlist
    - Parameter sanitization
    """
    tools = []
    prefix = api_entry.get('tool_prefix', api_entry['name'])
    allow_ops = api_entry.get('allow_ops', [])
    sanitize = security.get('sanitize_params', True)
    
    paths = spec.get('paths', {})
    
    for path, methods in paths.items():
        # Check allowlist
        if allow_ops:
            if not any(path.startswith(op) for op in allow_ops):
                continue
        
        for method, operation in methods.items():
            if method not in ['get', 'post', 'put', 'patch', 'delete']:
                continue
            
            op_id = operation.get('operationId', f"{method}_{path}")
            if sanitize:
                op_id = sanitize_name(op_id)
            
            tool_name = f"{prefix}.{op_id}"
            
            # Extract parameters
            params = []
            for param in operation.get('parameters', []):
                param_name = param.get('name', 'param')
                if sanitize:
                    param_name = sanitize_name(param_name)
                params.append({
                    "name": param_name,
                    "type": param.get('schema', {}).get('type', 'string'),
                    "required": param.get('required', False)
                })
            
            tools.append({
                "name": tool_name,
                "description": operation.get('summary', operation.get('description', '')),
                "path": path,
                "method": method.upper(),
                "parameters": params
            })
    
    return tools


def register_api(api_entry: Dict[str, Any], security: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register a single API from registry.
    
    Returns:
        Result dict with status, tools, hash
    """
    name = api_entry['name']
    
    print(f"\n📦 Registering: {name}")
    print(f"   Description: {api_entry.get('description', 'N/A')}")
    
    # Load spec
    spec, source_type, spec_hash = load_spec(api_entry, security)
    
    if spec is None:
        return {
            "name": name,
            "status": "failed",
            "reason": source_type,
            "tools": 0
        }
    
    print(f"   Source: {source_type}")
    print(f"   Hash: {spec_hash}")
    
    # Extract tools
    tools = extract_tools_from_spec(spec, api_entry, security)
    print(f"   Tools: {len(tools)}")
    
    # Register with UMCP (if available)
    try:
        from umcp_client import UMCPClient
        
        client = UMCPClient()
        if client.enabled and client.ping():
            result = client.call_tool("register_api", {
                "name": name,
                "tools": tools,
                "spec_hash": spec_hash,
                "auth_env": api_entry.get('auth_env', ''),
                "auth_header": api_entry.get('auth_header', '')
            })
            print(f"   ✅ Registered with UMCP")
        else:
            print(f"   ⚠️ UMCP not available, tools extracted but not registered")
    except ImportError:
        print(f"   ⚠️ UMCP client not available")
    except Exception as e:
        print(f"   ⚠️ UMCP registration failed: {e}")
    
    # Send Agent Mail notification
    try:
        from agent_mail_client import AgentMailClient
        
        mail = AgentMailClient()
        if mail.enabled:
            mail.send_message(
                to="factory_coordinator",
                subject=f"API Registered: {name}",
                body=f"""API {name} registered successfully.

Tools: {len(tools)}
Spec Hash: {spec_hash}
Source: {source_type}
""",
                tags=["api", "registration", name]
            )
    except:
        pass
    
    return {
        "name": name,
        "status": "registered",
        "tools": len(tools),
        "hash": spec_hash,
        "source": source_type
    }


def register_all_apis() -> List[Dict[str, Any]]:
    """Register all enabled APIs from registry."""
    print(f"\n{'='*60}")
    print(f"🔌 API REGISTRAR")
    print(f"   Registry: {REGISTRY_PATH}")
    print(f"{'='*60}")
    
    registry = load_registry()
    security = registry.get('security', {})
    apis = registry.get('apis', [])
    
    results = []
    
    for api_entry in apis:
        if not api_entry.get('enabled', False):
            print(f"\n⏭️ Skipping: {api_entry['name']} (disabled)")
            continue
        
        result = register_api(api_entry, security)
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 REGISTRATION SUMMARY")
    registered = sum(1 for r in results if r['status'] == 'registered')
    total_tools = sum(r.get('tools', 0) for r in results)
    print(f"   APIs: {registered}/{len(results)}")
    print(f"   Tools: {total_tools}")
    print(f"{'='*60}\n")
    
    return results


def register_single_api(name: str) -> Optional[Dict[str, Any]]:
    """Register a single API by name."""
    registry = load_registry()
    security = registry.get('security', {})
    
    for api_entry in registry.get('apis', []):
        if api_entry['name'] == name:
            if not security.get('allowlist_only', True):
                return register_api(api_entry, security)
            elif api_entry.get('enabled', False):
                return register_api(api_entry, security)
            else:
                print(f"❌ API '{name}' is in registry but disabled")
                return None
    
    print(f"❌ API '{name}' not found in registry (allowlist-only)")
    return None


def list_registry():
    """List all APIs in registry with status."""
    print(f"\n{'='*60}")
    print(f"📋 API REGISTRY STATUS")
    print(f"{'='*60}\n")
    
    registry = load_registry()
    
    for api_entry in registry.get('apis', []):
        name = api_entry['name']
        enabled = api_entry.get('enabled', False)
        status = "✅ Enabled" if enabled else "⏸️ Disabled"
        
        local = api_entry.get('local', '')
        local_exists = (PROJECT_ROOT / local).exists() if local else False
        
        print(f"  {name}")
        print(f"    Status: {status}")
        print(f"    Prefix: {api_entry.get('tool_prefix', name)}")
        print(f"    Auth: {api_entry.get('auth_env', 'None')} (NEVER logged)")
        print(f"    Local: {local} {'✅' if local_exists else '❌'}")
        print()


def main():
    parser = argparse.ArgumentParser(description="API Registrar - OpenAPI to UMCP")
    parser.add_argument("--all", action="store_true", help="Register all enabled APIs")
    parser.add_argument("--name", metavar="NAME", help="Register specific API by name")
    parser.add_argument("--list", action="store_true", dest="list_registry", help="List registry status")
    
    args = parser.parse_args()
    
    if args.list_registry:
        list_registry()
    elif args.name:
        result = register_single_api(args.name)
        sys.exit(0 if result else 1)
    else:
        # Default to --all
        results = register_all_apis()
        failed = sum(1 for r in results if r['status'] != 'registered')
        sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
