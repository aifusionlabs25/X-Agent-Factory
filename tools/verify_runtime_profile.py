import os
import sys
import argparse
import json

def load_env_file(filepath):
    """Simple .env loader to avoid dependencies if python-dotenv is missing."""
    env_vars = {}
    if os.path.exists(filepath):
        print(f"  [INFO] Loading secrets from {filepath}...")
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def verify_runtime_profile(client_slug):
    print(f"--- Running Runtime Verify (G15) for {client_slug} ---")
    
    base_dir = f"agents/clients/{client_slug}"
    profile_path = os.path.join(base_dir, "runtime_profile.json")
    
    # 0. Load Secrets Source
    # Priority: OS Environment > dashboard/.env.local
    dashboard_env_path = "dashboard/.env.local"
    local_secrets = load_env_file(dashboard_env_path)
    
    # 1. Check File Existence
    if not os.path.exists(profile_path):
        print(f"  [FAIL] runtime_profile.json missing at {profile_path}")
        print("  Run the Runtime Configuration in Dashboard to generate this.")
        sys.exit(1)

    try:
        with open(profile_path, 'r') as f:
            profile = json.load(f)
    except Exception as e:
        print(f"  [FAIL] JSON Decode Error: {e}")
        sys.exit(1)

    failures = []

    # 2. Check Schema Basics
    if profile.get("agent_slug") != client_slug:
         failures.append(f"agent_slug mismatch (Expected {client_slug}, got {profile.get('agent_slug')})")

    providers = profile.get("providers", {})
    secrets_map = profile.get("secrets", {})

    # 3. Provider Checks: Tavus
    tavus = providers.get("tavus", {})
    if tavus.get("enabled"):
        print("  [CHECK] Tavus Enabled")
        # Strict fields (G15.1)
        if not tavus.get("persona_id"):
            failures.append("Tavus enabled but 'persona_id' is empty.")
        if not tavus.get("replica_id"):
            failures.append("Tavus enabled but 'replica_id' is empty.")
        if not tavus.get("key_name"):
            failures.append("Tavus enabled but 'key_name' is empty (Required in V2).")
            
        # Check Secret
        ref = tavus.get("api_key_ref")
        if ref and ref.startswith("ENV:"):
            env_var = ref.split("ENV:")[1]
            # Check in OS or Local env
            if os.environ.get(env_var) or local_secrets.get(env_var):
                print(f"    [OK] Secret {env_var} found.")
            else:
                failures.append(f"Missing Secret: {env_var} (Required for Tavus)")
        else:
             failures.append(f"Invalid/Missing API Key Ref for Tavus.")

    # 4. Provider Checks: TTS (V2)
    tts = providers.get("tts", {})
    if tts.get("enabled"):
        print("  [CHECK] TTS Enabled")
        
        if not tts.get("engine"):
            failures.append("TTS enabled but 'engine' is empty.")
        if not tts.get("external_voice_id"):
            failures.append("TTS enabled but 'external_voice_id' is empty.")
        if not tts.get("voice_settings_preset"):
             failures.append("TTS enabled but 'voice_settings_preset' is empty.")

        # Check Secret
        ref = tts.get("api_key_ref")
        if ref and ref.startswith("ENV:"):
            env_var = ref.split("ENV:")[1]
             # Check in OS or Local env
            if os.environ.get(env_var) or local_secrets.get(env_var):
                print(f"    [OK] Secret {env_var} found.")
            else:
                failures.append(f"Missing Secret: {env_var} (Required for TTS)")
        else:
            failures.append(f"Invalid/Missing API Key Ref for TTS.")

    if failures:
        print("\n[FAIL] Runtime Verification Failed:")
        for fail in failures:
            print(f"  - {fail}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Runtime Profile Valid & runnable.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True)
    args = parser.parse_args()
    verify_runtime_profile(args.client)
