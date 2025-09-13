#!/usr/bin/env python3
"""
Opensource License Information Collator
Brings together opensource license information from pipeline stages
Sources:
- E-other-license-info-urls-from-hf.json (license info URLs)
- H-opensource-license-names.json (opensource license names)
- I-opensource-license-urls.json (opensource official URLs)
Output: K-collated-opensource-licenses.json + comprehensive report
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

def extract_model_name(full_name: str) -> str:
    """Extract clean model name from full name"""
    # Remove provider prefix like "Google:", "Meta:", etc.
    if ':' in full_name:
        model_part = full_name.split(':', 1)[1].strip()
    else:
        model_part = full_name.strip()
    
    # Remove (free) suffix if present
    if model_part.endswith(' (free)'):
        model_part = model_part[:-7].strip()
    
    return model_part

def load_json_file(filename: str, description: str) -> List[Dict[str, Any]]:
    """Load JSON file with error handling"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Loaded {len(data)} items from {description}: {filename}")
        return data
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load {description} from {filename}: {error}")
        return []

def create_canonical_slug_index(models: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Create index by canonical_slug for fast lookups"""
    index = {}
    for model in models:
        canonical_slug = model.get('canonical_slug', '')
        if canonical_slug:
            index[canonical_slug] = model
    return index

def collate_license_information() -> List[Dict[str, Any]]:
    """Collate opensource license information from 3 pipeline stages"""
    
    # Load source files
    print("Loading source files...")
    
    # Stage E: License info URLs from HF
    stage_e_models = load_json_file(
        'E-other-license-info-urls-from-hf.json',
        'license info URLs'
    )
    
    # Stage H: Opensource license names only
    opensource_names = load_json_file(
        'H-opensource-license-names.json',
        'opensource license names'
    )
    
    # Stage I: Opensource URLs
    opensource_urls = load_json_file(
        'I-opensource-license-urls.json',
        'opensource license URLs'
    )
    
    # Create indexes for fast lookups
    print("Creating lookup indexes...")
    stage_e_index = create_canonical_slug_index(stage_e_models)
    opensource_names_index = create_canonical_slug_index(opensource_names)
    opensource_urls_index = create_canonical_slug_index(opensource_urls)
    
    # Collect all unique canonical slugs from opensource models only
    all_slugs = set()
    all_slugs.update(opensource_names_index.keys())
    all_slugs.update(opensource_urls_index.keys())
    
    print(f"Found {len(all_slugs)} unique opensource models")
    
    # Collate information for each model
    collated_models = []
    
    for canonical_slug in sorted(all_slugs):
        # Get data from each stage
        stage_e_data = stage_e_index.get(canonical_slug, {})
        opensource_name_data = opensource_names_index.get(canonical_slug, {})
        opensource_url_data = opensource_urls_index.get(canonical_slug, {})
        
        # Get the original name from any available source (prioritize Stage-E which has full names)
        original_name = (stage_e_data.get('name') or
                        opensource_name_data.get('name') or
                        opensource_url_data.get('name') or
                        'Unknown')
        
        # Extract clean model name
        clean_model_name = extract_model_name(original_name) if original_name != 'Unknown' else 'Unknown'
        
        # Create simplified model record with only required fields
        collated_model = {
            # Primary identification
            'id': (opensource_name_data.get('id') or
                   opensource_url_data.get('id') or
                   stage_e_data.get('id') or
                   'Unknown'),
            
            'canonical_slug': canonical_slug,
            
            'original_name': original_name,
            
            'hugging_face_id': (opensource_name_data.get('hugging_face_id') or
                               opensource_url_data.get('hugging_face_id') or
                               stage_e_data.get('hugging_face_id') or
                               ''),
            
            'clean_model_name': clean_model_name,
            
            # License information
            'license_info_text': 'info',  # Static text as requested
            'license_info_url': stage_e_data.get('license_info_url', ''),
            'license_name': (opensource_name_data.get('license_name') or
                            opensource_url_data.get('license_name') or
                            'Unknown'),
            'license_url': opensource_url_data.get('official_license_url', '')
        }
        
        collated_models.append(collated_model)
    
    print(f"✓ Collated license information for {len(collated_models)} opensource models")
    return collated_models

def save_collated_data(collated_models: List[Dict[str, Any]]) -> str:
    """Save collated data to JSON file"""
    output_file = 'K-collated-opensource-licenses.json'
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collated_models, f, indent=2)
        print(f"✓ Saved {len(collated_models)} collated models to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_collation_report(collated_models: List[Dict[str, Any]]) -> str:
    """Generate comprehensive collation report"""
    report_file = 'K-collated-opensource-licenses-report.txt'
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("COLLATED OPENSOURCE LICENSE INFORMATION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models        : {len(collated_models)}\n")
            f.write(f"  Input sources       : 3 pipeline stage files\n")
            f.write(f"  Processor           : K_collate_opensource_licenses.py\n")
            f.write(f"  Output              : K-collated-opensource-licenses.json\n\n")
            
            # Pipeline stage coverage
            stage_coverage = {
                'stage_e': 0,
                'stage_h_opensource': 0,
                'stage_i': 0
            }
            
            stage_e_index = create_canonical_slug_index(load_json_file('E-other-license-info-urls-from-hf.json', 'temp'))
            
            for model in collated_models:
                canonical_slug = model.get('canonical_slug', '')
                if canonical_slug in stage_e_index: stage_coverage['stage_e'] += 1
                if model.get('license_name', 'Unknown') != 'Unknown': stage_coverage['stage_h_opensource'] += 1
                if model.get('license_url', ''): stage_coverage['stage_i'] += 1
            
            f.write(f"PIPELINE STAGE COVERAGE:\n")
            f.write(f"  Stage E (License Info URLs)    : {stage_coverage['stage_e']} models\n")
            f.write(f"  Stage H Opensource Names       : {stage_coverage['stage_h_opensource']} models\n")
            f.write(f"  Stage I Opensource URLs        : {stage_coverage['stage_i']} models\n\n")
            
            # License name distribution
            license_distribution = {}
            for model in collated_models:
                license_name = model.get('license_name', 'Unknown')
                license_distribution[license_name] = license_distribution.get(license_name, 0) + 1
            
            f.write(f"OPENSOURCE LICENSE DISTRIBUTION:\n")
            # Sort by count descending, then by name
            sorted_licenses = sorted(license_distribution.items(), key=lambda x: (-x[1], x[0]))
            for license_name, count in sorted_licenses:
                f.write(f"  {count:2d} models: {license_name}\n")
            f.write(f"\nTotal unique license types: {len(license_distribution)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED OPENSOURCE MODEL INFORMATION:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by license name, then canonical slug
            sorted_models = sorted(
                collated_models,
                key=lambda x: (x.get('license_name', ''), 
                              x.get('canonical_slug', ''))
            )
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Standardized field ordering: identifiers → names → licenses
                f.write(f"  ID: {model.get('id', '')}\n")
                f.write(f"  Original Name: {model.get('original_name', '')}\n")
                f.write(f"  HuggingFace ID: {model.get('hugging_face_id', '')}\n")
                f.write(f"  Canonical Slug: {model.get('canonical_slug', '')}\n")
                f.write(f"  Clean Model Name: {model.get('clean_model_name', '')}\n")
                f.write(f"  License Info Text: {model.get('license_info_text', '')}\n")
                f.write(f"  License Info URL: {model.get('license_info_url', '')}\n")
                f.write(f"  License Name: {model.get('license_name', '')}\n")
                f.write(f"  License URL: {model.get('license_url', '')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Collation report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    print("Opensource License Information Collator")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Collate license information from all stages
    collated_models = collate_license_information()
    
    if not collated_models:
        print("No models to collate")
        return False
    
    # Save JSON output
    json_success = save_collated_data(collated_models)
    
    # Generate comprehensive report
    report_success = generate_collation_report(collated_models)
    
    if json_success and report_success:
        print(f"SUCCESS: Collated {len(collated_models)} opensource models - JSON: {json_success} | Report: {report_success}")
        return True
    else:
        print("LICENSE INFORMATION COLLATION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)