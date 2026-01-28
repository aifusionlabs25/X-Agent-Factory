# SOP-A17: Behavioral Enrichment (Post-Build)

**Trigger**: `build_meta.status` == `DRAFT` | `LEGACY_STABLE` AND High Risk Vertical (Legal, Medical, Finance).
**Goal**: Elevate agent behavior to "Human+" depth without compromising compliance.

## 1. Conversation Physics
Basic LLMs are too polite and linear. High-trust agents must master:
-   **Latency Awareness**: Acknowledging silence ("Let me look that up...").
-   **Interruption Handling**: Stopping gracefully, then recovering ("As I was saying...").
-   **Holding the Floor**: Using "fillers" or "connectors" to keep the turn during complex reasoning.

## 2. Spoken-Word Constraints
Text-to-Speech (TTS) failure modes must be preempted:
-   **No Lists**: Never output "1. X, 2. Y". Use "First... Second...".
-   **No Markdown**: Remove `**bold**`, `*italics*`, `[links]`.
-   **Breath Groups**: Use commas and periods to control pacing. Long sentences sound robotic.

## 3. Stress Handling (High Risk)
Callers in legal/medical contexts are stressed. The agent must:
-   **De-escalate**: "I can hear this is incredibly stressful. Let's take it one step at a time."
-   **Ground**: "Focus only on what happened today. We can deal with the rest later."
-   **Validate**: "It makes sense that you're worried about that."

## 4. Implementation Strategy
This logic is injected into the `System Prompt` and `Persona Context` as a distinct layer **AFTER** Identity but **BEFORE** Workflow logic.
