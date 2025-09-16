#!/usr/bin/env python3
"""
Final License List Consolidator
Combines all license information from all pipeline stages into a comprehensive final list
Sources:
- C-google-licenses.json (Google model licenses)
- D-meta-licenses.json (Meta model licenses)
- K-collated-opensource-licenses.json (Opensource licenses)
- L-collated-custom-licenses.json (Custom licenses)
Output: M-final-license-list.json + comprehensive report
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import output utilities
import sys; import os; sys.path.append(os.path.join(os.path.dirname(__file__), "..", "04_utils")); from output_utils import get_output_file_path, get_input_file_path, ensure_output_dir_exists

def load_json_file(filename: str, description: str) -> List[Dict[str, Any]]:
    """Load JSON file with error handling - all files now use standardized flat array structure"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # All files now use flat array structure
        if isinstance(data, list):
            print(f"✓ Loaded {len(data)} items from {description}: {filename}")
            return data
        else:
            print(f"ERROR: Expected flat array structure in {filename}")
            return []
            
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

def consolidate_all_licenses() -> List[Dict[str, Any]]:
    """Consolidate all license information from all pipeline stages"""
    
    # Load all source files
    print("Loading all source files...")
    
    # Google licenses (Stage C)
    google_models = load_json_file(
        get_input_file_path('C-google-licenses.json'),
        'Google licenses'
    )
    
    # Meta licenses (Stage D)
    meta_models = load_json_file(
        get_input_file_path('D-meta-licenses.json'),
        'Meta licenses'
    )
    
    # Opensource licenses (Stage K)
    opensource_models = load_json_file(
        get_input_file_path('K-collated-opensource-licenses.json'),
        'Opensource licenses'
    )
    
    # Custom licenses (Stage L)
    custom_models = load_json_file(
        get_input_file_path('L-collated-custom-licenses.json'),
        'Custom licenses'
    )
    
    # Create indexes for fast lookups
    print("Creating lookup indexes...")
    google_index = create_canonical_slug_index(google_models)
    meta_index = create_canonical_slug_index(meta_models)
    opensource_index = create_canonical_slug_index(opensource_models)
    custom_index = create_canonical_slug_index(custom_models)
    
    # Collect all unique canonical slugs
    all_slugs = set()
    for index in [google_index, meta_index, opensource_index, custom_index]:
        all_slugs.update(index.keys())
    
    print(f"Found {len(all_slugs)} unique models across all license categories")
    
    # Consolidate information for each model
    final_models = []
    
    for canonical_slug in sorted(all_slugs):
        # Get data from each category
        google_data = google_index.get(canonical_slug, {})
        meta_data = meta_index.get(canonical_slug, {})
        opensource_data = opensource_index.get(canonical_slug, {})
        custom_data = custom_index.get(canonical_slug, {})
        
        # Determine source category and priority
        source_category = 'unknown'
        primary_data = {}
        
        if google_data:
            source_category = 'google'
            primary_data = google_data
        elif meta_data:
            source_category = 'meta'
            primary_data = meta_data
        elif opensource_data:
            source_category = 'opensource'
            primary_data = opensource_data
        elif custom_data:
            source_category = 'custom'
            primary_data = custom_data
        
        # Create final consolidated model record with standardized field names
        final_model = {
            # Primary identification
            'id': primary_data.get('id', ''),
            
            'canonical_slug': canonical_slug,
            
            # Model names using standardized field names
            'original_name': primary_data.get('original_name', ''),
            
            'hugging_face_id': primary_data.get('hugging_face_id', ''),
            
            'clean_model_name': primary_data.get('clean_model_name', ''),
            
            # License information fields
            'license_info_text': (google_data.get('license_info_text', '') or
                                 meta_data.get('license_info_text', '') or
                                 opensource_data.get('license_info_text', '') or
                                 custom_data.get('license_info_text', '') or
                                 ''),
            
            'license_info_url': (google_data.get('license_info_url', '') or
                                meta_data.get('license_info_url', '') or
                                opensource_data.get('license_info_url', '') or
                                custom_data.get('license_info_url', '') or
                                ''),
            
            'license_name': (google_data.get('license_name') or
                            meta_data.get('license_name') or
                            opensource_data.get('license_name') or
                            custom_data.get('license_name') or
                            'Unknown'),
            
            'license_url': (google_data.get('license_url') or
                           meta_data.get('license_url') or
                           opensource_data.get('license_url') or
                           custom_data.get('license_url') or
                           ''),
            
            # Source tracking
            'source_category': source_category
        }
        
        final_models.append(final_model)
    
    print(f"✓ Consolidated license information for {len(final_models)} total models")
    return final_models

def save_final_data(final_models: List[Dict[str, Any]]) -> str:
    """Save final consolidated data to JSON file"""
    output_file = get_output_file_path('M-final-license-list.json')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_models, f, indent=2)
        print(f"✓ Saved {len(final_models)} final models to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_final_report(final_models: List[Dict[str, Any]]) -> str:
    """Generate comprehensive final report"""
    report_file = get_output_file_path('M-final-license-list-report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("FINAL CONSOLIDATED LICENSE LIST REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models        : {len(final_models)}\n")
            f.write(f"  Input sources       : 4 pipeline stage files\n")
            f.write(f"  Processor           : M_final_list_of_licenses.py\n")
            f.write(f"  Output              : M-final-license-list.json\n\n")
            
            # Source category distribution
            category_stats = {}
            for model in final_models:
                category = model.get('source_category', 'unknown')
                category_stats[category] = category_stats.get(category, 0) + 1
            
            f.write(f"SOURCE CATEGORY DISTRIBUTION:\n")
            for category, count in sorted(category_stats.items()):
                f.write(f"  {category.title()}: {count} models\n")
            f.write(f"\n")
            
            # License name distribution
            license_distribution = {}
            for model in final_models:
                license_name = model.get('license_name', 'Unknown')
                license_distribution[license_name] = license_distribution.get(license_name, 0) + 1
            
            f.write(f"FINAL LICENSE DISTRIBUTION:\n")
            # Sort by count descending, then by name
            sorted_licenses = sorted(license_distribution.items(), key=lambda x: (-x[1], x[0]))
            for license_name, count in sorted_licenses:
                f.write(f"  {count:2d} models: {license_name}\n")
            f.write(f"\nTotal unique license types: {len(license_distribution)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED FINAL MODEL INFORMATION:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by source category, then license name, then canonical slug
            sorted_models = sorted(
                final_models,
                key=lambda x: (x.get('source_category', ''),
                              x.get('license_name', ''), 
                              x.get('canonical_slug', ''))
            )
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Standardized field ordering: identifiers → names → licenses → metadata
                f.write(f"  ID: {model.get('id', '')}\n")
                f.write(f"  Original Name: {model.get('original_name', '')}\n")
                f.write(f"  HuggingFace ID: {model.get('hugging_face_id', '')}\n")
                f.write(f"  Canonical Slug: {model.get('canonical_slug', '')}\n")
                f.write(f"  Clean Model Name: {model.get('clean_model_name', '')}\n")
                f.write(f"  License Info Text: {model.get('license_info_text', '')}\n")
                f.write(f"  License Info URL: {model.get('license_info_url', '')}\n")
                f.write(f"  License Name: {model.get('license_name', '')}\n")
                f.write(f"  License URL: {model.get('license_url', '')}\n")
                f.write(f"  Source Category: {model.get('source_category', '')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Final report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Final License List Consolidator")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Consolidate all license information
    final_models = consolidate_all_licenses()
    
    if not final_models:
        print("No models to consolidate")
        return False
    
    # Save JSON output
    json_success = save_final_data(final_models)
    
    # Generate comprehensive report
    report_success = generate_final_report(final_models)
    
    if json_success and report_success:
        print(f"SUCCESS: Consolidated {len(final_models)} total models - JSON: {json_success} | Report: {report_success}")
        return True
    else:
        print("FINAL LICENSE CONSOLIDATION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)