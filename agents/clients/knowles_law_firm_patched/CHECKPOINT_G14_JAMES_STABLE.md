# CHECKPOINT: G14_JAMES_STABLE

**Date**: 2026-01-22
**Status**: STABLE (Legacy Migrated)
**Identity**: "James" (Senior Intake Specialist)

## State Manifest
This agent has been fully migrated to Factory SOPs G13 and G14.

### 1. Compliance (G13.1)
- [x] Guardrail Layer (`kb/guardrails/`) active.
- [x] Mandatory Disclaimers present in `compliance_disclaimers.txt`.
- [x] Surgical insertions in `intake_playbook.txt` verified.

### 2. Packaging (G13.2)
- [x] `kb_manifest.json` uses namespaced tags (`priority:critical`, `kb:guardrail`).
- [x] `tavus_pack.md` reflects strict upload order.

### 3. Identity (G14.0)
- [x] `persona_profile.json` is the Single Source of Truth.
- [x] `persona_context.txt` includes `## Visual Persona`.
- [x] `system_prompt.txt` uses `{{agent_name}}` templates.

## Build Studio Alignment
This agent is a **LEGACY BUILD**.
-   It was **NOT** created via `/build` or `generate_sku_build.py`.
-   It has been manually migrated to match the output of those tools.
-   **Future Changes**: Should align with `client_profile.json` and `persona_profile.json`.

## Rollback Instructions
If this state is corrupted:
1.  **Stop**: Do not attempt partial fixes.
2.  **Restore**: Revert the `agents/clients/knowles_law_firm/` directory to the commit tagged `CHECKPOINT_G14_JAMES_STABLE`.
3.  **Verify**: Run `python tools/verify_g140.py`.
