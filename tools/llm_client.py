import os
import requests
import json
from dotenv import load_dotenv

# Load env immediately upon import to ensure keys are ready
load_dotenv('.env')
load_dotenv('.env.local')

class LLMClient:
    def __init__(self, provider="openai", model="gpt-4o"):
        self.provider = provider
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        if self.provider == "openai" and not self.api_key:
            print("⚠️ [LLMClient] Warning: OPENAI_API_KEY not found in environment.")

    def generate(self, system_prompt: str, user_prompt: str, temperature=0.7) -> str:
        """
        Generates text using the configured LLM provider.
        """
        if self.provider == "openai":
            return self._generate_openai(system_prompt, user_prompt, temperature)
        elif self.provider == "ollama":
            return self._generate_ollama(system_prompt, user_prompt, temperature)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _generate_openai(self, system_prompt, user_prompt, temperature):
        if not self.api_key:
            return "[Error: Missing OpenAI API Key]"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 4096
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"❌ [LLMClient] OpenAI Error: {e}")
            return f"[Error generating content: {e}]"

    def _generate_ollama(self, system_prompt, user_prompt, temperature):
        # Placeholder for Phase 27
        # Would POST to http://localhost:11434/api/chat
        pass

# Simple test if run directly
if __name__ == "__main__":
    client = LLMClient()
    print("Testing connection...")
    response = client.generate("You are a helpful assistant.", "Say hello to the factory operator.")
    print(f"Response: {response}")
