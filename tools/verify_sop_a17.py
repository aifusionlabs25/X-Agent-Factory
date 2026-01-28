import os
import sys
import argparse

def verify_sop_a17_spine(client_slug):
    print(f"--- Verifying SOP-A17 (Conversational Spine) for {client_slug} ---")
    
    base_dir = f"agents/clients/{client_slug}"
    prompt_path = os.path.join(base_dir, "system_prompt.txt")
    context_path = os.path.join(base_dir, "persona_context.txt")
    
    failures = []

    # 1. System Prompt Checks (Spine Import)
    if not os.path.exists(prompt_path):
        failures.append("system_prompt.txt missing")
    else:
        with open(prompt_path, 'r') as f:
            prompt_content = f.read()
            
        # We now look for the IMPORT or the Raw Text (Legacy support)
        has_import = "agents/_shared/conversational_spines/intake_triage_legal.md" in prompt_content
        has_raw_sop = "SOP-A17: Conversation Physics" in prompt_content
        
        if not (has_import or has_raw_sop):
            failures.append("Missing Conversational Spine Import OR Raw SOP-A17 Text in system_prompt.txt")
        else:
            if has_import:
                print("  [OK] System Prompt imports 'intake_triage_legal.md' Spine.")
            if has_raw_sop:
                print("  [NOTE] System Prompt uses hardcoded SOP-A17 text (Legacy).")

    # 2. Context Checks (Behavioral Guidelines)
    if not os.path.exists(context_path):
        failures.append("persona_context.md missing")
    else:
        with open(context_path, 'r') as f:
            context_content = f.read()
            
        # Check for alignment with Spine principles
        required_context_concepts = [
            "Behavioral Guidelines",
            "Pacing",
            "Stress Response"
        ]
        
        for phrase in required_context_concepts:
            if phrase not in context_content:
                failures.append(f"Missing '{phrase}' concept in persona_context.md")

    if failures:
        print("FAILURES:")
        for fail in failures:
            print(f"  [X] {fail}")
        sys.exit(1)
    else:
        print("  [OK] Persona Context aligned with Behavioral Spine.")
        print("\nSUCCESS: SOP-A17 Spine Verification Passed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", default="knowles_law_firm")
    args = parser.parse_args()
    verify_sop_a17_spine(args.client)
