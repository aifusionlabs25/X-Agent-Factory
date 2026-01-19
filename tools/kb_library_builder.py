
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
        self.generated_files: List[Dict] = [] # Track file metadata

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
        
        # 2. Strip excess whitespace but preserve paragraph structure
        # (Replacing naive implementation to keep newlines for semantic chunking)
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

    def build_core_files(self, dossier: Dict):
        """Generates the required set 00-55 from Dossier with proper field mapping."""
        logger.info("Building Core KB Files from Dossier...")
        
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
            
            # 3. If nothing found, use the kb_seed.md or source_bundle as fallback
            if not content_parts:
                source_bundle = self._try_load_source_bundle()
                if source_bundle and any(k.lower() in source_bundle.lower() for k in keywords):
                    # Extract relevant section from source bundle
                    for keyword in keywords:
                        patterns = [
                            rf"#{1,3}\s*{keyword}.*?(?=#{1,3}|\Z)",
                            rf"\*\*{keyword}\*\*.*?(?=\*\*|\n\n|\Z)",
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, source_bundle, re.IGNORECASE | re.DOTALL)
                            if match:
                                content_parts.append(f"## From Website Content\n{match.group(0).strip()}")
                                break
            
            # Build final content
            if content_parts:
                final_content = f"# {keywords[0]}\n\n" + "\n\n".join(content_parts)
            else:
                final_content = f"# {keywords[0]}\n\n*{mapping.get('fallback_text', 'No specific data found in intake dossier.')}*\n"
            
            # Sanitize final content
            final_content = self._sanitize_text(final_content)

            self._write_kb_file(f"{filename}.md", final_content, {
                "title": keywords[0],
                "tags": canonical_tags,
                "source_urls": [dossier.get("target_url", dossier.get("client_profile", {}).get("url", "internal"))],
                "summary": f"Core {keywords[0]} extracted from dossier.",
                "provenance": "safe_summary"
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
        bundle_path = self.ingested_dir / self.slug / "extracted" / "source_bundle.md"
        if bundle_path.exists():
            try:
                return bundle_path.read_text(encoding='utf-8')
            except:
                pass
        return None

    def run_crawler(self, base_url: str):
        """Crawls standard paths to augment KB."""
        logger.info(f"Starting Crawler for {base_url}...")
        
        paths = [
            "pricing", "services", "solutions", "industries", "faq", "docs", 
            "blog", "case-studies", "about", "contact", "security", "terms", "privacy",
            "careers", "team"
        ]
        
        # Normalize base URL (strip trailing slash)
        if base_url.endswith("/"): base_url = base_url[:-1]

        for path in paths:
             # Stop if we hit max files
            if len(self.generated_files) >= self.max_files:
                logger.warning("Max KB files reached. Stopping crawler.")
                break

            target_url = f"{base_url}/{path}"
            try:
                # Basic Rate Limiting sleep could go here
                
                downloaded = trafilatura.fetch_url(target_url)
                if downloaded:
                    text = trafilatura.extract(downloaded)
                    if text and len(text) > 200: # Min content filter
                        # Chunk it
                        chunks = self._chunk_text(text, target_url, path.capitalize())
                        
                        for i, chunk in enumerate(chunks):
                             if len(self.generated_files) >= self.max_files: break
                             
                             filename = f"60_crawled_{path}_part{i+1}.md"
                             safe_content = f"# {path.capitalize()} (Part {i+1})\n\nSource: {target_url}\n\n{chunk['text']}"
                             
                             self._write_kb_file(filename, safe_content, {
                                 "title": f"{path.capitalize()} - Part {i+1}",
                                 "tags": ["web", path.lower()],
                                 "source_urls": [target_url],
                                 "summary": f"Crawled content from {path}"
                             })
            except Exception as e:
                logger.warning(f"Failed to crawl {target_url}: {e}")

    def generate_indices(self):
        """Generates index.json and kb_pack_manifest.json."""
        
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
            "build_metadata": {
                "slug": self.slug,
                "generated_at": datetime.datetime.now().isoformat(),
                "tool_version": "1.1.0"
            }
        }
        
        with open(self.kb_dir / "index.json", 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2)
            
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
        base_url = dossier.get("target_url")
        
        # 1. Build Core (Required)
        self.build_core_files(dossier)
        
        # 2. Crawl Web (Augment)
        if base_url:
            self.run_crawler(base_url)
        else:
            logger.warning("No target_url in dossier, skipping crawler.")

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

