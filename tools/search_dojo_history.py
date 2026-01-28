import json
import os

path = r"c:\AI Fusion Labs\XAgents_ChatGPT_Export\conversations.json"

try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} conversations.")
    
    found_count = 0
    for conv in data:
        title = conv.get('title', 'No Title')
        found_in_conv = False
        
        # Check title
        if 'Dojo' in title:
            print(f"\n--- FOUND IN TITLE: {title} ---")
            found_in_conv = True
            
        # Check mapping
        mapping = conv.get('mapping', {})
        for node_id, node in mapping.items():
            message = node.get('message')
            if message:
                content = message.get('content', {})
                parts = content.get('parts', [])
                if parts is None:
                    parts = []
                text = " ".join([str(p) for p in parts])
                
                if 'Dojo' in text:
                    if not found_in_conv:
                        print(f"\n--- FOUND IN CONVERSATION: {title} ---")
                        found_in_conv = True
                    
                    # Print snippet
                    idx = text.find('Dojo')
                    snippet = text[max(0, idx-50):min(len(text), idx+100)]
                    print(f"Snippet: ...{snippet}...")
                    found_count += 1
                    if found_count > 10: break
        
        if found_count > 10: break

except Exception as e:
    print(f"Error: {e}")
