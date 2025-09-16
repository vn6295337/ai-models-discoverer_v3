#!/usr/bin/env python3
"""
Extract license names from HuggingFace pages for filtered models with HF IDs
Source: E-other-license-info-urls-from-hf.json
Outputs: F-other-license-names-from-hf.json + report
Excludes Google and Meta models (they have dedicated handlers)
"""

import json
import requests
import time
import re
from datetime import datetime
from typing import List, Dict

# Import output utilities
import sys; import os; sys.path.append(os.path.join(os.path.dirname(__file__), "..", "04_utils")); from output_utils import get_output_file_path, get_input_file_path, ensure_output_dir_exists


def extract_license_from_hf_page(hf_id: str) -> str:
    """Extract license from HuggingFace page"""
    if not hf_id:
        return "Unknown"
    
    url = f"https://huggingface.co/{hf_id}"
    
    try:
        # Add headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"HTTP {response.status_code}"
        
        content = response.text
        
        # Look for license information in the specific HuggingFace HTML structure
        patterns = [
            r'<span class="-mr-1 text-gray-400">License:</span>\s*<span>([^<]+)</span>',  # HF license structure
            r'<span[^>]*>License:</span>[^<]*<span[^>]*>([^<]+)</span>',  # General license span structure
            r'"license"\s*:\s*"([^"]+)"',  # JSON license field
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                license_name = match.group(1).strip()
                # Return license exactly as found on the page
                return license_name
        
        return "Unknown"
        
    except requests.RequestException as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Parse Error: {str(e)}"


def should_skip_model(name: str) -> bool:
    """Check if model should be skipped (Google, Meta)"""
    name_lower = name.lower()
    skip_providers = ['google:', 'meta:']
    
    for provider in skip_providers:
        if name_lower.startswith(provider):
            return True
    return False


def main():
    """Extract licenses from HuggingFace pages for non-Google/Meta models"""

    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Loading stage-E license info data...")
    
    # Load the JSON data
    with open(get_input_file_path('E-other-license-info-urls-from-hf.json'), 'r') as f:
        data = json.load(f)
    
    # Filter models with HuggingFace IDs, excluding Google/Meta
    target_models = []
    
    for model in data:
        primary_key = model.get('canonical_slug', '')  # Primary identifier
        name = model.get('name', '')                   # Practical for skip detection
        hf_id = model.get('hugging_face_id', '')       # Practical for HF API calls
        
        if hf_id and not should_skip_model(name):
            target_models.append({
                'id': model.get('id', ''),
                'canonical_slug': primary_key,
                'name': name,
                'hugging_face_id': hf_id
            })
    
    print(f"Found {len(target_models)} models to process (excluding Google/Meta)")
    
    # Extract licenses
    results = []
    
    for i, model in enumerate(target_models, 1):
        print(f"Processing {i}/{len(target_models)}: {model['name'][:60]}...")
        
        license_info = extract_license_from_hf_page(model['hugging_face_id'])
        
        results.append({
            'id': model['id'],
            'canonical_slug': model['canonical_slug'],     # Primary identifier
            'name': model['name'],
            'hugging_face_id': model['hugging_face_id'],
            'extracted_license': license_info
        })
        
        # Add small delay to be respectful to HuggingFace
        time.sleep(1)
    
    # Write results to JSON file
    json_output_file = get_output_file_path('F-other-license-names-from-hf.json')
    
    with open(json_output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Write human-readable report
    report_output_file = get_output_file_path('F-other-license-names-from-hf-report.txt')
    
    with open(report_output_file, 'w') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("OTHER MODEL LICENSE NAME EXTRACTIONS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Summary
        f.write(f"SUMMARY:\n")
        f.write(f"  Total models : {len(results)}\n")
        f.write(f"  Input        : E-other-license-info-urls-from-hf.json\n")
        f.write(f"  Processor    : F_fetch_other_license_names_from_hf.py\n")
        f.write(f"  Output       : F-other-license-names-from-hf.json\n\n")
        
        # License distribution
        license_counts = {}
        for model in results:
            license = model['extracted_license']
            license_counts[license] = license_counts.get(license, 0) + 1
        
        f.write("LICENSE DISTRIBUTION:\n")
        for license, count in sorted(license_counts.items()):
            f.write(f"  {license}: {count}\n")
        f.write(f"\nTotal license types: {len(license_counts)}\n\n")
        
        # Detailed results
        f.write("DETAILED MODEL EXTRACTION RESULTS:\n")
        f.write("=" * 80 + "\n\n")
        
        for i, model in enumerate(results, 1):
            f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
            f.write("-" * 50 + "\n")
            f.write(f"  ID               : {model.get('id', 'Unknown')}\n")
            f.write(f"  Canonical Slug   : {model.get('canonical_slug', 'Unknown')}\n")
            f.write(f"  HuggingFace ID   : {model.get('hugging_face_id', 'Unknown')}\n")
            f.write(f"  Extracted License: {model.get('extracted_license', 'Unknown')}\n")
            
            if i < len(results):
                f.write("\n" + "=" * 80 + "\n\n")
            else:
                f.write("\n")
    
    print(f"JSON results written to: {json_output_file}")
    print(f"Report written to: {report_output_file}")
    print(f"Processed {len(results)} models")


if __name__ == "__main__":
    main()