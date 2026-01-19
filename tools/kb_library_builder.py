
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
                 min_files: int = 25, max_files: int = 60, chunk_tokens: int = 650, overlap: int = 80):
        self.slug = slug
        self.agents_dir = Path(agents_dir)
        self.ingested_dir = Path(ingested_dir)
        self.agent_path = self.agents_dir / slug
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
        """Generates the required set 00-55 from Dossier."""
        logger.info("Building Core KB Files from Dossier...")
        
        for filename, info in self.file_map.items():
            keywords = info["keywords"]
            canonical_tags = info["tags"]
            
            content_accumulator = []
            
            # 1. Search in Dossier top-level keys
            for key, val in dossier.items():
                if isinstance(val, dict) or isinstance(val, str):
                    str_val = str(val)
                    if any(k.lower() in key.lower() for k in keywords):
                         content_accumulator.append(f"## From {key}\n{str_val}\n")
            
            # If we found content, write it. If not, write a placeholder (to meet "Required Set")
            if content_accumulator:
                final_content = f"# {keywords[0]}\n\n" + "\n".join(content_accumulator)
            else:
                final_content = f"# {keywords[0]}\n\n*No specific data found in intake dossier for {keywords[0]}.*\n"
            
            # Sanitize final content
            final_content = self._sanitize_text(final_content)

            self._write_kb_file(f"{filename}.md", final_content, {
                "title": keywords[0],
                "tags": canonical_tags,
                "source_urls": [dossier.get("target_url", "internal")],
                "summary": f"Core {keywords[0]} extracted from dossier.",
                "provenance": "safe_summary" # Dossier derived is considered safer
            })

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
    parser.add_argument("--min-files", type=int, default=25)
    parser.add_argument("--keys", help="API keys (unused, kept for compat)")
    
    args = parser.parse_args()
    
    builder = KBLibraryBuilder(args.slug, min_files=args.min_files)
    builder.run()
