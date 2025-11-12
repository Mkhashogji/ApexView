#!/usr/bin/env python3
"""
Generate OpenAPI JSON schema from FastAPI app.
This schema can be used to generate TypeScript types for the frontend.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


def generate_openapi_json(output_path: str = "openapi.json"):
    """
    Generate OpenAPI JSON schema and save to file.
    
    Args:
        output_path: Path to save the OpenAPI JSON file
    """
    openapi_schema = app.openapi()
    
    # Write to file with pretty formatting
    with open(output_path, 'w') as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"✓ OpenAPI schema generated: {output_path}")
    print(f"  Title: {openapi_schema.get('info', {}).get('title')}")
    print(f"  Version: {openapi_schema.get('info', {}).get('version')}")
    print(f"  Endpoints: {len(openapi_schema.get('paths', {}))}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "openapi.json"
    generate_openapi_json(output)

