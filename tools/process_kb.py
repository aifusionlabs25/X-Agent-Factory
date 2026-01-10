#!/usr/bin/env python3
"""
KB Processor - Consolidate and format research data for Tavus
Usage: python process_kb.py --agent luna_veterinary
"""

import os
import json
import glob
import re
from pathlib import Path
from datetime import datetime

AGENT_ID = "luna_veterinary"
# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH_DIR = os.path.join(BASE_DIR, "intelligence", "research")
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
OUTPUT_DIR = os.path.join(AGENTS_DIR, AGENT_ID, "knowledge_base")

def clean_text(text):
    """Remove excessive whitespace and noise"""
    if not text:
        return ""
    # condensed whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_research():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting KB Processing for {AGENT_ID}")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Find all research folders
    research_folders = glob.glob(os.path.join(RESEARCH_DIR, "batch_*")) + \
                      glob.glob(os.path.join(RESEARCH_DIR, "research_*"))
    
    print(f"Found {len(research_folders)} research folders")
    
    processed_urls = set()
    total_files = 0
    skipped_dupes = 0
    skipped_empty = 0
    
    # Processing stats per topic/folder could be useful, 
    # but we'll categorize by the query if possible, or just keep original filenames.
    
    for folder in research_folders:
        folder_name = os.path.basename(folder)
        # Try to find summary to identify topic
        summary_path = os.path.join(folder, "_summary.json")
        topic_tag = "general"
        
        if os.path.exists(summary_path):
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                    query = summary.get('query', '')
                    # Create a short tag from query
                    words = query.split()
                    if words:
                        topic_tag = "-".join(words[:3]).lower()
                        topic_tag = re.sub(r'[^a-z0-9-]', '', topic_tag)
            except:
                pass
        
        # Process JSON files
        json_files = glob.glob(os.path.join(folder, "*.json"))
        
        for json_file in json_files:
            if json_file.endswith("_summary.json"):
                continue
                
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                url = data.get('url', '')
                content = data.get('content', '')
                title = data.get('title', 'Untitled')
                
                # Deduplication check
                if url in processed_urls:
                    skipped_dupes += 1
                    continue
                
                if not content or len(content) < 200:
                    skipped_empty += 1
                    continue
                
                processed_urls.add(url)
                
                # Format for Tavus KB
                # We'll create a structured text file
                output_filename = f"{topic_tag}_{os.path.basename(json_file).replace('.json', '.txt')}"
                # Sanitize filename
                output_filename = re.sub(r'[^\w\-\.]', '_', output_filename)
                
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {title}\n")
                    f.write(f"Source: {url}\n")
                    f.write(f"Topic: {topic_tag}\n")
                    f.write("="*50 + "\n\n")
                    f.write(clean_text(content))
                
                total_files += 1
                
            except Exception as e:
                print(f"Error processing {json_file}: {e}")

    print(f"\nProcessing Complete!")
    print(f"Total Unique Files Created: {total_files}")
    print(f"Duplicates Skipped: {skipped_dupes}")
    print(f"Low Quality/Empty Skipped: {skipped_empty}")
    print(f"Output Directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    process_research()
