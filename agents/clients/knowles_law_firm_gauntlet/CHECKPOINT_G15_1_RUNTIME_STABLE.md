# CHECKPOINT: G15.1 RUNTIME STABLE
**Status**: 🟢 STABLE / VERIFIED
**Date**: 2026-01-23
**SKU**: Attorney Intake -> Knowles Law Firm ("James")

## 1. Factory Architecture Status
The X Agent Factory has transitioned from prompt engineering to a gated manufacturing system.
- **Base SKU**: `attorney_intake`
- **Overlay**: `knowles_law_firm`
- **Binding**: Runtime inputs separated from Content artifacts.

## 2. Artifact Manifest (Single Source of Truth)
All artifacts are present and verified:
- [x] `persona_profile.json`: Identity Truth (James / Male / Senior Intake).
- [x] `runtime_profile.json`: Provider Binding + Secrets Refs.
- [x] `system_prompt.txt`: Templated (`{{agent_name}}` resolved).
- [x] `kb_manifest.json`: Tagged for Tavus ingestion.
- [x] `kb/guardrails/*`: Integrated compliance layer.

## 3. Deployment Gates (Enforced)
Deployments are blocked unless `tools/verify_release_ready.py` PASSES:
1.  **ICC (Identity Consistency)**:
    - No unresolved templates.
    - Name/Role consistency across all files.
2.  **Compliance (G13)**:
    - Guardrails present.
    - Manifest tags valid (`client:knowles_law_firm`).
3.  **Runtime (G15.1)**:
    - Per-Agent Secrets (Namespaced).
    - Voice Presets configured.
    - Required fields present (Persona ID, Replica ID).

## 4. Runtime Configuration
- **Visual Interface**: `/agents/knowles_law_firm/runtime`
- **Secrets Storage**: `dashboard/.env.local`
- **Current State**:
    - Tavus: Enabled (Key: `TAVUS_API_KEY__KNOWLES_LAW_FIRM`)
    - TTS: Disabled (Ready for Cartesia/ElevenLabs)

## 5. Next Steps
- Clone Attorney SKU to second firm to prove scalability.
- Begin landing page wiring using `runtime_profile.json`.
