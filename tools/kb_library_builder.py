
import os
import json
import logging
import argparse
import hashlib
import re
import requests
import datetime
import shutil
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional

# External libs (assumed available in env)
import trafilatura
from bs4 import BeautifulSoup
import tiktoken
from llm_client import LLMClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KBLibraryBuilder:
    def __init__(self, slug: str, agents_dir: str = "agents", ingested_dir: str = "ingested_clients", 
                 min_files: int = 25, max_files: int = 60, chunk_tokens: int = 650, overlap: int = 80,
                 dossier_path: str = None):
        self.slug = slug
        self.agents_dir = Path(agents_dir)
        self.ingested_dir = Path(ingested_dir)
        self.agent_path = self.agents_dir / slug
        # Use explicit dossier_path if provided, otherwise derive from slug
        if dossier_path:
            self.dossier_path = Path(dossier_path)
        else:
            self.dossier_path = self.ingested_dir / slug / "dossier.json"
        
        self.kb_dir = self.agent_path / "kb"
        self.min_files = min_files
        self.max_files = max_files
        self.chunk_tokens = chunk_tokens
        self.overlap = overlap
        
        self.enc = tiktoken.get_encoding("cl100k_base")
        self.enc = tiktoken.get_encoding("cl100k_base")
        self.generated_files: List[Dict] = [] # Track file metadata

        # Initialize LLM Client
        self.llm = LLMClient()
        
        # Crawler Stats
        self.crawl_stats = {
            "pages_fetched": 0,
            "urls": [],
            "blocked_urls": [],
            "status_codes": {},
            "crawl_depth": 0,
            "elapsed_ms": 0
        }

        # Standard Topics (Required Set) with Canonical Tags
        self.file_map = {
            "00_overview": {
                "keywords": ["Overview", "Executive Summary", "Mission"],
                "tags": ["company_overview", "offerings", "tone_voice"]
            },
            "05_ICP_and_personas": {
                "keywords": ["ICP", "Target Audience", "Persona"],
                "tags": ["icp", "discovery"]
            },
            "10_services_and_offerings": {
                "keywords": ["Services", "Offerings", "Products"],
                "tags": ["offerings"]
            },
            "15_pricing_and_packages": {
                "keywords": ["Pricing", "Costs", "Packages"],
                "tags": ["pricing"]
            },
            "20_FAQ": {
                "keywords": ["FAQ", "Q&A", "Questions"],
                "tags": ["faq"]
            },
            "25_objections_and_rebuttals": {
                "keywords": ["Objections", "Rebuttals", "Counterarguments"],
                "tags": ["objections", "discovery"]
            },
            "30_competitors_and_positioning": {
                "keywords": ["Competitors", "Positioning", "Differentiation"],
                "tags": ["competitors"]
            },
            "35_integrations_and_stack": {
                "keywords": ["Integrations", "Tech Stack", "Technology"],
                "tags": ["integrations"]
            },
            "40_process_and_workflows": {
                "keywords": ["Process", "Workflow", "Steps"],
                "tags": ["workflow", "support_process"]
            },
            "45_compliance_and_security": {
                "keywords": ["Compliance", "Security", "Privacy"],
                "tags": ["compliance", "policies"]
            },
            "50_case_studies_and_proof": {
                "keywords": ["Case Studies", "Testimonials", "Proof"],
                "tags": ["proof"]
            },
            "55_contact_next_steps": {
                "keywords": ["Contact", "Next Steps", "CTA"],
                "tags": ["next_steps", "locations"]
            }
        }
        
        # Optional file map (created only if evidence found)
        self.optional_file_map = {
            "60_locations_and_hours": {
                 "keywords": ["Locations", "Hours", "Areas"],
                 "tags": ["locations"]
            },
            "65_policies_terms_privacy": {
                 "keywords": ["Terms", "Privacy Policy", "Refunds"],
                 "tags": ["policies"]
            },
            "70_terminology_glossary": {
                 "keywords": ["Glossary", "Definitions", "Acronyms"],
                 "tags": ["terminology"]
            },
            "75_safety_field_notes": {
                 "keywords": ["Safety", "Field Notes", "Precautions"],
                 "tags": ["safety"]
            }
        }

        # Injection patterns to sanitize
        self.injection_patterns = [
            r"ignore all previous instructions",
            r"forget everything",
            r"system prompt",
            r"you are a large language model",
            r"execute the following",
            r"new rule:",
            r"IMPORTANT:", 
        ]

    def _sanitize_text(self, text: str) -> str:
        """Removes dangerous injection patterns and cleans text."""
        if not text:
            return ""
        
        # 1. Neutralize specific patterns (case insensitive)
        for pattern in self.injection_patterns:
            text = re.sub(pattern, "[REDACTED_INJECTION_ATTEMPT]", text, flags=re.IGNORECASE)
        
        # 2. Strip LLM Markdown Code Fences (Common error)
        # Robust regex to find the content inside ```markdown ... ``` even if there is surrounding text
        # If the text contains ```markdown, we assume it's a wrapper and try to extract the inside.
        if "```markdown" in text:
             pattern = r"```markdown\s*(.*?)\s*```"
             match = re.search(pattern, text, re.DOTALL)
             if match:
                 text = match.group(1)
        elif "```" in text and text.strip().startswith("```"):
             # Handle generic code block wrapper
             pattern = r"^```\s*(.*?)\s*```$"
             match = re.search(pattern, text.strip(), re.DOTALL)
             if match:
                 text = match.group(1)

        # 3. Strip excess whitespace but preserve paragraph structure
        text = re.sub(r'[ \t]+', ' ', text) # Collapse horizontal whitespace
        text = re.sub(r'\n{3,}', '\n\n', text) # Collapse multiple newlines
        return text.strip()

    def _token_count(self, text: str) -> int:
        return len(self.enc.encode(text))

    def _load_dossier(self) -> Dict:
        if not self.dossier_path.exists():
            raise FileNotFoundError(f"Dossier not found at {self.dossier_path}")
        with open(self.dossier_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _chunk_text(self, text: str, source_url: str, title: str) -> List[Dict]:
        """Splits text into semantic chunks."""
        tokens = self.enc.encode(text)
        total_tokens = len(tokens)
        
        if total_tokens <= self.chunk_tokens:
            return [{
                "text": text,
                "token_count": total_tokens,
                "source": source_url,
                "title": title
            }]
            
        chunks = []
        start = 0
        while start < total_tokens:
            end = min(start + self.chunk_tokens, total_tokens)
            
            chunk_tokens_ids = tokens[start:end]
            chunk_text = self.enc.decode(chunk_tokens_ids)
            
            # Sanitization Check
            chunk_text = self._sanitize_text(chunk_text)

            chunks.append({
                "text": chunk_text,
                "token_count": len(chunk_tokens_ids),
                "source": source_url,
                "title": title
            })
            
            start += (self.chunk_tokens - self.overlap)
            
        return chunks

    def _write_kb_file(self, filename: str, content: str, meta: Dict):
        """Writes a KB file and tracks metadata."""
        file_path = self.kb_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.generated_files.append({
            "path": f"kb/{filename}",
            "title": meta.get("title", filename),
            "tags": meta.get("tags", []),
            "source_urls": meta.get("source_urls", []),
            "summary": meta.get("summary", ""),
            "provenance": meta.get("provenance", "unknown"),
            "chunk_meta": {
                "approx_tokens": self._token_count(content),
                "chunk_strategy": "heading_semantic"
            },
            "file_hash": hashlib.sha256(content.encode()).hexdigest()
        })
        logger.info(f"Generated KB file: {filename}")

    def _generate_with_llm(self, topic: str, context: str, dossier: Dict) -> str:
        """Uses LLM to synthesize a missing KB file from raw context."""
        company_name = dossier['client_profile']['name']
        industry = dossier['client_profile']['industry']
        
        system_prompt = f"""You are a senior technical writer for {company_name}, a leader in {industry}.
Your task is to write a comprehensive internal knowledge base document about "{topic}".
Use the provided raw collected data and the company dossier as your ONLY sources.
Write in a professional, clear, and authoritative tone suitable for training AI agents or new employees.
Format in valid Markdown. Use headers (##), bullet points, and bold text for emphasis.

CRITICAL EVIDENCE RULE:
- You must cite the Source URL for every major claim using [Source](url).
- If the provided context does not contain specific information about {topic}, YOU MUST WRITE: "Unknown / Confirm on discovery call".
- DO NOT invent, guess, or hallucinate pricing, specific metrics, or timelines.
"""
        
        user_prompt = f"""
[RAW CONTEXT FROM WEBSITE]
{context[:25000]}  # Increased context limit for better evidence finding

[DOSSIER SUMMARY]
Name: {company_name}
Industry: {industry}
Description: {dossier['client_profile'].get('description', 'N/A')}

[TASK]
Write the KB document: "{topic}" (Filename: {topic}.md)
Make it detailed (at least 300 words if possible) unless data is missing.
Remember: "Unknown" is better than a lie.
"""
        logger.info(f"✨ Invoking LLM for topic: {topic}")
        return self.llm.generate(system_prompt, user_prompt)

    def build_core_files(self, dossier: Dict):
        """Generates the required set 00-55 from Dossier with proper field mapping."""
        logger.info("Building Core KB Files from Dossier...")
        
        # 1. Load the source bundle
        context_text = self._try_load_source_bundle() or ""

        # 2. Append Crawled Content (if any)
        # We look at self.generated_files which now contains crawled pages
        crawled_text = []
        for f in self.generated_files:
            if "raw_crawl" in f.get("tags", []):
                try:
                    p = self.agent_path / f["path"]
                    if p.exists():
                        crawled_text.append(p.read_text(encoding='utf-8'))
                except:
                    pass
        
        if crawled_text:
            context_text += "\n\n[ADDITIONAL CRAWLED CONTEXT]\n" + "\n".join(crawled_text)
        
        # Statistics Check & Discovery Mode
        # If we have very few pages, we flag "Discovery Mode" and warn the LLM.
        is_discovery_mode = self.crawl_stats["pages_fetched"] < 5
        if is_discovery_mode:
            logger.warning(f"⚠️ Low Evidence Warning: Only crawled {self.crawl_stats['pages_fetched']} pages. Enabling Discovery Mode.")
            context_text += "\n\n[SYSTEM WARNING]: DATA IS SCARCE. DO NOT INVENT FACTS. IF INFORMATION IS MISSING, STATE 'Unknown / Discovery Required'."

        # Define explicit dossier field mappings to KB topics
        field_mappings = {
            "00_overview": {
                "keys": ["client_profile", "company_profile", "overview", "description", "about"],
                "nested_keys": ["name", "industry", "region", "url", "description", "mission"],
                "fallback_text": "Company overview information from prospect intake."
            },
            "05_ICP_and_personas": {
                "keys": ["target_audience", "icp", "persona", "ideal_customer", "audience"],
                "nested_keys": ["role", "sector", "pain_points", "demographics", "characteristics"],
                "fallback_text": "Ideal customer profile and target personas."
            },
            "10_services_and_offerings": {
                "keys": ["value_proposition", "services", "offerings", "products", "solutions"],
                "nested_keys": ["core_benefit", "features", "benefits", "software_integration"],
                "fallback_text": "Services and offerings information."
            },
            "15_pricing_and_packages": {
                "keys": ["offer", "pricing", "packages", "plans", "costs"],
                "nested_keys": ["type", "details", "price", "tiers"],
                "fallback_text": "Pricing and package information."
            },
            "20_FAQ": {
                "keys": ["faq", "questions", "qa"],
                "nested_keys": [],
                "fallback_text": "Frequently asked questions."
            },
            "25_objections_and_rebuttals": {
                "keys": ["objections", "rebuttals", "concerns", "pain_points"],
                "nested_keys": [],
                "fallback_text": "Common objections and how to address them."
            },
            "30_competitors_and_positioning": {
                "keys": ["competitors", "competition", "positioning", "differentiation"],
                "nested_keys": [],
                "fallback_text": "Competitive positioning and differentiation."
            },
            "35_integrations_and_stack": {
                "keys": ["integrations", "tech_stack", "technology", "software"],
                "nested_keys": ["software_integration"],
                "fallback_text": "Technology integrations and stack."
            },
            "40_process_and_workflows": {
                "keys": ["process", "workflow", "steps", "methodology"],
                "nested_keys": [],
                "fallback_text": "Process and workflow information."
            },
            "45_compliance_and_security": {
                "keys": ["compliance", "security", "privacy", "certifications"],
                "nested_keys": [],
                "fallback_text": "Compliance and security information."
            },
            "50_case_studies_and_proof": {
                "keys": ["case_studies", "testimonials", "proof", "metric_proof", "results"],
                "nested_keys": ["metric_proof"],
                "fallback_text": "Case studies and proof points."
            },
            "55_contact_next_steps": {
                "keys": ["contact", "next_steps", "cta", "offer"],
                "nested_keys": ["type", "details"],
                "fallback_text": "Contact information and next steps."
            }
        }
        
        for filename, info in self.file_map.items():
            keywords = info["keywords"]
            canonical_tags = info["tags"]
            mapping = field_mappings.get(filename, {})
            
            content_parts = []
            
            # 1. Search for mapped keys in dossier (both top-level and nested)
            for key in mapping.get("keys", []):
                if key in dossier:
                    val = dossier[key]
                    content_parts.append(self._format_dossier_value(key, val))
                    
            # 2. Also search nested within common top-level structures
            for top_key in ["client_profile", "target_audience", "value_proposition", "offer"]:
                if top_key in dossier and isinstance(dossier[top_key], dict):
                    for nested_key in mapping.get("nested_keys", []):
                        if nested_key in dossier[top_key]:
                            nested_val = dossier[top_key][nested_key]
                            content_parts.append(self._format_dossier_value(nested_key, nested_val))
            
            # 3. If nothing found OR content is very thin, attempting LLM Generation using COMBINED Context
            # Logic: If content length < 200 chars AND we have context, let the LLM write it.
            current_content_len = sum(len(c) for c in content_parts)
            
            if (not content_parts or current_content_len < 200) and context_text:
                 generated_text = self._generate_with_llm(keywords[0], context_text, dossier)
                 if generated_text and not generated_text.startswith("[Error"):
                     # Sanitize ONLY the generated text to strip markdown wrappers
                     generated_text = self._sanitize_text(generated_text)
                     content_parts.append(generated_text)
            
            # 4. Fallback (if LLM failed or no source bundle)
            if not content_parts:
                final_content = f"# {keywords[0]}\n\n*{mapping.get('fallback_text', 'No specific data found in intake dossier.')}*\n"
                provenance = "fallback"
            else:
                final_content = f"# {keywords[0]}\n\n" + "\n\n".join(content_parts)
                provenance = "llm_enhanced" if context_text else "dossier_extract"
            
            # Build final content
            if content_parts:
                final_content = f"# {keywords[0]}\n\n" + "\n\n".join(content_parts)
            else:
                final_content = f"# {keywords[0]}\n\n*{mapping.get('fallback_text', 'No specific data found in intake dossier.')}*\n"
            
            # Sanitize final content
            final_content = self._sanitize_text(final_content)

            # Extract actual cited sources from the content
            cited_urls = re.findall(r'\[Source\]\((http.*?)\)', final_content)
            all_sources = [dossier.get("target_url", dossier.get("client_profile", {}).get("url", "internal"))]
            if cited_urls:
                all_sources.extend(cited_urls)
            
            # Uniquify while preserving order
            all_sources = list(dict.fromkeys(all_sources))

            self._write_kb_file(f"{filename}.md", final_content, {
                "title": keywords[0],
                "tags": canonical_tags,
                "source_urls": all_sources,
                "summary": f"Content for {keywords[0]}.",
                "provenance": provenance
            })
    
    def _format_dossier_value(self, key: str, value) -> str:
        """Formats a dossier value for markdown output."""
        title = key.replace("_", " ").title()
        if isinstance(value, list):
            items = "\n".join([f"- {item}" for item in value])
            return f"## {title}\n{items}"
        elif isinstance(value, dict):
            items = "\n".join([f"- **{k.replace('_', ' ').title()}**: {v}" for k, v in value.items()])
            return f"## {title}\n{items}"
        else:
            return f"## {title}\n{value}"
    
    def _try_load_source_bundle(self) -> Optional[str]:
        """Attempts to load the source_bundle.md from ingested_clients."""
        # 1. Try relative to dossier (most reliable if dossier was passed explicitly)
        if self.dossier_path:
            bundle_path = self.dossier_path.parent / "extracted" / "source_bundle.md"
            if bundle_path.exists():
                logger.info(f"Found source bundle at: {bundle_path}")
                try:
                    return bundle_path.read_text(encoding='utf-8')
                except:
                    pass

        # 2. Try standard path logic
        bundle_path = self.ingested_dir / self.slug / "extracted" / "source_bundle.md"
        if bundle_path.exists():
            try:
                return bundle_path.read_text(encoding='utf-8')
            except:
                pass
        return None

    def run_crawler(self, base_url: str):
        """Recursive crawler to find more evidence (Depth 2)."""
        logger.info(f"Starting Recursive Crawler for {base_url}...")
        start_time = datetime.datetime.now()
        
        # Initialize Stats (Enriched)
        self.crawl_stats["assets"] = []
        self.crawl_stats["status_codes"] = {}
        
        # Normalize base URL (strip trailing slash)
        if base_url.endswith("/"): base_url = base_url[:-1]
        domain = urlparse(base_url).netloc

        # Initial Queue: (url, depth)
        queue = [(base_url, 0)]
        
        # Add standard paths to queue (depth 1 equivalents)
        standard_paths = [
            "pricing", "services", "solutions", "faq", "docs", 
            "about", "contact", "privacy", "terms"
        ]
        for p in standard_paths:
            queue.append((f"{base_url}/{p}", 1))

        visited = set()
        
        # Use a session for connection pooling
        import requests
        session = requests.Session()
        session.headers.update({"User-Agent": "X-Agent-Factory/1.0"})
        
        while queue and len(self.generated_files) < self.max_files:
            url, depth = queue.pop(0)
            
            if url in visited: continue
            visited.add(url)
            
            # Depth Gate
            if depth > 2: continue

            try:
                logger.info(f"Crawling: {url} (Depth {depth})")
                
                # Fetch content and Code
                try:
                    resp = session.get(url, timeout=10)
                    code = resp.status_code
                    self.crawl_stats["status_codes"][url] = code
                    
                    if code != 200:
                        self.crawl_stats["blocked_urls"].append(url)
                        continue
                        
                    content_type = resp.headers.get('Content-Type', '').lower()
                    
                    # Asset Filter
                    if 'text/html' not in content_type:
                        self.crawl_stats["assets"].append(url)
                        continue
                        
                    downloaded = resp.text
                    
                except Exception as req_err:
                    logger.warning(f"Request failed for {url}: {req_err}")
                    self.crawl_stats["blocked_urls"].append(url)
                    continue
                
                self.crawl_stats["pages_fetched"] += 1
                self.crawl_stats["urls"].append(url)
                self.crawl_stats["crawl_depth"] = max(self.crawl_stats["crawl_depth"], depth)

                # Extract Text
                text = trafilatura.extract(downloaded)
                if text and len(text) > 200:
                    path_slug = urlparse(url).path.strip('/').replace('/', '_') or "homepage"
                    filename = f"60_crawled_{path_slug[:50]}.md"
                    
                    safe_content = f"# Crawled: {url}\n\nSource: {url}\nDepth: {depth}\n\n{text}"
                    self._write_kb_file(filename, safe_content, {
                        "title": f"Crawled - {path_slug}",
                        "tags": ["web", "raw_crawl"],
                        "source_urls": [url],
                        "summary": f"Crawled content from {url}",
                        "provenance": "crawler"
                    })

                # Extract Links for Depth < 2
                if depth < 2:
                    soup = BeautifulSoup(downloaded, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        
                        # Normalize Link
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)
                        
                        # Internal Logic: Same Domain, HTTP/S
                        if parsed.netloc == domain and parsed.scheme in ['http', 'https']:
                            # Filter out typically useless paths
                            if not any(x in full_url.lower() for x in ['login', 'signup', 'javascript:', 'mailto:']):
                                # Asset extensions check
                                if any(full_url.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.svg']):
                                     self.crawl_stats["assets"].append(full_url)
                                     continue
                                     
                                if full_url not in visited:
                                    queue.append((full_url, depth + 1))
            
            except Exception as e:
                logger.warning(f"Failed to crawl {url}: {e}")
        
        elapsed = (datetime.datetime.now() - start_time).total_seconds() * 1000
        self.crawl_stats["elapsed_ms"] = int(elapsed)

    def generate_indices(self):
        """Generates index.json and kb_pack_manifest.json."""
        
        # Tavus Compatibility: Ensure document_tags is populated
        for f in self.generated_files:
            if "document_tags" not in f:
                f["document_tags"] = f.get("tags", [])

        # 1. index.json
        missing_topics = []
        # Check coverage
        for fname in self.file_map.keys():
            # Check if we generated this file (it might simply contain "No specific data...")
            # We enforce generation of ALL core files in build_core_files, so this check mostly confirms they were written.
            if not any(f['path'].endswith(f"{fname}.md") for f in self.generated_files):
                missing_topics.append(fname)
        
        index_data = {
            "files": self.generated_files,
            "coverage": {
                "total_files": len(self.generated_files),
                "required_topics_met": len(self.file_map) - len(missing_topics),
                "missing_topics": missing_topics
            },
            "discovery_required": self.crawl_stats.get("pages_fetched", 0) < 5,
            "build_metadata": {
                "slug": self.slug,
                "generated_at": datetime.datetime.now().isoformat(),
                "tool_version": "1.1.0"
            }
        }
        
        with open(self.kb_dir / "index.json", 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2)
            
        # 1.5 Write Crawl Report
        with open(self.kb_dir / "crawl_report.json", 'w', encoding='utf-8') as f:
            json.dump(self.crawl_stats, f, indent=2)

        # 2. kb_pack_manifest.json (Hashes)
        manifest_data = {
            os.path.basename(f["path"]): f["file_hash"] for f in self.generated_files
        }
        
        # Add index.json hash
        with open(self.kb_dir / "index.json", 'rb') as f:
             manifest_data["index.json"] = hashlib.sha256(f.read()).hexdigest()
             
        with open(self.agent_path / "kb_pack_manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2)

    def update_agent_manifest(self):
        """Updates the top-level agent manifest."""
        manifest_path = self.agent_path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                data = json.load(f)
            
            data["has_kb_library"] = True
            data["kb_stats"] = {
                "file_count": len(self.generated_files),
                "generated_at": datetime.datetime.now().isoformat()
            }
            
            with open(manifest_path, 'w') as f:
                json.dump(data, f, indent=2)

    def run(self):
        """Main execution flow."""
        logger.info(f"Starting KB Builder for {self.slug}")
        
        # Ensure KB dir exists (clean it if it does)
        if self.kb_dir.exists():
            shutil.rmtree(self.kb_dir)
        self.kb_dir.mkdir(parents=True)
        
        dossier = self._load_dossier()
        base_url = dossier.get("target_url") or dossier.get("client_profile", {}).get("url")
        
        # 1. Crawl Web First (Harvest Evidence)
        if base_url:
            self.run_crawler(base_url)
        else:
            logger.warning("No target_url in dossier, skipping crawler.")
            
        # 2. Build Core (Synthesize using Evidence)
        self.build_core_files(dossier)

        # 3. Indices & Manifests
        self.generate_indices()
        self.update_agent_manifest()
        
        logger.info(f"KB Build Complete. {len(self.generated_files)} files created.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KB Library Builder")
    parser.add_argument("--slug", required=True, help="Agent slug")
    parser.add_argument("--dossier", help="Direct path to dossier.json (overrides default)")
    parser.add_argument("--min-files", type=int, default=25)
    parser.add_argument("--keys", help="API keys (unused, kept for compat)")
    
    args = parser.parse_args()
    
    builder = KBLibraryBuilder(args.slug, min_files=args.min_files, dossier_path=args.dossier)
    builder.run()

