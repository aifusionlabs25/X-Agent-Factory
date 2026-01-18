"""
Schema Validator
Validates a JSON dossier against the official X Agent Factory schema.
"""
import json
import sys
import argparse
from pathlib import Path
from jsonschema import validate, ValidationError

def validate_dossier(dossier_path, schema_path=None):
    """
    Validate a dossier JSON file against the schema.
    Returns (True, None) if valid, (False, error_message) if invalid.
    """
    try:
        # Load Dossier
        with open(dossier_path, 'r', encoding='utf-8') as f:
            dossier = json.load(f)
            
        # Load Schema (default to docs/dossier_schema.json)
        if schema_path is None:
            schema_path = Path(__file__).parent.parent / "docs" / "dossier_schema.json"
            
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
            
        # Validate
        validate(instance=dossier, schema=schema)
        return True, None
        
    except FileNotFoundError as e:
        return False, f"File not found: {e.filename}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except ValidationError as e:
        return False, f"Schema Validation Error: {e.message} at {list(e.path)}"
    except Exception as e:
        return False, f"Unexpected Error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Validate a Client Dossier JSON")
    parser.add_argument("dossier", help="Path to the dossier.json file")
    parser.add_argument("--schema", help="Path to schema (optional)", default=None)
    
    args = parser.parse_args()
    
    print(f"🔍 Validating: {args.dossier}")
    valid, error = validate_dossier(args.dossier, args.schema)
    
    if valid:
        print("✅ Dossier is Valid.")
        sys.exit(0)
    else:
        print(f"❌ Validation Failed:\n{error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
