import os
import sys
import argparse

def apply_sop_a17(client_slug):
    print(f"--- Applying SOP-A17 (Behavioral Enrichment) to {client_slug} ---")
    
    base_dir = f"agents/clients/{client_slug}"
    prompt_path = os.path.join(base_dir, "system_prompt.txt")
    context_path = os.path.join(base_dir, "persona_context.txt")
    
    if not os.path.exists(prompt_path):
        print("  [FAIL] system_prompt.txt not found.")
        sys.exit(1)

    # 1. System Prompt Injection
    # We want to insert this before "## Firm Specifics" or similar logic sections
    
    behavioral_block = """
## SOP-A17: Conversation Physics & Style
- **Spoken Constraints**: NO markdown (bold/italic). NO numbered lists (use "First, Second"). Keep sentences under 15 words where possible.
- **Latency**: If you need >2s to think, say "Let me check that..." immediately.
- **Interruption**: If interrupted, STOP immediately. When resuming, say "As I was saying..." or "Coming back to that..."
- **Floor Holding**: Use connectors ("Now," "So," "Essentially") to keep the flow.

## SOP-A17: Stress Handling & De-escalation
- **Validation First**: Before enforcing a boundary, validate the emotion. "I hear how urgent this is."
- **Grounding**: If caller spirals, bring them back to the specific question. "Right now, I just need your name."
- **De-escalation**: Lower your volume/intensity if they raise theirs. (Voice Intent Rule).
"""
    
    with open(prompt_path, 'r') as f:
        content = f.read()
        
    if "SOP-A17" in content:
        print("  [SKIP] System Prompt already enriched.")
    else:
        # Simple append logic for now, or surgical insert if we find a good anchor
        # Inserting after strict disclaimers or identity is usually safe.
        # Let's insert after the header/imports.
        
        parts = content.split("## Firm Specifics")
        if len(parts) > 1:
            new_content = parts[0] + behavioral_block + "\n## Firm Specifics" + parts[1]
        else:
            new_content = content + "\n" + behavioral_block
            
        with open(prompt_path, 'w') as f:
            f.write(new_content)
        print("  [OK] Injected SOP-A17 into System Prompt.")

    # 2. Context Injection
    physics_context = """
## Behavioral Physics (SOP-A17)
-   **Pacing**: You are NOT a robot. You breathe. You pause.
-   **Tone Shifts**:
    -   *Intake*: Professional, efficient.
    -   *Stress*: Slower, warmer, lower pitch.
    -   *Objection*: Firm but polite.
"""
    with open(context_path, 'r') as f:
        content = f.read()

    if "Behavioral Physics" in content:
        print("  [SKIP] Context already enriched.")
    else:
        with open(context_path, 'a') as f:
            f.write("\n" + physics_context)
        print("  [OK] Appended SOP-A17 to Persona Context.")

    print("\nSUCCESS: SOP-A17 Applied.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True)
    args = parser.parse_args()
    apply_sop_a17(args.client)
