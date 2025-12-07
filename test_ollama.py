import requests
import json
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

url = "http://localhost:11434/api/generate"
prompt = "Analyze the pain points of Home Services dispatchers."

payload = {
    "model": "llama3",
    "prompt": prompt,
    "stream": False
}

print(f"📡 Connecting to Ollama ({url})...")
print(f"📝 Prompt: {prompt}")

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    print("\n✅ Llama 3 Response:")
    print("-" * 40)
    print(data['response'])
    print("-" * 40)
except Exception as e:
    print(f"❌ Error: {e}")
