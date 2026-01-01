"""
THE BOLT-ON ENGINEER
Merges `universal_base.json` with a specific Prospect Dossier to create a Custom System Prompt.
"""
import json
import os
import sys

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def merge_soul(base, dossier):
    """
    Replaces dynamic slots in the base model with dossier data.
    """
    # Simple text replacement for the demo. In a real LLM call, this would be more complex.
    base_str = json.dumps(base, indent=4)
    
    replacements = {
        "{{target_industry}}": dossier.get("industry", "Unknown Industry"),
        "{{target_role}}": dossier.get("role", "Operations Manager"),
        "{{friction_point}}": dossier.get("pain_point", "Operational Friction"),
        "{{incumbent_software}}": dossier.get("software", "Legacy Systems")
    }
    
    for key, value in replacements.items():
        base_str = base_str.replace(key, value)
        
    return json.loads(base_str)

def generate_system_prompt(merged_soul):
    """
    Converts the merged JSON into a text-based System Prompt.
    """
    core = merged_soul["persona_core"]
    logic = merged_soul["tactical_logic"]
    
    prompt = f"""
### SYSTEM PROMPT: {core['name']}
**Role:** {core['role']}
**Industry Target:** {merged_soul['dynamic_slots']['target_industry']}

# PRIME DIRECTIVE
{core['prime_directive']}

# THE VIBE
{core['voice']}

# TACTICAL LOGIC
1. **Opening:** {logic['opening']}
2. **The Hook:** {logic['hook']}
3. **The Closer:** {logic['closer']}

# COMMUNICATION RULES
"""
    for rule in merged_soul["communication_protocol"]:
        prompt += f"- {rule}\n"
        
    return prompt

def main():
    # Paths (Assumed relative to this script in mechanisms/tools)
    # tools/bolt_on_engineer.py -> templates/base_models/universal_base.json
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "base_models", "universal_base.json")
    
    # Check for dossier argument
    if len(sys.argv) < 2:
        print("Usage: python bolt_on_engineer.py <path_to_dossier.json>")
        return

    dossier_path = sys.argv[1]
    
    if not os.path.exists(base_path):
        print(f"❌ Critical Error: Base Model not found at {base_path}")
        return
        
    if not os.path.exists(dossier_path):
        print(f"❌ Critical Error: Dossier not found at {dossier_path}")
        return

    print(f"🔧 BOLT-ON ENGINEER: Fusing Universal Base with {os.path.basename(dossier_path)}...")
    
    try:
        base = load_json(base_path)
        dossier = load_json(dossier_path)
        
        merged = merge_soul(base, dossier)
        system_prompt = generate_system_prompt(merged)
        
        # Output
        output_path = os.path.join(os.path.dirname(dossier_path), f"SYSTEM_PROMPT_{dossier.get('industry', 'CUSTOM')}.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(system_prompt)
            
        print(f"✅ FUSION COMPLETE. System Prompt generated: {output_path}")
        
    except Exception as e:
        print(f"❌ FUSION FAILED: {e}")

if __name__ == "__main__":
    main()
