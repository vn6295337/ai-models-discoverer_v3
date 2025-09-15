#!/usr/bin/env python3
"""
OpenRouter API Models Fetcher
Fetches ALL models from OpenRouter API and saves to JSON + human-readable report
"""
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import requests

# Import output utilities
from output_utils import get_output_file_path, ensure_output_dir_exists, clean_output_directory

# Add utils directory to path for key_client import
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from utils.key_client import get_api_key, log_usage
except ImportError:
    print("WARNING: Could not import utils.key_client")

    def get_api_key(service):  # pylint: disable=unused-argument
        """Fallback function for API key retrieval"""
        return None

    def log_usage(service, metric, value):  # pylint: disable=unused-argument
        """Fallback function for usage logging"""

def load_api_configuration() -> Dict[str, Any]:
    """Load API configuration from 04_api_configuration.json"""
    config_file = '01_api_configuration.json'
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"WARNING: Failed to load API configuration from {config_file}: {error}")
        print("Using hardcoded fallback values")
        return {}

def fetch_all_openrouter_models() -> List[Dict[str, Any]]:
    """
    Fetch ALL models from OpenRouter API (no filtering)
    
    Returns:
        List of all model dictionaries from API
    """
    # Get API key from secure key management system
    api_key = get_api_key('openrouter')
    if not api_key:
        print("ERROR: Failed to retrieve OpenRouter API key from secure storage")
        print("Please check key management system")
        return []

    # Load API configuration
    config = load_api_configuration()
    
    # Extract configuration values with fallbacks
    endpoint = config.get('endpoints', {}).get('models', 'https://openrouter.ai/api/v1/models')
    timeout = config.get('timeouts', {}).get('api_request_timeout', 30)
    content_type = config.get('headers', {}).get('content_type', 'application/json')
    auth_template = config.get('headers', {}).get('authorization_template', 'Bearer {api_key}')

    try:
        print("Fetching ALL OpenRouter models from API...")

        headers = {
            'Authorization': auth_template.format(api_key=api_key),
            'Content-Type': content_type
        }

        # Fetch OpenRouter models
        print("Requesting models from OpenRouter API...")
        response = requests.get(endpoint, headers=headers, timeout=timeout)

        # Log API usage for rate limit tracking
        if response.status_code == 200:
            log_usage('openrouter', 'rpm', 1)  # 1 request per minute
            log_usage('openrouter', 'rpd', 1)  # 1 request per day

            data = response.json()
            if 'data' in data and isinstance(data['data'], list):
                all_models = data['data']
                print(f"Total models fetched from API: {len(all_models)}")
                return all_models

            print("OpenRouter API returned unexpected data format")
            return []
            
        print(f"OpenRouter API request failed with status {response.status_code}")
        if response.text:
            print(f"Error response: {response.text}")
        return []

    except requests.exceptions.Timeout:
        print("ERROR: OpenRouter API request timed out")
        return []
    except requests.exceptions.RequestException as request_error:
        print(f"ERROR: OpenRouter API request failed: {request_error}")
        return []
    except (ValueError, TypeError, KeyError) as general_error:
        print(f"ERROR: Unexpected error during API extraction: {general_error}")
        return []

def save_models_to_json(models: List[Dict[str, Any]], filename: str) -> bool:
    """
    Save models data to JSON file
    
    Args:
        models: List of model dictionaries
        filename: Output filename
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(models, json_file, indent=2)
        print(f"✓ Models saved to: {filename}")
        return True
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save models to {filename}: {error}")
        return False

def generate_human_readable_report(models: List[Dict[str, Any]], filename: str) -> bool:
    """
    Generate human-readable report of all models
    
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
            report_file.write("OPENROUTER API MODELS REPORT\n")
            report_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_file.write("=" * 80 + "\n\n")
            
            # Summary
            report_file.write(f"SUMMARY:\n")
            report_file.write(f"  Total models: {len(models)}\n\n")
            
            # Provider analysis with model IDs
            providers = {}
            for model in models:
                name = model.get('name', '')
                model_id = model.get('id', '')
                
                # Extract model ID (after first slash, or entire ID if no slash)
                if '/' in model_id:
                    extracted_id = model_id.split('/', 1)[1]
                else:
                    extracted_id = model_id
                
                if ': ' in name:
                    provider = name.split(': ', 1)[0].strip()
                    if provider not in providers:
                        providers[provider] = {'count': 0, 'models': []}
                    providers[provider]['count'] += 1
                    providers[provider]['models'].append(extracted_id)
            
            # Sort providers by count (descending order)
            sorted_providers = sorted(providers.items(), key=lambda x: x[1]['count'], reverse=True)
            
            # Calculate max provider name length for alignment
            max_provider_length = max(len(provider) for provider, _ in sorted_providers) if sorted_providers else 0
            
            report_file.write(f"PROVIDER BREAKDOWN (Descending Order):\n")
            for provider, data in sorted_providers:
                count = data['count']
                # Align columns using string formatting
                report_file.write(f"  {provider:<{max_provider_length}} : {count:>3} models\n")
                # List model IDs under each provider
                for model_id in sorted(data['models']):
                    report_file.write(f"    - {model_id}\n")
                report_file.write("\n")
            
            report_file.write(f"Total providers: {len(providers)}\n")
        
        print(f"✓ Human-readable report saved to: {filename}")
        return True
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {filename}: {error}")
        return False

def main():
    """Main execution function"""
    print("OpenRouter API Models Fetcher")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)

    # Clean output directory (only for first stage of pipeline)
    clean_output_directory()

    # Ensure output directory exists
    ensure_output_dir_exists()

    # Output filenames with full paths
    json_filename = get_output_file_path("A-api-models.json")
    report_filename = get_output_file_path("A-api-models-report.txt")
    
    # Fetch all models from API
    models = fetch_all_openrouter_models()
    
    if not models:
        print("No models fetched from API")
        return False
    
    # Save to JSON file
    json_success = save_models_to_json(models, json_filename)
    
    # Generate human-readable report
    report_success = generate_human_readable_report(models, report_filename)
    
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