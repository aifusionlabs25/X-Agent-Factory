import sys
sys.stdout.reconfigure(encoding='utf-8')
import argparse
import os
import json
import requests
from bs4 import BeautifulSoup
from utils import load_env

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

def load_specialist(name):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'specialists', f'{name}.txt')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def generate_with_ollama(persona_context, prompt):
    full_prompt = f"{persona_context}\n\n{prompt}"
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": full_prompt,
            "stream": False
        })
        response.raise_for_status()
        data = response.json()
        return data['response']
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return None

def fetch_website_content(url):
    print(f"   > 🕸️  Spidering: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        text = soup.get_text(separator=' ')
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit token count roughly
        return text[:15000] 
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

def analyze_site_with_webworker(content):
    print("   > 🔭 WebWorker: Extracting intelligence (Pricing, Hours, FAQs)...")
    persona = load_specialist("WebWorker")
    
    prompt = f"""
    [[FACTORY_MODE]]
    {persona}
    
    [WEBSITE CONTENT]
    {content}
    
    [TASK]
    Extract the following Client Data from the website content.
    Return strictly JSON.
    
    Fields required:
    1. "business_name": Name of the business.
    2. "hours": Business hours (normalized string).
    3. "pricing": Any mentioned pricing, consultation fees, or rates. If none, state "Not listed".
    4. "staff": List of names/roles found (e.g., "Dr. Smith - Veterinarian").
    5. "faqs": List of key questions and answers found.
    6. "contact_info": Phone, Email, Address.
    
    JSON Structure:
    {{
        "business_name": "...",
        "hours": "...",
        "pricing": "...",
        "staff": [],
        "faqs": [
            {{"q": "...", "a": "..."}}
        ],
        "contact_info": "..."
    }}
    [/TASK]
    """
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        })
        response.raise_for_status()
        data = response.json()
        return json.loads(data['response'])
    except Exception as e:
        print(f"❌ WebWorker Error: {e}")
        return None

def format_kb_with_troy(client_data):
    print("   > 🏗️  Troy: Formatting Knowledge Base...")
    persona = load_specialist("Troy")
    
    prompt = f"""
    [[FACTORY_MODE]]
    {persona}
    
    [CLIENT DATA]
    {json.dumps(client_data, indent=2)}
    
    [TASK]
    Format this data into a professional 'knowledge_base.txt' for a Tavus AI Agent.
    
    Structure:
    # [Client Name] Knowledge Base
    
    ## 🕒 Operating Hours
    [Hours]
    
    ## 💰 Pricing & Rates
    [Pricing]
    
    ## 👥 Key Staff
    [List of Staff]
    
    ## 📞 Contact
    [Contact Info]
    
    ## ❓ Frequently Asked Questions
    [Q&A Pairs]
    
    tags: #auto-generated #client-ingest #[industry-tag]
    [/TASK]
    """
    
    return generate_with_ollama(persona, prompt)

def ingest_client(url, output_dir=None):
    load_env()
    print(f"🚀 Client Ingest Started: {url}")
    
    # 1. Fetch
    content = fetch_website_content(url)
    if not content:
        return

    # 2. Analyze (WebWorker)
    client_data = analyze_site_with_webworker(content)
    if not client_data:
        return
        
    # 3. Format (Troy)
    kb_content = format_kb_with_troy(client_data)
    
    # 4. Save
    if not output_dir:
        biz_name = client_data.get('business_name', 'client').replace(' ', '_').lower()
        # Sanitize filename
        biz_name = "".join([c for c in biz_name if c.isalnum() or c=='_'])
        output_dir = f"ingested_clients/{biz_name}"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    kb_path = f"{output_dir}/knowledge_base.txt"
    json_path = f"{output_dir}/raw_data.json"
    
    # Save Clean KB
    if kb_content:
        clean_kb = kb_content
        if "Troy Ready." in kb_content:
            clean_kb = kb_content.split("Troy Ready.")[1].strip()
        # Strip potential markdown code blocks
        if "```" in clean_kb:
            parts = clean_kb.split("```")
            if len(parts) > 1:
                clean_kb = parts[1]
                if clean_kb.startswith("text") or clean_kb.startswith("markdown"):
                    clean_kb = clean_kb[4:].strip()
                
        with open(kb_path, 'w', encoding='utf-8') as f:
            f.write(clean_kb.strip())
            
    # Save Raw Data
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(client_data, f, indent=2)
        
    print(f"\n✅ Client Ingest Complete: {output_dir}")
    print(f"   📄 Knowledge Base: {kb_path}")
    print(f"   💾 Raw Data: {json_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client Ingest Tool")
    parser.add_argument("url", help="Client Website URL")
    parser.add_argument("--output_dir", help="Output directory", default=None)
    args = parser.parse_args()
    
    ingest_client(args.url, args.output_dir)
