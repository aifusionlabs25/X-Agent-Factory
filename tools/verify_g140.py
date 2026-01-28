import os
import sys
import json

def verify_persona_identity(client_slug):
    print(f"--- Verifying G14.0 Persona Identity for {client_slug} ---")
    
    base_dir = f"agents/clients/{client_slug}"
    profile_path = os.path.join(base_dir, "persona_profile.json")
    context_path = os.path.join(base_dir, "persona_context.txt")
    prompt_path = os.path.join(base_dir, "system_prompt.txt")
    
    # 1. Profile Existence & Schema Check
    print("\n[Step 1] Profile Validation...")
    if not os.path.exists(profile_path):
        print(f"  [FAIL] persona_profile.json Missing!")
        sys.exit(1)
        
    try:
        with open(profile_path, 'r') as f:
            profile = json.load(f)
            
        required_keys = ["identity", "tavus", "visual", "voice_intent"]
        for key in required_keys:
            if key not in profile:
                print(f"  [FAIL] Missing root key: {key}")
                sys.exit(1)
                
        print("  [OK] Profile Schema Valid.")
        agent_name = profile["identity"]["agent_display_name"]
        
    except json.JSONDecodeError:
        print("  [FAIL] Invalid JSON!")
        sys.exit(1)

    # 2. Context Injection Check
    print("\n[Step 2] Context Injection Check...")
    with open(context_path, 'r') as f:
        context_content = f.read()
        
    if "## Visual Persona" in context_content:
        print("  [OK] Visual Persona section present in context.")
    else:
        print("  [FAIL] Visual Persona section MISSING in context!")
        sys.exit(1)
        
    if agent_name in context_content:
        print(f"  [OK] Agent Name '{agent_name}' found in context.")
    else:
        print(f"  [WARN] Agent Name '{agent_name}' NOT found in context text.")

    # 3. System Prompt Check (Template Verification)
    print("\n[Step 3] System Prompt Alignment...")
    with open(prompt_path, 'r') as f:
        prompt_content = f.read()
        
    if agent_name in prompt_content:
         print(f"  [OK] Agent Name '{agent_name}' found in system prompt.")
    else:
         print(f"  [FAIL] Agent Name '{agent_name}' NOT found in system prompt!")
         sys.exit(1)

    # 4. Context Check (Identity Verification)
    print("\n[Step 4] Context Alignment...")
    with open(context_path, 'r') as f:
        context_content = f.read()
        
    if agent_name in context_content:
         print(f"  [OK] Persona Context contains Agent Name '{agent_name}'.")
    else:
         print(f"  [FAIL] Persona Context does NOT contain Agent Name '{agent_name}'!")
         sys.exit(1)

    print("\nSUCCESS: G14.0 Persona Identity Verified.")

if __name__ == "__main__":
    verify_persona_identity("knowles_law_firm")
