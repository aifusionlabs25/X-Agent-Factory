import json
import os
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python grok_loader.py <path_to_json>")
        return

    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"✅ successfully loaded {len(data)} leads from {filepath}")
        # In a real scenario, this might push to DB or transform fields.
        # For now, it validates JSON integrity.
        for lead in data:
            print(f"- Found: {lead.get('company_name')} ({lead.get('vertical')})")
            
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")

if __name__ == "__main__":
    main()
