# CASS Session Indexing - Operations Guide

**CASS** (Context-Aware Semantic Search) enables searchable, auditable Factory runs.

## Installation

```bash
# Homebrew (recommended)
brew install dicklesworthstone/tap/cass

# Or pip
pip install cass-cli
```

## Run Logging

Every Factory run (intake + build-agent) automatically creates:

```
runs/
└── 2026-01-18/
    └── abc123def456/
        ├── run_metadata.json   # Structured metadata
        ├── run_stdout.log      # Console output
        ├── run_stderr.log      # Errors
        └── run_summary.md      # Human-readable summary
```

### Metadata Schema

```json
{
  "run_id": "abc123def456",
  "tool": "intake_packager",
  "timestamp": "2026-01-18T12:00:00Z",
  "duration_seconds": 5.2,
  "success": true,
  "args": {"url": "https://example.com"},
  "outputs": {"client_slug": "example_co", "dossier_path": "..."}
}
```

## Indexing

```bash
# Index all runs
make cass-index

# Or directly
cass index runs/ --output .cass_index
```

## Searching

```bash
# Search by client slug
make cass-search q="nexgen_hvac"

# Search by URL domain
make cass-search q="acmesolar.com"

# Search for failures
make cass-search q="schema validation failed"

# Or directly
cass search "your query" --index .cass_index
```

## Example Queries

| Query | Finds |
|-------|-------|
| `nexgen` | Runs for NexGen client |
| `solar` | Solar industry runs |
| `validation failed` | Failed schema validations |
| `2026-01-18` | Runs from specific date |

## Disable Logging

Pass `--no-log` to skip run logging:

```bash
python tools/intake_packager.py --url https://example.com --no-log
python tools/factory_orchestrator.py --build-agent dossier.json --no-log
```
