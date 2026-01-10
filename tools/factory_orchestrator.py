"""
Factory Orchestrator
Watches for new hunt results and processes them through the full pipeline.

Pipeline:
1. Detect new *_qualified.json files
2. Run Contact Enricher on each lead
3. Run Nova for final priority ranking (A/B/C)
4. Run Sparkle to draft emails for A-tier leads
5. Compile Markdown report

Usage:
    python tools/factory_orchestrator.py                    # Process all unprocessed files
    python tools/factory_orchestrator.py --file <path>      # Process specific file
    python tools/factory_orchestrator.py --watch            # Watch mode (future)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import json
import time
import glob
import argparse
from datetime import datetime
from pathlib import Path

# Add tools to path
sys.path.insert(0, os.path.dirname(__file__))

from utils import load_env
from contact_enricher import enrich_contact
from email_generator import generate_outreach_email, save_email_template
from db_manager import init_db, upsert_lead

# Initialize DB on startup
init_db()

# Configuration
LEADS_DIR = Path(__file__).parent.parent / "intelligence" / "leads"
REPORTS_DIR = Path(__file__).parent.parent / "intelligence" / "reports"
PROCESSED_LOG = LEADS_DIR / ".processed"

def load_specialist(name):
    path = Path(__file__).parent.parent / 'specialists' / f'{name}.txt'
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def generate_with_ollama(persona, prompt, model="llama3"):
    import requests
    full_prompt = f"{persona}\n\n{prompt}"
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "format": "json"
        }, timeout=60)
        response.raise_for_status()
        data = response.json()
        return json.loads(data['response'])
    except Exception as e:
        print(f"   ⚠️ Ollama Error: {e}")
        return None

def get_processed_files():
    """Get list of already processed files."""
    if not PROCESSED_LOG.exists():
        return set()
    with open(PROCESSED_LOG, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f.readlines())

def mark_as_processed(filepath):
    """Mark a file as processed."""
    with open(PROCESSED_LOG, 'a', encoding='utf-8') as f:
        f.write(f"{filepath}\n")

def rank_lead_priority(lead, vertical_context=""):
    """Use Nova to rank lead priority A/B/C."""
    persona = load_specialist("Nova")
    
    prompt = f"""
    [[FACTORY_MODE]]
    {persona}
    
    [LEAD DATA]
    Business: {lead.get('title', 'Unknown')}
    URL: {lead.get('href', '')}
    Nova Score: {lead.get('nova_score', 0)}/10
    Reason: {lead.get('nova_reason', '')}
    Vertical: {vertical_context}
    
    [TASK]
    Analyze the business and assign a priority.
    
    CRITICAL: You must extract specific Sales Intelligence (BD) signals.
    1. Hook: A punchy opening line for an email (e.g. "Saw your 5-star reviews but noticed the broken booking link").
    2. Pain Point: The specific problem they have (e.g. "Manual scheduling", "Generic website").
    3. Sales Angle: How we pitch our agent (e.g. "24/7 Receptionist", "After-hours triage").
    
    Return JSON ONLY:
    {{
        "priority": "A" or "B" or "C",
        "reason": "1 sentence justification",
        "hook": "The opening line",
        "pain_point": "The detected problem",
        "sales_angle": "The strategy",
        "decision_maker": "Likely owner name (or 'Owner')",
        "urgency_score": <1-10>
    }}
    [/TASK]
    """
    
    return generate_with_ollama(persona, prompt, model="qwen2.5:32b")

def generate_email_draft(lead, pain_point=""):
    """Use Sparkle to generate email draft."""
    persona = load_specialist("Sparkle")
    
    prompt = f"""
    [[GHOST_MODE]]
    [[FACTORY_MODE]]
    {persona}
    
    [LEAD INFO]
    Business: {lead.get('title', 'Unknown')}
    URL: {lead.get('href', '')}
    Pain Point: {pain_point}
    Priority: {lead.get('priority', 'A')}
    
    [TASK]
    Write a cold outreach email. Be punchy, professional, no fluff.
    Reference their specific pain point.
    
    Return JSON ONLY:
    {{
        "subject": "Subject line (max 60 chars)",
        "body": "Email body (3-4 sentences max)",
        "ps_line": "Optional P.S. line for urgency"
    }}
    [/TASK]
    """
    
    return generate_with_ollama(persona, prompt)

def extract_domain(url):
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except:
        return url

def process_hunt_file(filepath):
    """Process a single qualified leads JSON file."""
    print(f"\n{'='*60}")
    print(f"🏭 FACTORY ORCHESTRATOR")
    print(f"   Processing: {Path(filepath).name}")
    print(f"{'='*60}")
    
    # Load leads
    with open(filepath, 'r', encoding='utf-8') as f:
        leads = json.load(f)
    
    if not leads:
        print("   ⚠️ No leads found in file.")
        return None
    
    print(f"   📋 Loaded {len(leads)} leads")
    
    # Extract vertical from filename
    filename = Path(filepath).stem
    vertical = filename.replace('_qualified', '').replace('_', ' ').title()
    
    # Pipeline stats
    total_leads = len(leads)
    a_tier = []
    b_tier = []
    c_tier = []
    total_mrr = 0
    
    # Process each lead
    for i, lead in enumerate(leads):
        print(f"\n   [{i+1}/{total_leads}] {lead.get('title', 'Unknown')[:40]}...")
        
        # 1. Contact Enricher (stub)
        domain = extract_domain(lead.get('href', ''))
        if domain:
            print(f"      > 📞 Contact Enricher: {domain}")
            contact = enrich_contact(domain)
            lead['contact'] = contact
        
        # 2. Nova Priority Ranking
        print(f"      > 💠 Nova: Ranking priority...")
        priority_data = rank_lead_priority(lead, vertical)
        if priority_data:
            lead['priority'] = priority_data.get('priority', 'B')
            lead['priority_reason'] = priority_data.get('reason', '')
            lead['urgency'] = priority_data.get('urgency_score', 5)
            lead['sales_intel'] = priority_data # SAVE ALL INTEL TO DB
        else:
            lead['priority'] = 'B'
            lead['priority_reason'] = 'Default ranking'
            lead['urgency'] = 5
            lead['sales_intel'] = {}
        
        # Sort into tiers
        if lead['priority'] == 'A':
            a_tier.append(lead)
        elif lead['priority'] == 'B':
            b_tier.append(lead)
        else:
            c_tier.append(lead)
        
        # 3. Sparkle Email Draft (A-tier only)
        if lead['priority'] == 'A':
            print(f"      > ✨ Sparkle: Drafting email...")
            email_data = generate_email_draft(lead, lead.get('nova_reason', ''))
            if email_data:
                lead['email_draft'] = email_data
        
        # Estimate MRR
        score = lead.get('nova_score', 5)
        if score >= 8:
            total_mrr += 2000
        elif score >= 6:
            total_mrr += 1000
        else:
            total_mrr += 500
        
        # Save to Database
        lead['vertical'] = vertical
        lead['location'] = "Unknown" # Parser improvement for later
        print(f"      > 💾 DB: Saving lead to factory.db...")
        upsert_lead(lead)
        
        # Small delay to not overwhelm Ollama
        time.sleep(0.5)
    
    # Generate Report
    print(f"\n   📝 Generating report...")
    report = generate_report(
        vertical=vertical,
        leads=leads,
        a_tier=a_tier,
        b_tier=b_tier,
        c_tier=c_tier,
        total_mrr=total_mrr,
        source_file=filepath
    )
    
    # Save Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_filename = f"{filename.replace('_qualified', '')}_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    report_path = REPORTS_DIR / report_filename
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n   ✅ Report saved: {report_path}")
    print(f"   📊 Summary: {len(a_tier)} A-tier | {len(b_tier)} B-tier | {len(c_tier)} C-tier")
    print(f"   💰 Estimated MRR: ${total_mrr:,}")
    
    # Send Email Report
    try:
        from email_sender import send_batch_report
        batch_name = f"{vertical.upper().replace(' ', '_')}_BATCH_{datetime.now().strftime('%Y%m%d')}"
        admin_email = os.environ.get("FACTORY_ADMIN_EMAIL", "aifusionlabs@gmail.com")
        print(f"\n   📧 Sending email report to {admin_email}...")
        result = send_batch_report(
            batch_name=batch_name,
            vertical=vertical,
            leads=leads,
            to_email=admin_email
        )
        if result:
            print(f"   ✅ Email sent! Batch: {batch_name}")
        else:
            print(f"   ⚠️ Email not sent (check RESEND_API_KEY)")
    except Exception as e:
        print(f"   ⚠️ Email error: {e}")
    
    # Mark as processed
    mark_as_processed(filepath)
    
    return report_path

def generate_report(vertical, leads, a_tier, b_tier, c_tier, total_mrr, source_file):
    """Generate Markdown report."""
    
    # Header
    report = f"""# 🏭 Hunt Report: {vertical}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  
**Source:** `{Path(source_file).name}`

---

## 📊 Summary

| Metric | Value |
|--------|-------|
| Total Leads | {len(leads)} |
| A-Tier (Hot) | {len(a_tier)} |
| B-Tier (Warm) | {len(b_tier)} |
| C-Tier (Cold) | {len(c_tier)} |
| **Est. Monthly MRR** | **${total_mrr:,}** |

---

## 🔥 A-Tier Leads (Contact Immediately)

"""
    
    if a_tier:
        for i, lead in enumerate(a_tier[:5]):  # Top 5
            email = lead.get('email_draft', {})
            contact = lead.get('contact', {}).get('best_contact', {})
            
            report += f"""### {i+1}. {lead.get('title', 'Unknown')}

- **URL:** [{lead.get('href', '')}]({lead.get('href', '')})
- **Score:** {lead.get('nova_score', 'N/A')}/10
- **Why A-Tier:** {lead.get('priority_reason', 'High potential')}
- **Contact:** {contact.get('email', 'N/A')} ({contact.get('name', 'Unknown')})

**📧 Email Draft:**

> **Subject:** {email.get('subject', 'N/A')}
>
> {email.get('body', 'No draft generated')}
>
> {email.get('ps_line', '')}

---

"""
    else:
        report += "*No A-tier leads found in this hunt.*\n\n---\n\n"
    
    # B-Tier Summary
    report += f"""## 🟡 B-Tier Leads (Follow Up This Week)

| Business | Score | Reason |
|----------|-------|--------|
"""
    
    for lead in b_tier[:10]:
        report += f"| {lead.get('title', 'Unknown')[:30]} | {lead.get('nova_score', 'N/A')}/10 | {lead.get('priority_reason', 'N/A')[:40]} |\n"
    
    if not b_tier:
        report += "| *No B-tier leads* | - | - |\n"
    
    # Footer
    report += f"""

---

## 📎 Full Data

The complete lead data is available in:
- `{Path(source_file).name}`

---

*Generated by X Agent Factory Orchestrator*
"""
    
    return report

def find_unprocessed_files():
    """Find all qualified JSON files that haven't been processed."""
    processed = get_processed_files()
    pattern = str(LEADS_DIR / "*_qualified.json")
    all_files = glob.glob(pattern)
    return [f for f in all_files if f not in processed]

def main():
    load_env()
    
    parser = argparse.ArgumentParser(description="Factory Orchestrator")
    parser.add_argument("--file", help="Process a specific file")
    parser.add_argument("--watch", action="store_true", help="Watch mode (future)")
    parser.add_argument("--reprocess", action="store_true", help="Reprocess all files")
    args = parser.parse_args()
    
    if args.reprocess:
        # Clear processed log
        if PROCESSED_LOG.exists():
            PROCESSED_LOG.unlink()
        print("🔄 Cleared processed log. Will reprocess all files.")
    
    if args.file:
        # Process specific file
        if os.path.exists(args.file):
            process_hunt_file(args.file)
        else:
            print(f"❌ File not found: {args.file}")
    elif args.watch:
        # Watch mode (future implementation)
        print("👀 Watch mode not yet implemented. Use manual mode for now.")
    else:
        # Process all unprocessed files
        unprocessed = find_unprocessed_files()
        
        if not unprocessed:
            print("✅ No unprocessed hunt files found.")
            print(f"   Watching: {LEADS_DIR}")
            return
        
        print(f"📋 Found {len(unprocessed)} unprocessed hunt files:")
        for f in unprocessed:
            print(f"   - {Path(f).name}")
        
        for filepath in unprocessed:
            process_hunt_file(filepath)
        
        print(f"\n{'='*60}")
        print(f"✅ FACTORY ORCHESTRATOR COMPLETE")
        print(f"   Processed: {len(unprocessed)} files")
        print(f"   Reports: {REPORTS_DIR}")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()
