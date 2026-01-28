import json
import os

path = r"c:\AI Fusion Labs\XAgents_ChatGPT_Export\conversations.json"

try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open('dojo_finds.txt', 'w', encoding='utf-8') as outfile:
        outfile.write(f"Loaded {len(data)} conversations.\n")
        
        found_convs = set()
        
        for conv in data:
            title = conv.get('title')
            if not title: title = "No Title"
            
            mapping = conv.get('mapping')
            if not mapping: continue
                
            full_text = ""
            for node_id, node in mapping.items():
                if not node: continue
                message = node.get('message')
                if not message: continue
                content = message.get('content')
                if not content: continue
                
                parts = content.get('parts')
                if not parts: continue
                
                for p in parts:
                    if isinstance(p, str):
                        full_text += p + " "
                    elif isinstance(p, dict):
                        full_text += str(p) + " "
            
            if 'Antigravity' in full_text:
                if title not in found_convs:
                    outfile.write(f"\n--- MATCH: {title} ---\n")
                    idx = full_text.find('Antigravity')
                    snippet = full_text[max(0, idx-100):min(len(full_text), idx+100)].replace('\n', ' ')
                    outfile.write(f"Snippet: ...{snippet}...\n")
                    found_convs.add(title)

    print("Search complete. Check dojo_finds.txt")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
