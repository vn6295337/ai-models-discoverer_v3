#!/usr/bin/env python3
"""
HuggingFace API Models Fetcher with Pre-fetch Filtering
Fetches generative AI models from HuggingFace API with server-side filtering and saves to compact JSON format

Pre-fetch filters applied (from 02_prefetch_filters.json):
- pipeline_tag: Filter for generative AI modalities (text-generation, text-to-image, etc.)
- gated: Only ungated models (no access restrictions)
- inference: Only models with free Inference API (warm/cold)

Outputs: Compact JSON file with deduplicated filtered models
"""
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path

import requests

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_paths = [
        Path("/home/km_project/.env"),
        Path(__file__).parent.parent.parent / ".env.local",
        Path(__file__).parent.parent / ".env"
    ]

    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"Loaded environment from: {env_path}")
            break
    else:
        print("No .env file found in expected locations")
except ImportError:
    print("Warning: python-dotenv not available, using system environment variables")

def ensure_output_dir_exists():
    """Create output directory if it doesn't exist"""
    output_dir = Path(__file__).parent.parent / "02_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def get_output_file_path(filename: str) -> Path:
    """Get full path for output file"""
    output_dir = ensure_output_dir_exists()
    return output_dir / filename

def load_api_configuration() -> Dict[str, Any]:
    """Load API configuration from 01_api_configuration.json"""
    config_file = Path(__file__).parent.parent / "03_configs" / "01_api_configuration.json"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"WARNING: Failed to load API configuration from {config_file}: {error}")
        print("Using hardcoded fallback values")
        return {}

def load_exclude_keys() -> List[str]:
    """Load exclude keys from 04_postfetch_field_removal.json"""
    config_file = Path(__file__).parent.parent / "03_configs" / "04_postfetch_field_removal.json"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('common_exclude_keys', [])
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"WARNING: Failed to load exclude keys from {config_file}: {error}")
        print("Using hardcoded fallback values")
        return ['spaces', 'siblings', 'widgetData']

def load_prefetch_filters() -> Dict[str, Any]:
    """Load pre-fetch filters from 02_prefetch_filters.json"""
    config_file = Path(__file__).parent.parent / "03_configs" / "02_prefetch_filters.json"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('active_filters', {})
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"WARNING: Failed to load prefetch filters from {config_file}: {error}")
        print("Using no prefetch filters")
        return {}

def fetch_all_huggingface_models() -> List[Dict[str, Any]]:
    """
    Fetch models from HuggingFace API with pre-fetch filters applied

    Returns:
        List of filtered model dictionaries from API
    """
    # Get API key
    hf_token = os.getenv('HUGGINGFACE_API_KEY')
    if not hf_token:
        print("WARNING: HUGGINGFACE_API_KEY not found, proceeding without authentication")

    # Load configurations
    config = load_api_configuration()
    exclude_keys = load_exclude_keys()
    prefetch_filters = load_prefetch_filters()

    # Extract configuration values with fallbacks
    base_url = config.get('api_endpoints', {}).get('models_list', 'https://huggingface.co/api/models')
    timeout = config.get('request_parameters', {}).get('timeout', 30)

    # Pagination parameters
    pagination = config.get('pagination', {})
    limit = pagination.get('limit', 500)
    full = pagination.get('full', True)

    # Build filter parameters
    filter_params = {}

    # Apply gated filter if enabled
    if prefetch_filters.get('gated', {}).get('enabled'):
        gated_value = prefetch_filters['gated'].get('value')
        filter_params['gated'] = str(gated_value).lower()
        print(f"Applying pre-fetch filter: gated={gated_value}")

    # Get pipeline_tag values for iteration
    pipeline_tag_filter = prefetch_filters.get('pipeline_tag', {})
    pipeline_tags = []
    if pipeline_tag_filter.get('enabled'):
        pipeline_tags = pipeline_tag_filter.get('values', [])
        print(f"Applying pre-fetch filter: pipeline_tag in {pipeline_tags}")

    # Get inference values
    inference_filter = prefetch_filters.get('inference', {})
    inference_values = []
    if inference_filter.get('enabled'):
        inference_values = inference_filter.get('values', [])
        print(f"Applying pre-fetch filter: inference in {inference_values}")

    all_models = []
    seen_model_ids = set()  # Track unique models to avoid duplicates

    try:
        print("Fetching HuggingFace models from API with pre-fetch filters...")

        headers = {}
        if hf_token:
            headers['Authorization'] = f'Bearer {hf_token}'

        # If we have pipeline_tag filters, fetch for each tag separately
        # Otherwise, fetch all models once
        tags_to_fetch = pipeline_tags if pipeline_tags else [None]

        # If we have inference filters, fetch for each value separately
        # Otherwise, fetch all models once
        inference_to_fetch = inference_values if inference_values else [None]

        for current_tag in tags_to_fetch:
            for current_inference in inference_to_fetch:
                filter_label = []
                if current_tag:
                    filter_label.append(f"pipeline_tag={current_tag}")
                if current_inference:
                    filter_label.append(f"inference={current_inference}")

                if filter_label:
                    print(f"\n--- Fetching models with filters: {', '.join(filter_label)} ---")

                # Fetch models in batches for current filter combination using cursor-based pagination
                batch_count = 0
                next_url = None

                while True:
                    batch_count += 1
                    print(f"Fetching batch {batch_count}...")

                    # Build request URL and params
                    if next_url:
                        # Use the next URL from Link header for pagination
                        request_url = next_url
                        params = {}  # URL already contains all params
                    else:
                        # First request - build params
                        request_url = base_url
                        params = {
                            'limit': limit,
                            'full': 'true' if full else 'false'
                        }

                        # Add filter parameters
                        params.update(filter_params)

                        # Add current pipeline_tag if specified
                        if current_tag:
                            params['pipeline_tag'] = current_tag

                        # Add current inference if specified
                        if current_inference:
                            params['inference'] = current_inference

                    # Debug: Print actual API request
                    if params:
                        print(f"  DEBUG: API request params: {params}")
                    else:
                        print(f"  DEBUG: Using pagination URL from Link header")

                    response = requests.get(request_url, headers=headers, params=params, timeout=timeout)

                    # Debug: Print response status
                    print(f"  DEBUG: Response status: {response.status_code}")

                    if response.status_code != 200:
                        print(f"HuggingFace API request failed with status {response.status_code}")
                        if response.text:
                            print(f"Error response: {response.text}")
                        break

                    batch_models = response.json()

                    # Debug: Show response structure
                    if batch_count == 1 and not batch_models:
                        print(f"  DEBUG: Empty response. Full response: {response.text[:500]}")

                    if not batch_models or len(batch_models) == 0:
                        print("No more models to fetch for this filter")
                        break

                    # Remove unwanted keys and deduplicate
                    new_models = 0
                    for model in batch_models:
                        model_id = model.get('id', model.get('modelId', ''))

                        # Skip if already seen (deduplication across different filter combinations)
                        if model_id in seen_model_ids:
                            continue

                        seen_model_ids.add(model_id)

                        # Remove unwanted keys
                        for key in exclude_keys:
                            model.pop(key, None)

                        all_models.append(model)
                        new_models += 1

                    print(f"  Fetched {len(batch_models)} models, {new_models} new (total unique: {len(all_models)})")

                    # Parse Link header for next page URL
                    link_header = response.headers.get('Link', '')
                    next_url = None

                    if link_header:
                        # Parse Link header: <url>; rel="next"
                        # Can have multiple links separated by comma
                        links = link_header.split(',')
                        for link in links:
                            if 'rel="next"' in link or "rel='next'" in link:
                                # Extract URL from <url>
                                url_match = link.split(';')[0].strip()
                                if url_match.startswith('<') and url_match.endswith('>'):
                                    next_url = url_match[1:-1]  # Remove < and >
                                    print(f"  DEBUG: Found next page URL in Link header")
                                break

                    # If no next link, we've reached the end
                    if not next_url:
                        print("Reached end of available models for this filter (no next link)")
                        break

        print(f"Total models fetched from API: {len(all_models)}")
        return all_models

    except requests.exceptions.Timeout:
        print("ERROR: HuggingFace API request timed out")
        return all_models
    except requests.exceptions.RequestException as request_error:
        print(f"ERROR: HuggingFace API request failed: {request_error}")
        return all_models
    except (ValueError, TypeError, KeyError) as general_error:
        print(f"ERROR: Unexpected error during API extraction: {general_error}")
        return all_models

def save_models_to_compact_json(models: List[Dict[str, Any]], filename: Path) -> bool:
    """
    Save models data to compact JSON file (no pretty printing)

    Args:
        models: List of model dictionaries
        filename: Output filename

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(models, json_file, separators=(',', ':'))
        print(f"✓ Models saved to compact JSON: {filename}")
        return True
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save models to {filename}: {error}")
        return False

def generate_summary_report(models: List[Dict[str, Any]], filename: Path) -> bool:
    """
    Generate summary report of fetched models

    Args:
        models: List of model dictionaries
        filename: Output filename

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filename, 'w', encoding='utf-8') as report_file:
            # Header
            report_file.write("=" * 80 + "\n")
            report_file.write("HUGGINGFACE API MODELS FETCH REPORT\n")
            report_file.write(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
            report_file.write("=" * 80 + "\n\n")

            # Summary
            report_file.write(f"SUMMARY:\n")
            report_file.write(f"  Total models fetched: {len(models)}\n\n")

            # Pipeline tag distribution
            pipeline_tags = {}
            for model in models:
                tag = model.get('pipeline_tag', 'unknown')
                pipeline_tags[tag] = pipeline_tags.get(tag, 0) + 1

            report_file.write(f"PIPELINE TAG DISTRIBUTION:\n")
            for tag, count in sorted(pipeline_tags.items(), key=lambda x: x[1], reverse=True):
                report_file.write(f"  {tag}: {count}\n")
            report_file.write(f"\nTotal pipeline tags: {len(pipeline_tags)}\n")

        print(f"✓ Summary report saved to: {filename}")
        return True

    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {filename}: {error}")
        return False

def main():
    """Main execution function"""
    print("HuggingFace API Models Fetcher (with Pre-fetch Filters)")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)

    # Output filenames
    json_filename = get_output_file_path("A-fetched-api-models.json")
    report_filename = get_output_file_path("A-fetched-api-models-report.txt")

    # Fetch all models from API
    models = fetch_all_huggingface_models()

    if not models:
        print("No models fetched from API")
        return False

    # Save to compact JSON file
    json_success = save_models_to_compact_json(models, json_filename)

    # Generate summary report
    report_success = generate_summary_report(models, report_filename)

    if json_success and report_success:
        print("="*60)
        print("FETCH COMPLETE")
        print(f"Total models: {len(models)}")
        print(f"JSON output: {json_filename}")
        print(f"Report output: {report_filename}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("FETCH FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)
