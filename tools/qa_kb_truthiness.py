import os
import json
import re
import argparse
import sys
from pathlib import Path
from typing import Set, List, Dict

# Regex Patterns
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_PATTERN = r'\b(?:\+?1[-.]?)?\(?[2-9]\d{2}\)?[-.]?\d{3}[-.]?\d{4}\b' # US Phone roughly
METRIC_PATTERN = r'\b\d{1,3}%\b|\b(hundreds|thousands|millions|billions)\b' # % and "millions"
SUBJECTIVE_PATTERN = r'\b(number one|#1|industry standard|best in class|trusted by)\b'

PLACEHOLDERS = [
    r"1-800-123-4567",
    r"555-0199",
    r"example\.com",
    r"\[Insert .*\]",
    r"Lorem Ipsum",
    r"techsupport@domain.com",
    r"^\s*\[.*\]\s*$", # Python list leak
    r"As an AI language model",
]

def extract_entities(text: str) -> Dict[str, Set[str]]:
    """Extracts verifiable entities from text."""
    return {
        "emails": set(re.findall(EMAIL_PATTERN, text)),
        "phones": set(re.findall(PHONE_PATTERN, text)),
        "metrics": set(re.findall(METRIC_PATTERN, text, re.IGNORECASE)),
        "claims": set(re.findall(SUBJECTIVE_PATTERN, text, re.IGNORECASE)),
    }

def check_truthiness(agent_slug: str, agents_dir: str = "agents", min_pages: int = 5) -> bool:
    print(f"🔍 Running QA Truthiness Check V2 for: {agent_slug}")
    
    agent_path = Path(agents_dir) / agent_slug
    kb_dir = agent_path / "kb"
    
    if not kb_dir.exists():
        print(f"❌ KB Directory not found: {kb_dir}")
        return False

    errors = []
    
    # --- 1. Load Artefacts ---
    try:
        with open(kb_dir / "crawl_report.json", 'r', encoding='utf-8') as f:
            crawl_stats = json.load(f)
        with open(kb_dir / "index.json", 'r', encoding='utf-8') as f:
            index_data = json.load(f)
    except Exception as e:
        print(f"💥 Failed to load metadata: {e}")
        return False

    pages_fetched = crawl_stats.get('pages_fetched', 0)
    discovery_required = index_data.get('discovery_required', False)

    print(f"ℹ️ Crawl Stats: {pages_fetched} pages. Discovery Mode: {discovery_required}")

    # --- 2. Low Crawl Gate ---
    if pages_fetched < min_pages and not discovery_required:
        errors.append(f"❌ LOW CRAWL FAIL: Fetched {pages_fetched} pages (<{min_pages}) but 'discovery_required' is NOT true.")

    # --- 3. Build Evidence Corpus ---
    evidence_text = ""
    unique_sources = set()
    
    # Load 60_crawled content
    for f in kb_dir.glob("60_crawled_*.md"):
        try:
            evidence_text += f.read_text(encoding='utf-8') + "\n"
        except: pass
        
    # Check Evidence URL diversity (Core files only)
    for f_meta in index_data.get("files", []):
         if not f_meta['path'].startswith("kb/60_crawled"):
             for url in f_meta.get("source_urls", []):
                 unique_sources.add(url)
                 
    if len(unique_sources) < 2 and pages_fetched >= min_pages:
         # Only enforce diversity if we actually crawled enough to expect diversity
         errors.append(f"❌ Insufficient Source Diversity: Only {len(unique_sources)} unique sources cited in Core files.")

    # --- 4. Core File Scans ---
    nested_markdown_pattern = r"```markdown"
    
    for md_file in kb_dir.glob("*.md"):
        # Skip evidence files for structural/placeholder checks
        if md_file.name.startswith("60_crawled"):
            continue

        try:
            content = md_file.read_text(encoding='utf-8')
            
            # A. Structural Integrity
            if re.search(nested_markdown_pattern, content):
                errors.append(f"❌ Nested Markdown Block detected in {md_file.name}")
            
            # B. Placeholders
            for p in PLACEHOLDERS:
                if re.search(p, content, re.IGNORECASE | re.MULTILINE):
                    errors.append(f"❌ Placeholder/Leak detected in {md_file.name}: {p}")

            # C. Evidence Cross-Check (The "Big One")
            # If we are in Discovery Mode, we tend to be lenient, OR we enforce "Unknown".
            # But if we claim a phone number, it BETTER be real.
            
            entities = extract_entities(content)
            
            # Cross-check Phone Numbers
            for phone in entities["phones"]:
                # Normalization is hard, simple substring check for now
                clean_phone = re.sub(r'[\(\)\-\.\s]', '', phone) # 1234567890
                # Very rough check against evidence
                # We strip evidence to same format? Too expensive. 
                # Just check if the literal string exists nearby in evidence? 
                # Let's check if the specific phone regex matches in evidence.
                
                if phone not in evidence_text:
                     # Try lenient match (strip separators)
                     if clean_phone not in re.sub(r'[\(\)\-\.\s]', '', evidence_text):
                         errors.append(f"❌ HALLUCINATION RISK: Phone {phone} in {md_file.name} not found in Crawl Data.")

            # Cross-check Emails
            for email in entities["emails"]:
                if email.lower() not in evidence_text.lower():
                     # Exclude generic placeholders if we already caught them above
                     if "example.com" not in email:
                         errors.append(f"❌ HALLUCINATION RISK: Email {email} in {md_file.name} not found in Crawl Data.")

            # Cross-check Subjective Claims
            # These are strictly flagged unless they appear in evidence.
            for claim in entities["claims"]:
                if claim.lower() not in evidence_text.lower():
                     if "Unknown" not in content:
                         errors.append(f"❌ SUBJECTIVE CLAIM: Found '{claim}' in {md_file.name} without evidence support.")
            
            # Cross-check Word Metrics
            for metric in entities["metrics"]:
                # Metrics extracted via regex might be tuples due to grouping in pattern
                # Fix: METRIC_PATTERN has a group. re.findall returns tuple if groups exist.
                # Let's handle string or tuple.
                val = metric if isinstance(metric, str) else metric[0]
                if not val: val = metric[1] # "millions" is group 1
                
                if val.lower() not in evidence_text.lower():
                    if "Unknown" not in content:
                        errors.append(f"❌ UNVERIFIED METRIC: '{val}' in {md_file.name} not backed by evidence.")

        except Exception as e:
            errors.append(f"❌ Error reading {md_file.name}: {e}")

    # Report
    if errors:
        print("\n💥 QUALITY GATE FAILED:")
        for e in errors:
            print(e)
        return False
    
    print("✅ Quality Gate Passed (V2): Strict Verification Complete.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--min-pages", type=int, default=5)
    args = parser.parse_args()
    
    success = check_truthiness(args.slug, min_pages=args.min_pages)
    sys.exit(0 if success else 1)
