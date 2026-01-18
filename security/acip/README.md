# ACIP (Agentic Coding Instruction Protocol) - Vendored

**Version:** 1.0
**Source:** https://github.com/anthropics/acip
**Vendored:** 2026-01-18

## Purpose

This folder contains vendored ACIP security guidelines for prompt-injection hardening.
These are prepended to agent system prompts when `--acip` flag is enabled.

## Usage

```bash
# Build agent with ACIP hardening
python tools/factory_orchestrator.py --build-agent dossier.json --acip
```

This produces:
- `system_prompt.txt` - Standard prompt (unchanged)
- `system_prompt_with_acip.txt` - Prompt with ACIP prefix

## Files

- `README.md` - This file
- `ACIP_v1_full.md` - Full ACIP specification (vendored)

## Upstream

For the latest ACIP specification, see the upstream repository.
