# Implementation Plan: Reasoning Modes Bolt-on

**Objective**: Add an optional "Reasoning Profile" layer to agents to standardizing reasoning stacks (e.g., "SDR Qualification", "Legal Intake") without bloating prompts.

## User Review Required
> [!NOTE]
> This is a non-disruptive "Bolt-on". Existing agents (Knowles) will remain valid without this field. It is purely additive.

## Proposed Changes

### Phase 0: Reference & Presets (Refined)
1.  **Docs**: Update `docs/reasoning/mode_selector.md` to use canonical names (`reflex`, `hermeneutic`, `adversarial`, `legal`, `compliance`) and remove hard latency numbers.
2.  **Presets**: `docs/reasoning/presets.json` (Already created, verify alignment).

### Phase 1: Schema Extension & Validation (Refined)
1.  **Artifact**: `agents/clients/<slug>/persona_profile.json` (Field `reasoning_profile`).
2.  **Validation (`verify_icc.py`)**:
    *   **Guardrail**: Only runs if `reasoning_profile` is present.
    *   **Checks**:
        *   `preset_id` matches `presets.json` OR is "custom".
        *   `mode_stack` length 1-6.
        *   `mode_stack` items in allowed set `{reflex, hermeneutic, adversarial, legal, compliance}`.
        *   Type checking (strings only).

### Phase 2: UI & Config (Deferred)
*   **Dashboard**: Add "Reasoning Preset" dropdown to the Agent Configuration page.

### Phase 3: Prompt Injection (Builder)
1.  **Builder**: Update `generate_sku_build.py`.
2.  **Logic**: If `reasoning_profile` exists and `preset_id` != None:
    *   Inject **Tiny Snippet** into `system_prompt.txt`.
    *   **Format**: Minimalist, no numbered lists (James compatibility).
    *   **Example**:
        ```text
        [Reasoning: legal_intake_v1]
        Stack: hermeneutic > legal > compliance
        Required: referral_decision
        Checks: premature_closure
        ```
    *   **Constraint**: Do NOT paste `modes_of_reasoning.md` content.

## Verification Plan
1.  **Validation Test**:
    *   Run `verify_icc.py` on Knowles (valid profile).
    *   Temporarily break Knowles profile (e.g. invalid mode) and verify script fails.
2.  **Builder Test**:
    *   Run `generate_sku_build.py` for Knowles.
    *   Inspect `system_prompt.txt` for the injected snippet.
