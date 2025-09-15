#!/usr/bin/env python3
"""
Other License Names Standardizer
Standardizes extracted license names from HuggingFace pages using config mappings
Source: F-other-license-names-from-hf.json (raw extracted license names)
Config: 04_license_standardization_rules.json (standardization mappings)
Outputs: G-standardized-other-license-names-from-hf.json + report
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Tuple

# Import output utilities
from output_utils import get_output_file_path, get_input_file_path, ensure_output_dir_exists

def load_license_names_data() -> List[Dict[str, Any]]:
    """Load extracted license names from Stage-F"""
    input_file = get_input_file_path('F-other-license-names-from-hf.json')
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            license_data = json.load(f)
        print(f"✓ Loaded {len(license_data)} models with license names from: {input_file}")
        return license_data
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load license names from {input_file}: {error}")
        return []

def load_license_standardization_config() -> Dict[str, Any]:
    """Load license standardization configuration from JSON file"""
    config_file = '04_license_standardization_rules.json'
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Loaded license standardization config from: {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load standardization config from {config_file}: {error}")
        return {}

def get_license_standardization_mappings(config: Dict[str, Any]) -> Tuple[Dict[str, str], bool]:
    """Get license name standardization mappings from config"""
    # Check if the config has the nested structure
    license_config = config.get('license_name_standardization', config)
    
    if not license_config.get('enabled', False):
        print("License name standardization is disabled in config")
        return {}, False
    
    mappings = license_config.get('mappings', {})
    case_sensitive = license_config.get('case_sensitive', False)
    
    print(f"Loaded {len(mappings)} license mappings, case_sensitive={case_sensitive}")
    return mappings, case_sensitive

def standardize_license_name(raw_license: str, mappings: Dict[str, str], case_sensitive: bool = False, debug: bool = False) -> str:
    """Standardize a single license name using config mappings"""
    if not raw_license or raw_license.strip() == '':
        return 'Unknown'
    
    if not mappings:
        # No mappings available, return cleaned original or Unknown
        cleaned = raw_license.strip()
        if debug:
            print(f"  DEBUG: No mappings available, returning: {cleaned}")
        return cleaned if cleaned else 'Unknown'
    
    # Clean the input
    license_input = raw_license.strip()
    
    # Try exact match first (case-sensitive)
    if license_input in mappings:
        result = mappings[license_input]
        if debug:
            print(f"  DEBUG: Exact match '{license_input}' -> '{result}'")
        return result
    
    # If case insensitive, try matching with different cases
    if not case_sensitive:
        for mapping_key, standardized_value in mappings.items():
            if license_input.lower() == mapping_key.lower():
                if debug:
                    print(f"  DEBUG: Case-insensitive match '{license_input}' -> '{standardized_value}' (via key '{mapping_key}')")
                return standardized_value
    
    # Check for error patterns
    license_lower = license_input.lower()
    if (license_lower.startswith('http ') or 
        license_lower.startswith('error:') or 
        license_lower.startswith('parse error:') or 
        license_lower in ['not found', 'no hf id']):
        if debug:
            print(f"  DEBUG: Error pattern detected '{license_input}' -> 'Unknown'")
        return 'Unknown'
    
    # Return original if it looks like a legitimate license name
    if debug:
        print(f"  DEBUG: No match found for '{license_input}', returning original")
    return license_input

def process_license_standardization(license_data: List[Dict[str, Any]], 
                                   config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process license names and standardize them using config"""
    processed_models = []
    
    # Get mappings and config settings
    mappings, case_sensitive = get_license_standardization_mappings(config)
    
    print(f"Processing {len(license_data)} models for license name standardization...")
    print(f"Using {len(mappings)} standardization mappings (case_sensitive={case_sensitive})")
    
    for i, model in enumerate(license_data, 1):
        primary_key = model.get('canonical_slug', '')  # Primary identifier
        raw_license = model.get('extracted_license', '') # Practical for license processing
        
        # Standardize license name using config (enable debug for first few)
        debug_mode = i <= 5  # Debug first 5 models
        standardized_license = standardize_license_name(raw_license, mappings, case_sensitive, debug_mode)
        
        # Create processed model record
        processed_model = {
            'id': model.get('id', ''),
            'canonical_slug': primary_key,             # Primary identifier
            'name': model.get('name', ''),
            'hugging_face_id': model.get('hugging_face_id', ''),
            'raw_extracted_license': raw_license,
            'standardized_license_name': standardized_license
        }
        
        processed_models.append(processed_model)
        
        # Progress indicator
        if i % 50 == 0 or i == len(license_data):
            print(f"  Processed {i}/{len(license_data)} models...")
    
    return processed_models

def save_standardized_licenses_json(processed_models: List[Dict[str, Any]]) -> str:
    """Save processed models with standardized license names to JSON file"""
    output_file = get_input_file_path('G-standardized-other-license-names-from-hf.json')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_models, f, indent=2)
        print(f"✓ Saved standardized license names to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def generate_standardization_report(processed_models: List[Dict[str, Any]]) -> str:
    """Generate human-readable report"""
    report_file = get_output_file_path('G-standardized-other-license-names-from-hf-report.txt')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("STANDARDIZED OTHER LICENSE NAMES REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total models : {len(processed_models)}\n")
            f.write(f"  Input        : F-other-license-names-from-hf.json\n")
            f.write(f"  Config       : 04_license_standardization_rules.json\n")
            f.write(f"  Processor    : G_standardize_other_license_names_from_hf.py\n")
            f.write(f"  Output       : G-standardized-other-license-names-from-hf.json\n\n")
            
            # Standardization statistics
            standardized_distribution = {}
            transformation_count = 0
            
            for model in processed_models:
                raw_license = model.get('raw_extracted_license', '')
                standardized = model.get('standardized_license_name', 'Unknown')
                
                standardized_distribution[standardized] = standardized_distribution.get(standardized, 0) + 1
                
                # Count transformations
                if raw_license.strip() != standardized:
                    transformation_count += 1
            
            f.write(f"STANDARDIZATION RESULTS:\n")
            f.write(f"  Models with license transformations: {transformation_count}\n")
            f.write(f"  Models unchanged: {len(processed_models) - transformation_count}\n")
            if processed_models:
                f.write(f"  Transformation rate: {(transformation_count/len(processed_models)*100):.1f}%\n\n")
            else:
                f.write(f"  Transformation rate: 0.0%\n\n")
            
            # Standardized license distribution
            f.write(f"STANDARDIZED LICENSE DISTRIBUTION:\n")
            for license_name in sorted(standardized_distribution.keys()):
                count = standardized_distribution[license_name]
                f.write(f"  {license_name}: {count} models\n")
            f.write(f"\nTotal license types: {len(standardized_distribution)}\n\n")
            
            # Transformation examples
            transformations = {}
            for model in processed_models:
                raw = model.get('raw_extracted_license', '').strip()
                standard = model.get('standardized_license_name', 'Unknown')
                if raw != standard and raw != '':
                    if raw not in transformations:
                        transformations[raw] = standard
            
            if transformations:
                f.write(f"LICENSE NAME TRANSFORMATIONS:\n")
                for raw_name in sorted(transformations.keys()):
                    standardized = transformations[raw_name]
                    f.write(f"  '{raw_name}' → '{standardized}'\n")
                f.write(f"\nTotal unique transformations: {len(transformations)}\n\n")
            
            # Models with no changes
            unchanged_models = []
            for model in processed_models:
                raw = model.get('raw_extracted_license', '').strip()
                standard = model.get('standardized_license_name', 'Unknown')
                if raw == standard and raw != '':
                    unchanged_models.append(model)
            
            if unchanged_models:
                f.write(f"MODELS WITH NO LICENSE CHANGES ({len(unchanged_models)} models):\n")
                for model in unchanged_models:
                    model_name = model.get('name', 'Unknown')
                    license_name = model.get('raw_extracted_license', 'Unknown')
                    f.write(f"  {model_name}: '{license_name}'\n")
                f.write(f"\n")
            
            # Detailed model listings - only models with changes
            f.write("DETAILED MODEL STANDARDIZATION RESULTS:\n")
            f.write("=" * 80 + "\n\n")
            
            # Filter to only models with license changes
            changed_models = []
            for model in processed_models:
                raw = model.get('raw_extracted_license', '').strip()
                standard = model.get('standardized_license_name', 'Unknown')
                if raw != standard or raw == '':  # Include models that were empty/unknown
                    changed_models.append(model)
            
            # Sort models by standardized license then model name
            sorted_models = sorted(
                changed_models, 
                key=lambda x: (x.get('standardized_license_name', ''), x.get('name', ''))
            )
            
            for i, model in enumerate(sorted_models, 1):
                f.write(f"MODEL {i}: {model.get('canonical_slug', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Key fields
                f.write(f"  ID                     : {model.get('id', 'Unknown')}\n")
                f.write(f"  Canonical Slug         : {model.get('canonical_slug', 'Unknown')}\n")
                f.write(f"  HuggingFace ID         : {model.get('hugging_face_id', 'Unknown')}\n")
                f.write(f"  Raw License            : {model.get('raw_extracted_license', 'Unknown')}\n")
                f.write(f"  Standardized License   : {model.get('standardized_license_name', 'Unknown')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Standardization report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    
    # Ensure output directory exists
    ensure_output_dir_exists()

    print("Other License Names Standardizer")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Load license names data from Stage-5
    license_data = load_license_names_data()
    if not license_data:
        print("No license names data loaded")
        return False
    
    # Load standardization configuration
    config = load_license_standardization_config()
    if not config:
        print("No standardization configuration loaded")
        return False
    
    # Process license standardization
    processed_models = process_license_standardization(license_data, config)
    
    if not processed_models:
        print("No models processed")
        return False
    
    # Save JSON output
    json_success = save_standardized_licenses_json(processed_models)
    
    # Generate report
    report_success = generate_standardization_report(processed_models)
    
    if json_success and report_success:
        print("="*60)
        print("STANDARDIZATION COMPLETE")
        print(f"Total models: {len(processed_models)}")
        print(f"JSON output: {json_success}")
        print(f"Report output: {report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("STANDARDIZATION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)