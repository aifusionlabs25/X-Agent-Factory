# The X Agent Factory: "On-Demand Customization" Workflow

## Philosophy
We do NOT build custom agents from scratch for every client.
We build **"Base Models" (X Agents)** that sit on the shelf.
When a client buys, we **"Inject"** their specific context using the Troy Protocol.

## The Workflow

### 1. The "Shelf" (R&D Phase)
*This happens BEFORE the client signs up.*
1.  **WebWorker Scan**: Identifies a high-value vertical (e.g., Veterinary).
2.  **Factory Build**: Generates the "Base Agent" (Ava).
    -   `template.json`: Defines the generic triage/scheduling logic.
    -   **Artifact**: `agents/ava_veterinary/base_logic.txt` (The Standard Skeleton).
3.  **Status**: Ava sits on the shelf, ready to triage generic pets.

### 2. The "Hand-Off" (Sales Phase)
*Client ("Dr. Smith's Vet Clinic") signs up.*
1.  **Input**: You provide:
    -   `Client Name`: "Dr. Smith's Clinic"
    -   `Replica ID`: `r7923...` (The Tavus Video Avatar of Dr. Smith or his receptionist).
    -   `Specific Nuance`: "We are closed on Wednesdays and hate using the word 'emergency'."

### 3. The "Injection" (Troy Protocol)
*Troy activates to customize the Base Model.*
1.  **Ingest**: Takes `base_logic.txt` + `Client Nuance`.
2.  **Forge Skeleton**: Modifies the logic (e.g., adds "Closed Wednesdays" rule).
    -   Output: `custom_system_prompt.txt`
3.  **Forge Soul**: Creates the persona context.
    -   Input: "Dr. Smith's Clinic" brand voice.
    -   Output: `custom_persona_context.txt` (e.g., "You are Sarah, the welcoming face of Dr. Smith's...").

### 4. The "Deployment" (Tavus API)
*The artifacts are pushed to the Tavus Replica.*
1.  **API Call**: `POST /v2/replicas/{replica_id}/context`
    -   `system_prompt`: `custom_system_prompt.txt`
    -   `context`: `custom_persona_context.txt`
2.  **Result**: The Replica `r7923` is now "Sarah", following the factory-standard triage logic, but speaking with Dr. Smith's voice and knowing his specific hours.

## Why This Wins
-   **Speed**: You don't debug logic for every client. The "Base Logic" is proven.
-   **Quality**: Troy ensures the "Soul" matches the "Skeleton" perfectly every time.
-   **Scale**: You can deploy 100 clones of Ava in 10 minutes, each with a different name/voice, but the same reliable brain.
