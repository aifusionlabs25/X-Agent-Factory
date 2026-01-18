"""
Intake Packager (Bolt-On #1)
Scrapes a prospect website and generates a schema-compliant dossier.json.

Usage:
    python tools/intake_packager.py --url https://example.com
    python tools/intake_packager.py --url https://example.com --extra-url https://example.com/about

Output:
    ingested_clients/<client_slug>/
        extracted/source_bundle.md
        dossier.json
        sources.json
        intake_notes.md
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import time
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin

# Third-party imports
try:
    import trafilatura
    from trafilatura.settings import use_config
    from bs4 import BeautifulSoup
    import requests
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Run: pip install trafilatura beautifulsoup4 requests")
    sys.exit(1)

# Add tools to path
sys.path.insert(0, os.path.dirname(__file__))
from schema_validator import validate_dossier

# Configuration
INGESTED_DIR = Path(__file__).parent.parent / "ingested_clients"
USER_AGENT = "X-Agent-Factory/1.0 (+https://github.com/aifusionlabs25/X-Agent-Factory)"
REQUEST_DELAY = 1.0  # Seconds between requests


def compute_slug(name):
    """Convert name to URL-safe slug (max 40 chars)."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '_', slug)
    slug = slug[:40].rstrip('_')  # Limit length, clean trailing
    return slug or "unknown_client"


def fetch_page(url, session=None):
    """Fetch a page with respectful headers and rate limiting."""
    if session is None:
        session = requests.Session()
    
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        time.sleep(REQUEST_DELAY)  # Rate limiting
        return response.text
    except Exception as e:
        print(f"   ⚠️ Failed to fetch {url}: {e}")
        return None


def extract_metadata(html, url):
    """Extract page metadata using BeautifulSoup."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Title
    title = None
    if soup.title:
        title = soup.title.string
    if not title:
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content')
    
    # Description
    description = None
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        description = meta_desc.get('content')
    if not description:
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            description = og_desc.get('content')
    
    # Domain as fallback name
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    
    return {
        "title": title or domain,
        "description": description or "",
        "domain": domain,
        "url": url
    }


def extract_main_content(html):
    """Extract main text content using Trafilatura."""
    config = use_config()
    config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
    
    content = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        include_links=False,
        output_format='markdown',
        config=config
    )
    return content or ""


def infer_industry(text, domain):
    """Infer industry from text content (heuristic, no LLM)."""
    text_lower = text.lower()
    
    industry_keywords = {
        "HVAC": ["hvac", "heating", "cooling", "air conditioning", "furnace", "thermostat"],
        "Solar": ["solar", "photovoltaic", "renewable energy", "solar panel", "inverter"],
        "Plumbing": ["plumbing", "plumber", "pipe", "drain", "water heater"],
        "Electrical": ["electrical", "electrician", "wiring", "circuit", "panel"],
        "Roofing": ["roofing", "roof", "shingle", "gutter"],
        "Landscaping": ["landscaping", "lawn", "garden", "irrigation"],
        "IT Services": ["it services", "managed services", "cybersecurity", "network"],
        "Healthcare": ["healthcare", "medical", "clinic", "patient", "health"],
        "Legal": ["legal", "law firm", "attorney", "lawyer"],
        "Real Estate": ["real estate", "property", "homes for sale", "realtor"],
        "SaaS": ["saas", "software", "platform", "cloud", "subscription"],
        "Field Service": ["field service", "dispatch", "technician", "service call"],
    }
    
    for industry, keywords in industry_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return industry
    
    # Default based on domain
    if "hvac" in domain.lower():
        return "HVAC"
    elif "solar" in domain.lower():
        return "Solar"
    
    return "General Services"


def infer_pain_points(industry):
    """Return default pain points based on industry (no LLM)."""
    pain_points_map = {
        "HVAC": [
            "Emergency repairs disrupting daily operations",
            "High energy costs from inefficient systems",
            "Difficulty scheduling timely maintenance"
        ],
        "Solar": [
            "Unclear ROI on solar investment",
            "Complex permitting and installation process",
            "Concerns about system reliability"
        ],
        "Plumbing": [
            "Water damage from undetected leaks",
            "Aging infrastructure requiring frequent repairs",
            "High costs for emergency service calls"
        ],
        "Field Service": [
            "Inefficient technician routing and dispatch",
            "Lack of real-time visibility into job status",
            "Paper-based processes slowing down operations"
        ],
        "SaaS": [
            "Integration complexity with existing tools",
            "User adoption and training challenges",
            "Scaling costs as team grows"
        ],
    }
    
    return pain_points_map.get(industry, [
        "Operational inefficiencies impacting productivity",
        "Difficulty finding reliable service providers",
        "High costs for reactive maintenance"
    ])


def build_dossier(metadata, content, urls):
    """Build a schema-compliant dossier from extracted data."""
    industry = infer_industry(content, metadata["domain"])
    pain_points = infer_pain_points(industry)
    
    # Build company name from title
    company_name = metadata["title"]
    # Clean common suffixes
    for suffix in [" | Home", " - Home", " | Official", " - Official", " | Welcome", " - Welcome"]:
        company_name = company_name.replace(suffix, "")
    company_name = company_name.strip()[:50] or metadata["domain"]
    
    dossier = {
        "schema_version": "1.0",
        "client_profile": {
            "name": company_name,
            "industry": industry,
            "region": "TBD",  # Cannot infer without more data
            "url": metadata["url"]
        },
        "target_audience": {
            "role": "Decision Maker",
            "sector": industry,
            "pain_points": pain_points
        },
        "value_proposition": {
            "core_benefit": f"Streamlined {industry.lower()} operations",
            "metric_proof": "TBD - Requires discovery call",
            "software_integration": "TBD"
        },
        "offer": {
            "type": "Demo",
            "details": "Free consultation and needs assessment"
        }
    }
    
    return dossier


def build_intake_notes(metadata, dossier, inferred_fields, unknown_fields):
    """Build intake notes documenting what was inferred vs unknown."""
    notes = f"""# Intake Notes: {dossier['client_profile']['name']}

**Processed:** {datetime.utcnow().isoformat()}Z
**Source URL:** {metadata['url']}

## Inferred Fields (from scrape)
"""
    for field, source in inferred_fields.items():
        notes += f"- **{field}**: {source}\n"
    
    notes += """
## Unknown Fields (marked TBD)
"""
    for field in unknown_fields:
        notes += f"- **{field}**: Requires manual input or discovery call\n"
    
    notes += """
## Recommended Next Steps
1. Review dossier.json and fill in TBD fields
2. Run: `python tools/factory_orchestrator.py --build-agent <path_to_dossier.json>`
3. Review generated agent artifacts
"""
    return notes


def run_intake(url, extra_urls=None, run_logger=None):
    """Main intake pipeline."""
    print(f"\n{'='*60}")
    print(f"📥 INTAKE PACKAGER")
    print(f"   URL: {url}")
    print(f"{'='*60}\n")
    
    urls_to_process = [url]
    if extra_urls:
        urls_to_process.extend(extra_urls)
    
    session = requests.Session()
    all_content = []
    sources = []
    metadata = None
    
    # Step 1: Fetch pages
    print("📡 Step 1: Fetching pages...")
    for page_url in urls_to_process:
        print(f"   > {page_url}")
        html = fetch_page(page_url, session)
        if html:
            if metadata is None:
                metadata = extract_metadata(html, page_url)
            content = extract_main_content(html)
            all_content.append(f"## Source: {page_url}\n\n{content}")
            sources.append({
                "url": page_url,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "success": True
            })
        else:
            sources.append({
                "url": page_url,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "success": False
            })
    
    if not metadata:
        print("❌ Failed to fetch any pages.")
        if run_logger:
            run_logger.error("Failed to fetch any pages")
        return False, None
    
    combined_content = "\n\n---\n\n".join(all_content)
    
    # Step 2: Compute client slug and create output directory
    client_slug = compute_slug(metadata["title"])
    output_dir = INGESTED_DIR / client_slug
    extracted_dir = output_dir / "extracted"
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Output: {output_dir}")
    
    # Log to run_logger
    if run_logger:
        run_logger.set_output("client_slug", client_slug)
        run_logger.set_output("output_dir", str(output_dir))
        run_logger.log(f"Client slug: {client_slug}")
    
    # Step 3: Build source bundle
    print("\n📝 Step 2: Building source bundle...")
    source_bundle = f"""# Source Bundle: {metadata['title']}

**Domain:** {metadata['domain']}
**Scraped:** {datetime.utcnow().isoformat()}Z

## Page Summary
{metadata.get('description', 'No description available.')}

---

{combined_content}
"""
    source_bundle_path = extracted_dir / "source_bundle.md"
    with open(source_bundle_path, 'w', encoding='utf-8') as f:
        f.write(source_bundle)
    print(f"   ✅ extracted/source_bundle.md ({len(source_bundle)} bytes)")
    
    # Step 4: Build dossier
    print("\n🔧 Step 3: Building dossier...")
    dossier = build_dossier(metadata, combined_content, urls_to_process)
    
    # Track inferred vs unknown
    inferred_fields = {
        "client_profile.name": f"From page title: {metadata['title']}",
        "client_profile.industry": f"Inferred from content keywords",
        "client_profile.url": f"From input URL",
        "target_audience.pain_points": "Default for industry"
    }
    unknown_fields = [
        "client_profile.region",
        "value_proposition.metric_proof",
        "value_proposition.software_integration"
    ]
    
    dossier_path = output_dir / "dossier.json"
    with open(dossier_path, 'w', encoding='utf-8') as f:
        json.dump(dossier, f, indent=2)
    print(f"   ✅ dossier.json")
    
    if run_logger:
        run_logger.set_output("dossier_path", str(dossier_path))
    
    # Step 5: Save sources
    sources_path = output_dir / "sources.json"
    with open(sources_path, 'w', encoding='utf-8') as f:
        json.dump({"sources": sources, "total": len(sources)}, f, indent=2)
    print(f"   ✅ sources.json")
    
    # Step 6: Build intake notes
    intake_notes = build_intake_notes(metadata, dossier, inferred_fields, unknown_fields)
    notes_path = output_dir / "intake_notes.md"
    with open(notes_path, 'w', encoding='utf-8') as f:
        f.write(intake_notes)
    print(f"   ✅ intake_notes.md")
    
    # Step 7: Validate dossier
    print("\n✔️ Step 4: Validating dossier...")
    valid, error = validate_dossier(str(dossier_path))
    if not valid:
        print(f"❌ Validation Failed: {error}")
        if run_logger:
            run_logger.error(f"Schema validation failed: {error}")
        return False, client_slug
    print("   ✅ Dossier is schema-compliant.")
    
    if run_logger:
        run_logger.log("Dossier validated successfully")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ INTAKE COMPLETE")
    print(f"   Client: {dossier['client_profile']['name']}")
    print(f"   Slug: {client_slug}")
    print(f"   Output: {output_dir}")
    print(f"\n   Next: python tools/factory_orchestrator.py --build-agent {dossier_path}")
    print(f"{'='*60}\n")
    
    return True, client_slug


def main():
    parser = argparse.ArgumentParser(description="Intake Packager - Source to Dossier")
    parser.add_argument("--url", required=True, help="Primary prospect website URL")
    parser.add_argument("--extra-url", action="append", dest="extra_urls", help="Additional URLs to scrape")
    parser.add_argument("--llm", choices=["ollama"], help="(Future) Use LLM for enhanced inference")
    parser.add_argument("--no-log", action="store_true", help="Disable run logging")
    
    args = parser.parse_args()
    
    if args.llm:
        print("⚠️ LLM mode not yet implemented. Using heuristic inference.")
    
    # Run with logging
    if args.no_log:
        success, _ = run_intake(args.url, args.extra_urls)
    else:
        from run_logger import RunLogger
        with RunLogger("intake_packager", {"url": args.url, "extra_urls": args.extra_urls or []}) as run:
            success, client_slug = run_intake(args.url, args.extra_urls, run_logger=run)
            if client_slug:
                run.set_output("client_slug", client_slug)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

