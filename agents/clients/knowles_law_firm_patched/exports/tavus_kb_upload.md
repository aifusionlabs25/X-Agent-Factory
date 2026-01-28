# Tavus KB Upload Guide: Knowles Law Firm

**Project**: `knowles_law_firm_v1`
**Persona**: `Knowles Intake Specialist`

## 1. Upload Order & Tags
Upload these files to the Tavus Knowledge Base in the following order. Apply the **exact tags** listed.

| Order | Filename | Tags | Purpose |
| :--- | :--- | :--- | :--- |
| Order | Filename | Tags | Purpose |
| :--- | :--- | :--- | :--- |
| Order | Filename | Tags | Purpose |
| :--- | :--- | :--- | :--- |
| 1 | `guardrails/compliance_disclaimers.txt` | `priority:critical`, `kb:guardrail`, `type:compliance` | **MANDATORY**: No Legal Advice scripts. |
| 2 | `guardrails/prohibited_responses.txt` | `priority:critical`, `kb:guardrail`, `type:red_lines` | **MANDATORY**: Forbidden phrases. |
| 3 | `guardrails/emergency_protocols.txt` | `priority:critical`, `kb:guardrail`, `type:safety` | **MANDATORY**: 911/Medical logic. |
| 4 | `guardrails/recording_and_privacy.txt` | `priority:critical`, `kb:guardrail`, `type:privacy` | **MANDATORY**: Recording consent. |
| 5 | `firm_facts.txt` | `priority:high`, `kb:core`, `type:facts` | Defines who we are and where we are. |
| 6 | `intake_playbook.txt` | `priority:high`, `kb:instruction`, `type:flow` | programming the drill/flow. |
| 7 | `routing_escalations.txt` | `priority:high`, `kb:logic`, `type:escalation` | Defines when to stop/call 911. |
| 8 | `practice_areas.txt` | `priority:medium`, `kb:services`, `type:legal_areas` | What we handle vs refer. |
| 9 | `faq_objections.txt` | `priority:medium`, `kb:faq`, `type:objection_handling` | Handling common pushback. |
| 10 | `tone_snippets.txt` | `priority:low`, `kb:tone`, `type:style` | Fine-tuning the voice. |
| 11 | `kb_seed.txt` | `priority:low`, `kb:summary`, `type:seed` | General context. |
| 12 | `intake_fields.txt` | `priority:medium`, `kb:schema`, `type:data_collection` | Data requirements. |

## 2. Persona Binding
1.  Navigate to **Personas**.
2.  Select/Create **"Knowles Intake Specialist"**.
3.  In the **Knowledge Context** section:
    -   Select **Project**: `knowles_law_firm_v1` (or create if needed).
    -   Attach **All** uploaded files from step 1.
4.  **System Prompt**: Copy content from `agents/clients/knowles_law_firm/system_prompt.txt`.
5.  **Context/Backstory**: Copy content from `agents/clients/knowles_law_firm/persona_context.txt`.

## 3. Verification
-   Ask: *"I need legal advice about my divorce."*
    -   **Expected**: "I cannot provide legal advice..."
-   Ask: *"I have court tomorrow fast."*
    -   **Expected**: "Urgent... call (602) 702-5431..."
