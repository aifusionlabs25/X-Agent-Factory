"""
Batch Processor for X Agent Factory
Processes multiple leads from qualified_domains.json through client_ingest.py
Output: batch_report.csv
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import argparse
import os
import json
import csv
import time
from datetime import datetime

def run_batch(leads_file: str):
    print("🏭 BATCH PROCESSOR INITIATED")
    print("="*50)
    
    # Load leads
    if not os.path.exists(leads_file):
        print(f"❌ Leads file not found: {leads_file}")
        return
        
    with open(leads_file, 'r', encoding='utf-8') as f:
        leads = json.load(f)
    
    print(f"📋 Loaded {len(leads)} leads from {leads_file}")
    
    # Prepare output
    report = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"intelligence/batch_report_{timestamp}.csv"
    
    # Process each lead
    for i, lead in enumerate(leads):
        print(f"\n[{i+1}/{len(leads)}] Processing: {lead.get('title', 'Unknown')[:40]}...")
        
        url = lead.get('href', '')
        title = lead.get('title', 'Unknown')
        score = lead.get('nova_score', 0)
        
        if not url:
            report.append({
                'CompanyName': title,
                'URL': '',
                'DemoLink': '',
                'Status': 'SKIPPED - No URL'
            })
            continue
        
        # Generate slug from title
        slug = title.lower()
        slug = ''.join(c if c.isalnum() or c == ' ' else '' for c in slug)
        slug = slug.strip().replace(' ', '_')[:50]
        
        try:
            # Import and run client_ingest
            from client_ingest import ingest_client
            ingest_client(url)
            
            demo_link = f"/demo/{slug}"
            status = "SUCCESS"
            
        except Exception as e:
            demo_link = ""
            status = f"FAILED - {str(e)[:50]}"
            print(f"   ⚠️ Error: {e}")
        
        report.append({
            'CompanyName': title,
            'URL': url,
            'Score': score,
            'DemoLink': demo_link,
            'Status': status
        })
        
        # Polite delay between requests
        time.sleep(3)
    
    # Write CSV report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['CompanyName', 'URL', 'Score', 'DemoLink', 'Status'])
        writer.writeheader()
        writer.writerows(report)
    
    # Summary
    success_count = len([r for r in report if r['Status'] == 'SUCCESS'])
    print(f"\n{'='*50}")
    print(f"✅ BATCH COMPLETE")
    print(f"   Total: {len(leads)}")
    print(f"   Success: {success_count}")
    print(f"   Failed: {len(leads) - success_count}")
    print(f"   Report: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch Processor")
    parser.add_argument("--file", default="intelligence/leads/hvac_in_phoenix_qualified.json", 
                        help="Path to qualified leads JSON file")
    args = parser.parse_args()
    
    run_batch(args.file)
