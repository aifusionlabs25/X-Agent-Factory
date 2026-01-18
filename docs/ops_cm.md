# CM Memory System - Operations Guide

**CM** (cass_memory_system) generates durable memory packs from Factory runs.

## Installation

```bash
# Homebrew (recommended)
brew install dicklesworthstone/tap/cm

# Verify installation
cm --version
```

## Project Configuration

Memory system is configured via `.cmconfig.yaml`:

```yaml
sources:
  runs: ./runs
output:
  memory_dir: ./memory
```

## Directory Structure

```
memory/
├── global/
│   ├── factory_playbook.md   # Factory-wide statistics
│   └── gotchas.md            # Common errors
└── clients/
    └── <client_slug>/
        ├── memory_pack.md    # Client run history
        └── build_notes.md    # Build configuration
```

## Usage

### Build All Memory Packs

```bash
make cm-build
# or
python tools/memory_builder.py --all
```

### Build Single Client Pack

```bash
make cm-client slug=nexgen_hvac
# or
python tools/memory_builder.py --client nexgen_hvac
```

### Search Memory (via CASS)

```bash
make cass-search q="nexgen_hvac"
```

## Memory Pack Contents

### `factory_playbook.md` (Global)
- Total run count
- Success/failure rates
- Tools usage breakdown
- Active clients list

### `memory_pack.md` (Per-Client)
- Last run timestamp
- Run history table
- Output artifacts
- Recent errors

### `build_notes.md` (Per-Client)
- Build arguments
- Configuration used

## Integration

Memory packs are advisory side artifacts. They don't modify the build pipeline.

Future phases may inject `memory_pack.md` into agent artifacts.
