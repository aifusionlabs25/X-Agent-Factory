import os
import json
import argparse
import sys
from datetime import datetime

def generate_build(args):
    print(f"--- Generating SKU Build: {args['clientSlug']} ---")
    
    base_dir = f"agents/clients/{args['clientSlug']}"
    kb_dir = os.path.join(base_dir, "kb")
    gr_dir = os.path.join(kb_dir, "guardrails")
    export_dir = os.path.join(base_dir, "exports")
    
    # 1. Create Directories
    os.makedirs(gr_dir, exist_ok=True)
    os.makedirs(export_dir, exist_ok=True)
    
    # 2. Client Profile
    client_profile = {
        "client_name": args['clientName'],
        "domain": args['domain'],
        "region": args['region'],
        "key_contacts": ["Intake Team"]
    }
    with open(os.path.join(base_dir, "client_profile.json"), "w") as f:
        json.dump(client_profile, f, indent=4)
        print("  [OK] client_profile.json")

    # 3. Persona Profile (G14.0)
    persona_profile = {
        "identity": {
            "agent_display_name": args['agentName'],
            "role_title": args['roleTitle'],
            "tone_preset": "Professional, Empathetic, Controlled"
        },
        "tavus": {
            "persona_id": args.get('tavusPersona', "DEFAULT"),
            "visual_notes": "Business formal attire."
        },
        "visual": {
            "headshot_path": "placeholder_headshot.png",
            "description": f"Professional, {args.get('emotion', 'approachable')}."
        },
        "voice_intent": {
            "pace": args.get('pace', "Moderate"),
            "energy": "Balanced",
            "warmth": "High"
        }
    }
    
    # Optional: Reasoning Profile (G15.2 Bolt-on)
    if "reasoning_profile" in args:
        persona_profile["reasoning_profile"] = args["reasoning_profile"]
    with open(os.path.join(base_dir, "persona_profile.json"), "w") as f:
        json.dump(persona_profile, f, indent=4)
        print("  [OK] persona_profile.json")

    # 4. Build Meta (State)
    build_meta = {
        "status": "DRAFT",
        "created_at": datetime.now().isoformat(),
        "sku_type": "attorney-intake"
    }
    with open(os.path.join(base_dir, "build_meta.json"), "w") as f:
        json.dump(build_meta, f, indent=4)
        print("  [OK] build_meta.json")

    # 5. Guardrails (G13.1)
    # Using defaults for now
    gr_files = {
        "compliance_disclaimers.txt": "Mandatory Scripts: No Legal Advice, No Attorney-Client Relationship, Recording Consent.",
        "prohibited_responses.txt": "Forbidden phrases (case evaluation, outcomes) and safe alternatives.",
        "emergency_protocols.txt": "Trigger words and scripts for 911, violence, and medical emergencies.",
        "recording_and_privacy.txt": "One-party consent logic and privacy scripts."
    }
    for fname, content in gr_files.items():
        with open(os.path.join(gr_dir, fname), "w") as f:
            f.write(f"# {fname}\n{content}\n(Generated Default Content)")
    print(f"  [OK] Guardrails ({len(gr_files)} files)")

    # 6. Standard KB Files
    std_files = ["firm_facts.txt", "practice_areas.txt", "intake_playbook.txt", "faq_objections.txt", "routing_escalations.txt"]
    for fname in std_files:
        with open(os.path.join(kb_dir, fname), "w") as f:
            f.write(f"# {fname}\nPlaceholder content for {args['clientName']}")
    print(f"  [OK] Standard KB ({len(std_files)} files)")

    # 7. Manifest (G13.2)
    manifest = {
        "project_info": {
            "tavus_project_name": f"{args['clientSlug']}_v1",
            "persona_name": args['agentName'],
            "global_tags": [f"client:{args['clientSlug']}", "sku:attorney-intake"]
        },
        "files": []
    }
    
    # Add guardrails to manifest
    for fname in gr_files.keys():
        manifest["files"].append({
            "filename": f"guardrails/{fname}",
            "tags": ["priority:critical", "kb:guardrail", "type:compliance"],
            "purpose": "Guardrail"
        })
        
    # Add std files to manifest
    for fname in std_files:
        manifest["files"].append({
            "filename": fname,
            "tags": ["priority:high", "kb:core", "type:content"],
            "purpose": "Standard Content"
        })
        
    with open(os.path.join(base_dir, "kb_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)
        print("  [OK] kb_manifest.json")

    # 8. Tavus Pack
    with open(os.path.join(export_dir, "tavus_pack.md"), "w") as f:
        f.write(f"# Tavus Pack: {args['clientName']}\n\nGenerated via Build Studio.")
    print("  [OK] tavus_pack.md")
    
    # 9. Context Files (Derived)
    with open(os.path.join(base_dir, "persona_context.txt"), "w") as f:
        f.write(f"# Agent Persona Context: {args['agentName']}\n\n## Visual Persona\nDerived from persona_profile.json")
    
    with open(os.path.join(base_dir, "system_prompt.txt"), "w") as f:
         f.write(f"# System Prompt\nName: {args['agentName']}")
         
         # Phase 3: Reasoning Injection (Tiny Snippet)
         reasoning = args.get("reasoning_profile")
         if reasoning and reasoning.get("preset_id"):
             # Format: Minimalist, no numbering (James compatibility)
             snippet = (
                 f"\n\n[Reasoning: {reasoning['preset_id']}]\n"
                 f"Stack: {' > '.join(reasoning.get('mode_stack', []))}\n"
                 f"Required: {', '.join(reasoning.get('artifacts_expected', []))}\n"
                 f"Checks: {', '.join(reasoning.get('failure_checks', []))}"
             )
             f.write(snippet)
             print(f"  [INJECT] Reasoning snippet ({reasoning['preset_id']})")

    print("\n[SUCCESS] Build Generation Complete.")
    print(f"Location: {base_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="JSON string of build arguments")
    args = parser.parse_args()
    
    try:
        json_input = args.json
        if json_input.endswith(".json") and os.path.exists(json_input):
            with open(json_input, 'r') as f:
                data = json.load(f)
        else:
             data = json.loads(json_input)
             
        generate_build(data)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating build: {e}")
        sys.exit(1)
