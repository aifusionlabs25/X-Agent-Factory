import argparse
import json
import os
import sys

def load_client_profile(client_slug):
    profile_path = f"agents/clients/{client_slug}/client_profile.json"
    if not os.path.exists(profile_path):
        print(f"Error: Client profile not found at {profile_path}")
        sys.exit(1)
    
    with open(profile_path, 'r') as f:
        return json.load(f)

def write_kb_file(client_slug, filename, content):
    path = f"agents/clients/{client_slug}/kb/{filename}"
    with open(path, 'w') as f:
        f.write(content)
    print(f"Generated: {path}")

def generate_kb(client_slug, domain):
    profile = load_client_profile(client_slug)
    firm_name = profile.get("firm_name", "The Firm")
    phone = profile.get("main_phone", "(555) 555-5555")
    offices = profile.get("offices", [])
    
    # 1. Firm Facts
    facts_content = f"# Firm Facts: {firm_name}\n\n"
    facts_content += f"- **Official Domain**: {domain}\n"
    facts_content += f"- **Main Phone**: {phone}\n"
    facts_content += "- **Email Policy**: Do not disclose internal emails. Use web contact form.\n\n"
    facts_content += "## Office Locations\n"
    for office in offices:
        facts_content += f"- **{office.get('city')}**: {office.get('address')}\n"
    
    write_kb_file(client_slug, "firm_facts.txt", facts_content)

    # 2. Practice Areas
    practice_content = f"# Practice Areas: {firm_name}\n\n"
    practice_content += "## Core Areas\n"
    practice_content += "- **DUI Defense**: Driving Under the Influence, Extreme DUI, Super Extreme DUI.\n"
    practice_content += "- **Criminal Defense**: Drugs, Assault, Theft, Domestic Violence.\n"
    practice_content += "- **Personal Injury**: Car accidents, Slip and Fall (Check firm specifics).\n\n"
    practice_content += "> [!IMPORTANT]\n"
    practice_content += "> We accept intake for ALL legal matters, but primarily specialize in the above. If a caller has a different issue, take the intake and the firm will refer it out.\n"
    
    write_kb_file(client_slug, "practice_areas.txt", practice_content)

    # 3. Intake Playbook
    playbook_content = f"# Intake Playbook\n\n"
    playbook_content += "## Phase 1: Greeting & Triage\n"
    playbook_content += "- Greeting: \"Thank you for calling {firm_name}...\"\n"
    playbook_content += "- Triage: \"How may we help you fight for your rights today?\"\n\n"
    playbook_content += "## Phase 2: Vitals & Urgency\n"
    playbook_content += "- Name, Callback Number, Safe to Contact?\n"
    playbook_content += "- Urgency Check: In Custody? Court Date < 72h? 911 Issue?\n\n"
    playbook_content += "## Phase 3: Facts\n"
    playbook_content += "- Incident Location (City/State).\n"
    playbook_content += "- Brief Narrative.\n\n"
    playbook_content += "## Phase 4: Closing\n"
    playbook_content += "- Standard: \"Next business day follow-up.\"\n"
    playbook_content += "- Urgent: \"Escalating now. Please also call {phone}.\"\n"
    
    write_kb_file(client_slug, "intake_playbook.txt", playbook_content)

    # 4. FAQ & Objections
    faq_content = f"# FAQ & Objections\n\n"
    faq_content += "## Common Questions\n"
    faq_content += "**Q: Can I speak to a lawyer right now?**\n"
    faq_content += "A: \"Our attorneys are dedicated to their clients and may be in court. I will gather your information so they can review your case effectively before speaking with you.\"\n\n"
    faq_content += "**Q: How much do you charge?**\n"
    faq_content += "A: \"Fees vary by case complexity. We offer consultations to discuss your specific situation and provide a transparent quote.\"\n\n"
    faq_content += "**Q: Do you take cases in [Other State]?**\n"
    faq_content += "A: \"We are based in Arizona but can take your information. Our team will verify if we can assist or help find you a referral in your area.\"\n"
    
    write_kb_file(client_slug, "faq_objections.txt", faq_content)

    # 5. Routing & Escalations
    routing_content = f"# Routing & Escalations\n\n"
    routing_content += "## Priority 1: IMMEDIATE\n"
    routing_content += "- **Triggers**: In Custody / Arrest in Progress / Court Date < 72h.\n"
    routing_content += f"- **Action**: Log as URGENT. Instruct caller to call {phone}.\n\n"
    routing_content += "## Priority 2: STANDARD\n"
    routing_content += "- **Triggers**: General Inquiries / Post-Arrest (Bonded Out) / Civil.\n"
    routing_content += "- **Action**: Log Intake. Promise follow-up next business day.\n\n"
    routing_content += "## Priority 3: EMERGENCY\n"
    routing_content += "- **Triggers**: Violence / Medical Emergency.\n"
    routing_content += "- **Action**: **HANG UP AND DIAL 911**.\n"
    
    write_kb_file(client_slug, "routing_escalations.txt", routing_content)

    # 6. Compliance Disclaimers
    comp_content = f"# Compliance & Disclaimers\n\n"
    comp_content += "## Mandatory Scripts\n"
    comp_content += "1. **No Legal Advice**: \"I cannot provide legal advice. I am here to gather information.\"\n"
    comp_content += "2. **No Attorney-Client Relationship**: \"This intake process does not create an attorney-client relationship.\"\n"
    comp_content += "3. **Confidentiality**: \"Your information is kept confidential for our internal review.\"\n"
    
    write_kb_file(client_slug, "compliance_disclaimers.txt", comp_content)

    # 7. Tone Snippets
    tone_content = f"# Tone & Voice Snippets\n\n"
    tone_content += "## Empathetic yet Controlled\n"
    tone_content += "- \"I understand this is a stressful time. Let's get these details down so we can start helping you.\"\n"
    tone_content += "- \"Thank you for sharing that. Validating: You said the incident happened in [City]?\"\n\n"
    tone_content += "## Professional Re-direct\n"
    tone_content += "- \"I hear you. To ensure the attorney gets the right information, I need to ask...\"\n"
    
    write_kb_file(client_slug, "tone_snippets.txt", tone_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Client KB Pack")
    parser.add_argument("--client", required=True, help="Client slug (e.g. knowles_law_firm)")
    parser.add_argument("--domain", required=True, help="Client domain (e.g. knowleslaw.org)")
    args = parser.parse_args()
    
    generate_kb(args.client, args.domain)
