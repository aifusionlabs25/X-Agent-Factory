# UMCP Tool Bus - Operations Guide

**UMCP** (Ultimate MCP Server) provides a unified tool bus for external integrations (Tavus, Salesforce, etc.).

## Installation

```bash
# Via pip
pip install ultimate-mcp-server

# Or Docker
docker run -d --name umcp -p 8026:8026 ghcr.io/dicklesworthstone/ultimate-mcp-server
```

## Starting the Server

```bash
# Using Make targets
make umcp-up   # Start server
make umcp-down # Stop server
make umcp-ping # Health check
```

## Configuration

Set the server URL via environment variable:

```bash
export UMCP_URL=http://localhost:8026

# Or in .env
UMCP_URL=http://localhost:8026
```

## Client Usage

```python
from tools.umcp_client import UMCPClient

client = UMCPClient()

# Check health
if client.ping():
    print("UMCP connected!")

# List available tools
tools = client.list_tools()
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")

# Call a tool
result = client.call_tool("tavus.create_video", {
    "script": "Hello world",
    "replica_id": "abc123"
})
```

## Available Tool Namespaces

| Namespace | Description |
|-----------|-------------|
| `tavus.*` | Tavus video API |
| `elevenlabs.*` | ElevenLabs voice API |
| `salesforce.*` | Salesforce CRM |
| `email.*` | Email sending |

## Integration with Factory

When `UMCP_URL` is set:
- Run logger records "UMCP connected" + tool count
- Optional Agent Mail notification posted

If not configured: Silent no-op (baseline unchanged).

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `UMCP_URL` | UMCP server URL | None (disabled) |
| `UMCP_TIMEOUT` | Request timeout (seconds) | 30 |

## Troubleshooting

**Server not responding:**
```bash
make umcp-ping  # Check health
docker logs umcp  # View logs
```

**Tool not found:**
```bash
# List available tools
python -c "from tools.umcp_client import UMCPClient; print(UMCPClient().list_tools())"
```
