#!/usr/bin/env python3
"""
HuggingFace-Scraped & Google License Extraction for Groq Models

This script processes Groq models using a 3-category approach:
1. Meta/Llama models: Handled by A_extract_meta_licenses.py (skipped here)
2. Google models: Use hardcoded licenses from 06_google_models_licenses.json  
3. Other models: HuggingFace scraping with 2-category classification

HuggingFace 2-Category Logic:
- Opensource: license found in 05_opensource_license_urls.json
- Custom: license NOT found in 05_opensource_license_urls.json

Source Data: stage-1-scrape-production-models.json, 02_groq_to_hf_mappings.json
Output: stage-4-hf-scraped-licensing.json
"""

import json
import sys
import time
from typing import Dict, List, Any
from datetime import datetime

# Import license extraction functions
try:
    from D_extract_hf_license_names import extract_license_from_hf_page
except ImportError as e:
    print(f"ERROR: Could not import D_extract_hf_license_names: {e}")
    sys.exit(1)

try:
    from C_extract_hf_license_info_urls import get_huggingface_license_info
except ImportError as e:
    print(f"ERROR: Could not import C_extract_hf_license_info_urls: {e}")
    sys.exit(1)


def load_groq_models() -> List[Dict[str, Any]]:
    """Load Groq production models from stage-1 data"""
    try:
        with open('stage-1-scrape-production-models.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('production_models', [])
    except FileNotFoundError:
        print("ERROR: stage-1-scrape-production-models.json not found")
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in stage-1 file: {e}")
        return []


def load_groq_to_hf_mappings() -> Dict[str, str]:
    """Load Groq to HuggingFace ID mappings"""
    try:
        with open('02_groq_to_hf_mappings.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('groq_to_hf_mappings', {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load 02_groq_to_hf_mappings.json: {e}")
        return {}


def load_license_standardization() -> Dict[str, str]:
    """Load license name standardization mappings"""
    try:
        with open('06_license_name_standardization.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        mappings = data.get('license_name_standardization', {}).get('mappings', {})
        # Convert to lowercase keys for case-insensitive matching
        return {k.lower(): v for k, v in mappings.items()}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load license standardization: {e}")
        return {}


def load_opensource_license_urls() -> Dict[str, str]:
    """Load open source license URL mappings"""
    try:
        with open('05_opensource_license_urls.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'opensource_licenses' in data:
            license_mapping = {}
            for license_info in data['opensource_licenses']:
                license_name = license_info.get('license_name', '')
                license_url = license_info.get('license_url', '')
                if license_name and license_url:
                    license_mapping[license_name.lower()] = license_url
            return license_mapping
        
        return {}
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load opensource license URLs: {e}")
        return {}


def load_google_license_mappings() -> Dict[str, Dict[str, str]]:
    """Load Google model license mappings"""
    try:
        with open('07_google_models_licenses.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('google_models', {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load Google license mappings: {e}")
        return {}


def detect_hf_id(groq_model_id: str, hf_mappings: Dict[str, str]) -> str:
    """
    Detect HuggingFace ID from Groq model ID.
    
    Logic:
    1. If model_id contains '/', use as-is (already HF format)
    2. Otherwise, lookup in groq_to_hf_mappings.json
    3. Return HF ID or empty string if not mappable
    """
    # Direct HF format (contains slash)
    if '/' in groq_model_id:
        return groq_model_id
    
    # Mapped format
    return hf_mappings.get(groq_model_id, '')


def standardize_license_name(license_name: str, standardization_mappings: Dict[str, str]) -> str:
    """Standardize license name using mappings"""
    if not license_name:
        return license_name
    
    license_lower = license_name.lower()
    return standardization_mappings.get(license_lower, license_name)


def is_google_model(model_id: str, provider: str) -> bool:
    """Check if model is from Google"""
    return (provider.lower() == 'google' or 
            'gemini' in model_id.lower() or 
            'gemma' in model_id.lower())


def get_google_license_info(model_id: str, google_mappings: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """Get hardcoded license info for Google models"""
    model_lower = model_id.lower()
    
    if 'gemini' in model_lower:
        return google_mappings.get('gemini', {})
    elif 'gemma' in model_lower:
        return google_mappings.get('gemma', {})
    
    # Fallback to gemini if pattern not recognized
    return google_mappings.get('gemini', {})


def extract_hf_scraped_and_google_licenses(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract license information using 3-category approach"""
    # Load all mappings and standardization data
    hf_mappings = load_groq_to_hf_mappings()
    standardization_mappings = load_license_standardization()
    license_url_mappings = load_opensource_license_urls()
    google_mappings = load_google_license_mappings()
    
    processed_models = []
    
    print(f"Processing {len(models)} Groq models using 3-category approach...")
    print(f"Loaded {len(hf_mappings)} HF mappings")
    print(f"Loaded {len(standardization_mappings)} standardization rules")
    print(f"Loaded {len(license_url_mappings)} opensource license URL mappings")
    print(f"Loaded {len(google_mappings)} Google license mappings")
    
    for model in models:
        model_id = model.get('model_id', '')
        provider = model.get('model_provider', '')
        
        # CATEGORY 1: Skip Meta models (handled by A_extract_meta_licenses.py)
        if 'llama' in model_id.lower() or provider.lower() == 'meta':
            continue
        
        # CATEGORY 2: Google models (use hardcoded licenses)
        if is_google_model(model_id, provider):
            print(f"Processing Google model: {model_id} ({provider})")
            
            google_license_info = get_google_license_info(model_id, google_mappings)
            
            google_model = {
                'model_id': model_id,
                'model_provider': provider,
                'category': 'google',
                'license_info_text': google_license_info.get('license_info_text', ''),
                'license_info_url': google_license_info.get('license_info_url', ''),
                'license_name': google_license_info.get('license_name', ''),
                'license_url': google_license_info.get('license_url', '')
            }
            
            processed_models.append(google_model)
            print(f"  Applied Google license: {google_license_info.get('license_name', 'Unknown')}")
            continue
        
        # CATEGORY 3: Other models (HuggingFace scraping with 2-category logic)
        hf_id = detect_hf_id(model_id, hf_mappings)
        if not hf_id:
            print(f"Skipping model (no HF mapping): {model_id}")
            continue  # Not HF-mappable, skip
        
        print(f"Processing HF-mappable model: {model_id} → {hf_id}")
        
        # Step 1: Extract license name by scraping HuggingFace page
        print(f"  Scraping license name from HF page...")
        raw_license_name = extract_license_from_hf_page(hf_id)
        
        # Step 2: Standardize license name
        standardized_license_name = standardize_license_name(raw_license_name, standardization_mappings)
        print(f"  License name: '{raw_license_name}' → '{standardized_license_name}'")
        
        # Step 3: Extract license info URL using priority-based detection
        print(f"  Finding best license info URL...")
        hf_license_info = get_huggingface_license_info(hf_id)
        license_info_url = hf_license_info.get('license_info_url', '')
        
        # Step 4: Apply 2-category logic based on opensource license URL mappings
        is_opensource = (standardized_license_name and 
                        standardized_license_name.lower() in license_url_mappings)
        
        if is_opensource:
            # OPENSOURCE CATEGORY
            license_url = license_url_mappings[standardized_license_name.lower()]
            hf_model = {
                'model_id': model_id,
                'model_provider': provider,
                'hf_id': hf_id,
                'category': 'opensource',
                'raw_license_name': raw_license_name,
                'license_info_text': 'info',
                'license_info_url': license_info_url,
                'license_name': standardized_license_name,
                'license_url': license_url
            }
            print(f"  OPENSOURCE: Mapped '{standardized_license_name}' to {license_url}")
        else:
            # CUSTOM CATEGORY
            hf_model = {
                'model_id': model_id,
                'model_provider': provider,
                'hf_id': hf_id,
                'category': 'custom',
                'raw_license_name': raw_license_name,
                'license_info_text': '',
                'license_info_url': '',
                'license_name': standardized_license_name,
                'license_url': license_info_url  # Use HF URL as license_url for custom
            }
            print(f"  CUSTOM: No URL mapping for '{standardized_license_name}', using HF URL")
        
        processed_models.append(hf_model)
        
        # Add delay to be respectful to HuggingFace
        time.sleep(1)
    
    print(f"\nProcessed {len(processed_models)} models total")
    
    # Summary by category
    categories = {}
    for model in processed_models:
        cat = model.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("Category breakdown:")
    for category, count in categories.items():
        print(f"  {category.title()}: {count} models")
    
    return processed_models


def save_processed_results(processed_models: List[Dict[str, Any]]) -> str:
    """Save processed license results to JSON file"""
    output_file = 'stage-4-hf-scraped-licensing.json'
    
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat() + '+00:00',
            'source_file': 'stage-1-scrape-production-models.json',
            'processor': 'B_extract_opensource_licenses.py',
            'approach': '3-category processing: Meta (skipped), Google (hardcoded), Others (HF-scraped)',
            'categories': {
                'google': 'Hardcoded licenses from 07_google_models_licenses.json',
                'opensource': 'HF-scraped with license_info_text=info, official license URLs',
                'custom': 'HF-scraped with blank info fields, HF URL as license_url'
            },
            'dependencies': [
                '02_groq_to_hf_mappings.json',
                '07_google_models_licenses.json',
                'D_extract_hf_license_names.py',
                'C_extract_hf_license_info_urls.py',
                '06_license_name_standardization.json',
                '05_opensource_license_urls.json'
            ],
            'total_models': len(processed_models),
            'description': 'Models with Google hardcoded and HuggingFace-scraped license information'
        },
        'models': processed_models
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(processed_models)} processed license models to: {output_file}")
    return output_file


def main():
    """Main execution function"""
    print("=" * 80)
    print("GOOGLE & HUGGINGFACE-SCRAPED LICENSE EXTRACTION FOR GROQ MODELS")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    try:
        # Load Groq models
        models = load_groq_models()
        if not models:
            print("No models found to process")
            return False
        
        # Extract licenses using 3-category approach
        processed_models = extract_hf_scraped_and_google_licenses(models)
        
        if not processed_models:
            print("No models found for processing")
            return True
        
        # Save results
        output_file = save_processed_results(processed_models)
        
        # Summary
        print("\n" + "=" * 80)
        print("LICENSE EXTRACTION SUMMARY")
        print("=" * 80)
        print(f"Total Groq models: {len(models)}")
        print(f"Processed models: {len(processed_models)}")
        print(f"Output file: {output_file}")
        
        # Category breakdown
        categories = {}
        for model in processed_models:
            category = model.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        
        print("\nCategory Distribution:")
        for category, count in sorted(categories.items()):
            print(f"  {category.title()}: {count} models")
        
        # License breakdown
        license_counts = {}
        for model in processed_models:
            license_name = model.get('license_name', 'Unknown')
            license_counts[license_name] = license_counts.get(license_name, 0) + 1
        
        print("\nLicense Distribution:")
        for license_name, count in sorted(license_counts.items()):
            # Check if any model with this license has a non-HF license_url
            has_official_url = any(
                model.get('license_url') and 
                not model.get('license_url', '').startswith('https://huggingface.co')
                for model in processed_models 
                if model.get('license_name') == license_name
            )
            status = "OFFICIAL" if has_official_url else "HF_URL"
            print(f"  {license_name}: {count} models ({status})")
        
        print(f"\nCompleted at: {datetime.now().isoformat()}")
        return True
        
    except Exception as e:
        print(f"ERROR: License extraction failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)