"""
Lead Enrichment Pipeline
Orchestrates WebWorker, Nova, Fin, and Sparkle to build a complete lead dossier.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import argparse
import os
import json
import requests
import time
import re
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

def generate_with_ollama(persona_context, prompt, model="llama3"):
    full_prompt = f"{persona_context}\n\n{prompt}"
    try:
        response = requests.post(OLLAMA_URL, json={
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

def generate_with_gemini(persona_context, prompt):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None

    full_prompt = f"{persona_context}\n\n{prompt}"
    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{GEMINI_URL}?key={api_key}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if response.status_code == 429:
                print(f"   ⚠️ Gemini Rate Limit. Waiting {2 * (attempt + 1)}s...")
                time.sleep(2 * (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"   ⚠️ Gemini Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    return None

# ============================================================
# STAGE 1: WEBWORKER - Technical Spider
# ============================================================
def webworker_enrich(url):
    print(f"   > 🕷️  WebWorker: Spidering {url}...")
    
    result = {
        "has_online_booking": False,
        "google_reviews_score": 0.0,
        "google_reviews_count": 0,
        "detected_tools": [],
        "social_links": {
            "facebook": None,
            "instagram": None,
            "linkedin": None,
            "twitter": None
        },
        "phone_prominent": False,
        "email_found": None,
        "raw_text_preview": ""
    }
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ').lower()
        html = response.text.lower()
        
        result["raw_text_preview"] = text[:2000]
        
        # Detect Online Booking
        booking_signals = ['book online', 'schedule online', 'book now', 'schedule appointment', 
                          'calendly', 'acuity', 'square appointments', 'booksy', 'schedulista']
        result["has_online_booking"] = any(signal in text for signal in booking_signals)
        
        # Detect CRM/Tools
        tools_patterns = {
            'ServiceTitan': ['servicetitan', 'service titan'],
            'Housecall Pro': ['housecallpro', 'housecall pro'],
            'Jobber': ['jobber'],
            'HubSpot': ['hubspot', 'hs-script'],
            'Salesforce': ['salesforce', 'pardot'],
            'Zendesk': ['zendesk'],
            'Intercom': ['intercom'],
            'Drift': ['drift.com', 'driftt'],
            'LiveChat': ['livechat'],
            'Calendly': ['calendly'],
            'HeyGen': ['heygen'],
            'Tavus': ['tavus'],
            'ChatGPT': ['chatgpt', 'openai']
        }
        
        for tool, patterns in tools_patterns.items():
            if any(p in html for p in patterns):
                result["detected_tools"].append(tool)
        
        # Extract Social Links
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if 'facebook.com' in href:
                result["social_links"]["facebook"] = link['href']
            elif 'instagram.com' in href:
                result["social_links"]["instagram"] = link['href']
            elif 'linkedin.com' in href:
                result["social_links"]["linkedin"] = link['href']
            elif 'twitter.com' in href or 'x.com' in href:
                result["social_links"]["twitter"] = link['href']
        
        # Check if phone is prominent (in header/hero)
        phone_pattern = r'[\(]?\d{3}[\)]?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text[:500])
        result["phone_prominent"] = len(phones) > 0
        
        # Extract email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        if emails:
            result["email_found"] = emails[0]
            
    except Exception as e:
        print(f"   ⚠️ Spider failed: {e}")
    
    return result

# ============================================================
# STAGE 2: NOVA - Competitive Analysis
# ============================================================
def nova_analyze(webworker_data, lead_title):
    print(f"   > 💠 Nova: Analyzing competitive landscape...")
    persona = load_specialist("Nova")
    
    prompt = f"""
    [[FACTORY_MODE]]
    {persona}
    
    [LEAD DATA]
    Business: {lead_title}
    Has Online Booking: {webworker_data.get('has_online_booking')}
    Detected Tools: {webworker_data.get('detected_tools')}
    Phone Prominent: {webworker_data.get('phone_prominent')}
    Social Presence: {[k for k, v in webworker_data.get('social_links', {}).items() if v]}
    
    [TASK]
    Analyze this lead for sales potential.
    
    Return JSON ONLY:
    {{
        "competition_risk": <1-10, 10 = already using advanced AI/CRM>,
        "competition_notes": "What tools are they using?",
        "growth_signal": <1-10, 10 = high growth indicators>,
        "growth_notes": "Active website, social presence, etc.",
        "final_priority": "A" or "B" or "C",
        "priority_reason": "Why this rating?"
    }}
    [/TASK]
    """
    
    return generate_with_ollama(persona, prompt)

# ============================================================
# STAGE 3: FIN - Sales Strategy
# ============================================================
def fin_strategize(nova_data, webworker_data, pain_point=""):
    print(f"   > 💼 Fin: Developing sales approach...")
    persona = load_specialist("Fin")
    
    prompt = f"""
    [[FACTORY_MODE]]
    {persona}
    
    [LEAD ANALYSIS]
    Priority: {nova_data.get('final_priority', 'B')}
    Competition Risk: {nova_data.get('competition_risk', 5)}/10
    Growth Signal: {nova_data.get('growth_signal', 5)}/10
    Has Booking: {webworker_data.get('has_online_booking')}
    Phone Prominent: {webworker_data.get('phone_prominent')}
    Known Pain Point: {pain_point}
    
    [TASK]
    Develop a sales approach for this lead.
    
    Return JSON ONLY:
    {{
        "recommended_approach": "Direct Demo" or "Warm Intro" or "Nurture" or "Pass",
        "approach_reason": "Why this approach?",
        "objection_prediction": "What will they likely object to?",
        "objection_handler": "How to overcome it?",
        "best_time_to_call": "Morning/Afternoon/Evening",
        "decision_maker_likely": "Owner/Manager/Front Desk"
    }}
    [/TASK]
    """
    
    return generate_with_ollama(persona, prompt)

# ============================================================
# STAGE 4: SPARKLE - Outreach Copy
# ============================================================
def sparkle_compose(lead_title, pain_point, fin_data, demo_link=""):
    print(f"   > ✨ Sparkle: Composing outreach copy...")
    persona = load_specialist("Sparkle")
    
    prompt = f"""
    [[GHOST_MODE]]
    [[FACTORY_MODE]]
    {persona}
    
    [LEAD INFO]
    Business: {lead_title}
    Pain Point: {pain_point}
    Recommended Approach: {fin_data.get('recommended_approach', 'Direct Demo')}
    Predicted Objection: {fin_data.get('objection_prediction', 'Budget')}
    Demo Link: {demo_link or '[DEMO_LINK]'}
    
    [TASK]
    Write a cold outreach email. Be punchy. No fluff.
    
    Return JSON ONLY:
    {{
        "email_subject": "Subject line (max 50 chars)",
        "email_body": "3 sentences MAX. Include the pain point and demo link.",
        "linkedin_message": "2 sentences for LinkedIn DM"
    }}
    [/TASK]
    """
    
    return generate_with_ollama(persona, prompt)

# ============================================================
# ORCHESTRATOR
# ============================================================
def enrich_lead(url, lead_title, pain_point="", demo_link=""):
    load_env()
    print(f"\n🔬 LEAD ENRICHMENT PIPELINE")
    print(f"   Target: {lead_title}")
    print("="*50)
    
    enriched = {
        "url": url,
        "lead_title": lead_title,
        "pain_point": pain_point,
        "demo_link": demo_link,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "webworker": {},
        "nova": {},
        "fin": {},
        "sparkle": {}
    }
    
    # Stage 1: WebWorker
    enriched["webworker"] = webworker_enrich(url)
    
    # Stage 2: Nova
    nova_result = nova_analyze(enriched["webworker"], lead_title)
    if nova_result:
        enriched["nova"] = nova_result
    
    # Stage 3: Fin
    fin_result = fin_strategize(enriched.get("nova", {}), enriched["webworker"], pain_point)
    if fin_result:
        enriched["fin"] = fin_result
    
    # Stage 4: Sparkle
    sparkle_result = sparkle_compose(lead_title, pain_point, enriched.get("fin", {}), demo_link)
    if sparkle_result:
        enriched["sparkle"] = sparkle_result
    
    # Save
    slug = lead_title.lower()
    slug = re.sub(r'[^a-z0-9\s]', '', slug).strip().replace(' ', '_')[:50]
    
    output_dir = "intelligence/leads"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"{slug}_enriched.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, indent=2)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"✅ ENRICHMENT COMPLETE")
    print(f"   📁 Saved to: {output_path}")
    print(f"   📊 Priority: {enriched.get('nova', {}).get('final_priority', 'N/A')}")
    print(f"   🎯 Approach: {enriched.get('fin', {}).get('recommended_approach', 'N/A')}")
    if enriched.get('sparkle', {}).get('email_subject'):
        print(f"   📧 Subject: {enriched['sparkle']['email_subject']}")
    
    return enriched

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lead Enrichment Pipeline")
    parser.add_argument("url", help="Lead's website URL")
    parser.add_argument("--title", default="Unknown Business", help="Lead's business name")
    parser.add_argument("--pain", default="", help="Known pain point")
    parser.add_argument("--demo", default="", help="Demo link if available")
    args = parser.parse_args()
    
    enrich_lead(args.url, args.title, args.pain, args.demo)
