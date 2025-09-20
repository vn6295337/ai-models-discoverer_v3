#!/usr/bin/env python3
"""
Extract license information from HuggingFace pages for models with HF IDs
Excludes Google, Mistral, and Meta models (they have dedicated handlers)
"""

import json
import requests
import time
import re
from typing import List, Dict


def extract_license_from_hf_page(hf_id: str) -> str:
    """Extract license from HuggingFace page"""
    if not hf_id:
        return "No HF ID"
    
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
        
        return "Not Found"
        
    except requests.RequestException as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Parse Error: {str(e)}"


def should_skip_model(name: str) -> bool:
    """Check if model should be skipped (Google, Mistral, Meta)"""
    name_lower = name.lower()
    skip_providers = ['google:', 'meta:', 'mistral ai:', 'mistral:']
    
    for provider in skip_providers:
        if name_lower.startswith(provider):
            return True
    return False


def main():
    """Extract licenses from HuggingFace pages for non-Google/Mistral/Meta models"""
    
    print("Loading stage-1 data...")
    
    # Load the JSON data
    with open('/home/km_project/ai-models-discoverer_v2/openrouter_pipeline/stage-1-api-data-extraction.json', 'r') as f:
        data = json.load(f)
    
    # Filter models with HuggingFace IDs, excluding Google/Mistral/Meta
    target_models = []
    
    for model in data:
        name = model.get('name', '')
        hf_id = model.get('hugging_face_id', '')
        
        if hf_id and not should_skip_model(name):
            target_models.append({
                'name': name,
                'hugging_face_id': hf_id,
                'canonical_slug': model.get('canonical_slug', '')
            })
    
    print(f"Found {len(target_models)} models to process (excluding Google/Mistral/Meta)")
    
    # Extract licenses
    results = []
    
    for i, model in enumerate(target_models, 1):
        print(f"Processing {i}/{len(target_models)}: {model['name'][:60]}...")
        
        license_info = extract_license_from_hf_page(model['hugging_face_id'])
        
        results.append({
            'name': model['name'],
            'hugging_face_id': model['hugging_face_id'],
            'canonical_slug': model['canonical_slug'],
            'extracted_license': license_info
        })
        
        # Add small delay to be respectful to HuggingFace
        time.sleep(1)
    
    # Write results to text file
    output_file = '/home/km_project/ai-models-discoverer_v2/openrouter_pipeline/huggingface_license_results.txt'
    
    with open(output_file, 'w') as f:
        f.write("HUGGINGFACE MODEL LICENSE EXTRACTIONS\n")
        f.write("=" * 50 + "\n")
        f.write("(Excludes Google, Mistral, and Meta models)\n\n")
        
        for i, model in enumerate(results, 1):
            f.write(f"{i}. Model: {model['name']}\n")
            f.write(f"   HuggingFace ID: {model['hugging_face_id']}\n")
            f.write(f"   Canonical Slug: {model['canonical_slug']}\n")
            f.write(f"   Extracted License: {model['extracted_license']}\n")
            f.write("\n")
        
        # Summary statistics
        license_counts = {}
        for model in results:
            license = model['extracted_license']
            license_counts[license] = license_counts.get(license, 0) + 1
        
        f.write("SUMMARY:\n")
        f.write(f"Total models processed: {len(results)}\n")
        f.write("License distribution:\n")
        for license, count in sorted(license_counts.items()):
            f.write(f"  {license}: {count}\n")
    
    print(f"Results written to: {output_file}")
    print(f"Processed {len(results)} models")


if __name__ == "__main__":
    main()