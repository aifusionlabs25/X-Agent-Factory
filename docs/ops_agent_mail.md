# MCP Agent Mail - Operations Guide

**MCP Agent Mail** provides agent coordination via message passing, searchable history, and advisory file leases.

## Installation

```bash
# Via pip
pip install mcp-agent-mail

# Or run the Docker container
docker run -d --name agent-mail -p 8025:8025 ghcr.io/dicklesworthstone/mcp-agent-mail
```

## Starting the Server

```bash
# Using Make targets
make agent-mail-up   # Start server
make agent-mail-down # Stop server
make agent-mail-ping # Health check

# Or directly
uvicorn mcp_agent_mail:app --port 8025
```

## Configuration

Set the server URL via environment variable:

```bash
export AGENT_MAIL_URL=http://localhost:8025

# Or in .env
AGENT_MAIL_URL=http://localhost:8025
```

## Client Usage

```python
from tools.agent_mail_client import AgentMailClient

client = AgentMailClient()

# Send a message
client.send_message(
    to="nova",
    subject="Build Complete",
    body="Built nexgen_hvac agent",
    tags=["build", "nexgen_hvac"]
)

# Search messages
results = client.search("nexgen_hvac")

# Lease files (advisory)
lease_id = client.lease(["agents/nexgen_hvac/**"], ttl=300)
# ... do work ...
client.release_lease(lease_id)
```

## Integration with Factory

When `AGENT_MAIL_URL` is set or `--notify-agent-mail` flag is used:

1. **Intake Complete**: Posts URL, industry, dossier path
2. **Build Complete**: Posts client_slug, artifacts, manifest hash
3. **Failures**: Posts validation errors, run_id

If not configured, notifications are silently skipped (baseline unchanged).

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/messages` | POST | Send message |
| `/messages/search` | GET | Search messages |
| `/threads` | GET | List threads |
| `/leases` | POST | Create file lease |
| `/leases/{id}` | DELETE | Release lease |

## Troubleshooting

**Server not responding:**
```bash
make agent-mail-ping  # Check health
docker logs agent-mail  # View logs
```

**Messages not appearing:**
- Check `AGENT_MAIL_URL` is set correctly
- Verify server is running on expected port
