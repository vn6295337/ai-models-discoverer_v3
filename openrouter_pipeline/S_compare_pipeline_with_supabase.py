#!/usr/bin/env python3
"""
Pipeline vs Supabase Field Comparison
Compares field values between R_filtered_db_data.json and Supabase working_version table
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not found. Install with: pip install supabase")
    exit(1)

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        current_env = Path(__file__).parent / ".env"
        if current_env.exists():
            load_dotenv(current_env)
except ImportError:
    pass

# Configuration
PIPELINE_DATA_FILE = Path(__file__).parent / "pipeline-outputs" / "R_filtered_db_data.json"
REPORT_FILE = Path(__file__).parent / "S-field-comparison-report.txt"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
TABLE_NAME = "working_version"
INFERENCE_PROVIDER = "OpenRouter"

def get_supabase_client() -> Optional[Client]:
    """Initialize Supabase client"""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        return None

    try:
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return client
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        return None

def load_pipeline_data() -> List[Dict[str, Any]]:
    """Load pipeline data from R_filtered_db_data.json"""
    try:
        with open(PIPELINE_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} models from pipeline data")
        return data
    except Exception as e:
        print(f"Failed to load pipeline data: {e}")
        return []

def load_supabase_data(client: Client) -> List[Dict[str, Any]]:
    """Load OpenRouter data from Supabase working_version table"""
    try:
        response = client.table(TABLE_NAME).select("*").eq("inference_provider", INFERENCE_PROVIDER).execute()
        data = response.data if response.data else []
        print(f"Loaded {len(data)} models from Supabase")
        return data
    except Exception as e:
        print(f"Failed to load Supabase data: {e}")
        return []

def create_comparison_report(pipeline_data: List[Dict[str, Any]], supabase_data: List[Dict[str, Any]]):
    """Generate field comparison report"""

    # Create lookup dictionaries by human_readable_name
    pipeline_lookup = {model.get('human_readable_name', ''): model for model in pipeline_data}
    supabase_lookup = {model.get('human_readable_name', ''): model for model in supabase_data}

    # Get all unique model names
    all_model_names = set(pipeline_lookup.keys()) | set(supabase_lookup.keys())
    all_model_names.discard('')  # Remove empty names

    # Fields to compare (excluding auto-managed fields)
    fields_to_compare = [
        'inference_provider',
        'model_provider',
        'human_readable_name',
        'model_provider_country',
        'official_url',
        'input_modalities',
        'output_modalities',
        'license_info_text',
        'license_info_url',
        'license_name',
        'license_url',
        'rate_limits',
        'provider_api_access'
    ]

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("FIELD COMPARISON REPORT: PIPELINE vs SUPABASE\n")
        f.write("=" * 80 + "\n\n")

        for model_name in sorted(all_model_names):
            pipeline_model = pipeline_lookup.get(model_name, {})
            supabase_model = supabase_lookup.get(model_name, {})

            f.write(f"MODEL: {model_name}\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Field Name':<25} | {'Pipeline Value':<25} | {'Supabase Value':<25}\n")
            f.write("-" * 80 + "\n")

            for field in fields_to_compare:
                pipeline_value = str(pipeline_model.get(field, '')).strip()
                supabase_value = str(supabase_model.get(field, '')).strip()

                # Truncate long values for display
                pipeline_display = pipeline_value[:23] + ".." if len(pipeline_value) > 25 else pipeline_value
                supabase_display = supabase_value[:23] + ".." if len(supabase_value) > 25 else supabase_value

                f.write(f"{field:<25} | {pipeline_display:<25} | {supabase_display:<25}\n")

            f.write("\n" + "=" * 80 + "\n\n")

def main():
    """Main execution function"""
    print("Starting field comparison...")

    # Load pipeline data
    pipeline_data = load_pipeline_data()
    if not pipeline_data:
        print("No pipeline data loaded")
        return False

    # Connect to Supabase and load data
    client = get_supabase_client()
    if not client:
        print("Failed to connect to Supabase")
        return False

    supabase_data = load_supabase_data(client)

    # Generate comparison report
    create_comparison_report(pipeline_data, supabase_data)

    print(f"Comparison report saved to: {REPORT_FILE}")
    return True

if __name__ == "__main__":
    main()