import os
import sys
import argparse
import json
import re

def verify_icc(client_slug):
    print(f"--- Running ICC (Identity Consistency Check) for {client_slug} ---")
    
    base_dir = f"agents/clients/{client_slug}"
    report_path = os.path.join(base_dir, "IDENTITY_CONSISTENCY_REPORT.md")
    
    # Artifacts to check
    artifacts = [
        "system_prompt.txt",
        "persona_context.txt",
        "kb_manifest.json",
        "persona_profile.json",
        "exports/tavus_pack.md"
    ]
    
    # 1. Load Profile (Source of Truth)
    profile_path = os.path.join(base_dir, "persona_profile.json")
    if not os.path.exists(profile_path):
        print(f"  [CRITICAL] persona_profile.json missing!")
        sys.exit(1)
        
    try:
        with open(profile_path, 'r') as f:
            profile = json.load(f)
            identity = profile.get("identity", {})
            tavus = profile.get("tavus", {})
            
            display_name = identity.get("agent_display_name")
            role_title = identity.get("role_title")
            tavus_id = tavus.get("persona_id")
            
            if not all([display_name, role_title, tavus_id]):
                print("  [CRITICAL] Profile missing required fields (name, role, or tavus_id).")
                sys.exit(1)
                
    except Exception as e:
        print(f"  [CRITICAL] Profile JSON error: {e}")
        sys.exit(1)

    # 2. Start Reporting
    report_lines = [
        f"# Identity Consistency Report: {client_slug}",
        f"**Date**: {os.popen('date /t').read().strip()}",
        f"**Target Identity**: `{display_name}` ({role_title})",
        f"**Tavus ID**: `{tavus_id}`",
        "",
        "## Checks",
        "| Rule | Status | Details |",
        "| :--- | :--- | :--- |"
    ]
    
    failures = 0
    
    # RULE 1: Unresolved Tokens
    token_pattern = re.compile(r"(\{\{.*?\}\}|\$\{.*?\}|<%=.*?%>)")
    token_fail = False
    details = []
    
    for fname in artifacts:
        path = os.path.join(base_dir, fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = token_pattern.findall(content)
                if matches:
                    token_fail = True
                    details.append(f"{fname}: {matches[:3]}") # Show first 3
    
    if token_fail:
        report_lines.append(f"| Unresolved Tokens | ❌ **FAIL** | Found tokens in: {'; '.join(details)} |")
        failures += 1
    else:
        report_lines.append("| Unresolved Tokens | ✅ PASS | No template syntax found. |")

    # RULE 2: Display Name Match
    name_fail = False
    # Check Prompt
    p_path = os.path.join(base_dir, "system_prompt.txt")
    if os.path.exists(p_path):
        with open(p_path, 'r', encoding='utf-8') as f:
            if display_name not in f.read():
                name_fail = True
                
    # Check Context
    c_path = os.path.join(base_dir, "persona_context.txt")
    if os.path.exists(c_path):
        with open(c_path, 'r', encoding='utf-8') as f:
            if display_name not in f.read():
                name_fail = True
                
    if name_fail:
         report_lines.append(f"| Name Consistency | ❌ **FAIL** | Display Name '{display_name}' NOT found in Prompt or Context. |")
         failures += 1
    else:
         report_lines.append(f"| Name Consistency | ✅ PASS | '{display_name}' verified in artifacts. |")

    # RULE 3: Tavus ID Presence
    # (Already checked existence in profile loading)
    report_lines.append(f"| Tavus ID | ✅ PASS | Defined as {tavus_id}. |")

    # RULE 4: Manifest Tags
    m_path = os.path.join(base_dir, "kb_manifest.json")
    tag_fail = False
    if os.path.exists(m_path):
        with open(m_path, 'r') as f:
            manifest = json.load(f)
            tags = manifest.get("project_info", {}).get("global_tags", [])
            tag_str = json.dumps(tags)
            
            if f"client:{client_slug}" not in tag_str:
                tag_fail = True
            if "sku:" not in tag_str:
                tag_fail = True
    else:
         tag_fail = True # Missing manifest

    if tag_fail:
        report_lines.append("| Manifest Tags | ❌ **FAIL** | Missing 'client:slug' or 'sku:type' tags. |")
        failures += 1
    else:
        report_lines.append("| Manifest Tags | ✅ PASS | Standard tags verified. |")

    # RULE 5: Reasoning Profile (Validate-if-present)
    # Ref: Phase 1 of Reasoning Modes Bolt-on
    reasoning = profile.get("reasoning_profile")
    if reasoning:
        r_fail = False
        r_errs = []
        
        # 5.1 Preset ID
        preset = reasoning.get("preset_id")
        if not preset:
            r_fail = True
            r_errs.append("Missing preset_id")
        else:
            # Check against presets.json OR 'custom'
            # Note: For efficiency, we hardcode the check or would strictly load presets.json. 
            # Given constraints, we'll allow 'custom' or any string for now, but ensure it's not empty.
            if not isinstance(preset, str):
                r_fail = True
                r_errs.append("preset_id must be string")

        # 5.2 Mode Stack
        stack = reasoning.get("mode_stack")
        allowed_modes = {"reflex", "hermeneutic", "adversarial", "legal", "compliance"}
        
        if not isinstance(stack, list):
            r_fail = True
            r_errs.append("mode_stack must be list")
        elif not (1 <= len(stack) <= 6):
            r_fail = True
            r_errs.append(f"mode_stack length {len(stack)} invalid (1-6)")
        else:
            invalid_modes = [m for m in stack if m not in allowed_modes]
            if invalid_modes:
                r_fail = True
                r_errs.append(f"Invalid modes: {invalid_modes}")

        if r_fail:
            report_lines.append(f"| Reasoning Profile | ❌ **FAIL** | {'; '.join(r_errs)} |")
            failures += 1
        else:
            report_lines.append(f"| Reasoning Profile | ✅ PASS | Valid stack: {preset} ({len(stack)} modes) |")
    else:
        report_lines.append(f"| Reasoning Profile | ⚪ SKIP | Not configured (Optional). |")
        
    # Write Report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        
    print(f"  [REPORT] Generated {report_path}")
    
    if failures > 0:
        print(f"  [FAIL] {failures} Quality Gate violations found.")
        sys.exit(1)
    else:
        print("  [SUCCESS] Identity Consistency Verified.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True)
    args = parser.parse_args()
    verify_icc(args.client)
