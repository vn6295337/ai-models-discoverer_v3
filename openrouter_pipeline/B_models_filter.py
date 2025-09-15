#!/usr/bin/env python3
"""
OpenRouter Models Filter
Filters models from A-api-models.json for free models only
"""
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Tuple

# Import output utilities
from output_utils import get_output_file_path, get_input_file_path, ensure_output_dir_exists

def load_filtering_config() -> Dict[str, Any]:
    """Load filtering configuration from JSON file"""
    config_file = "02_models_filtering_rules.json"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Loaded filtering rules from: {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load filtering config from {config_file}: {error}")
        return {}

def load_models_from_json(filename: str) -> List[Dict[str, Any]]:
    """
    Load models from JSON file
    
    Args:
        filename: Input JSON filename
        
    Returns:
        List of model dictionaries
    """
    try:
        if not os.path.exists(filename):
            print(f"ERROR: Input file not found: {filename}")
            return []
            
        with open(filename, 'r', encoding='utf-8') as json_file:
            models = json.load(json_file)
        
        print(f"✓ Loaded {len(models)} models from: {filename}")
        return models
        
    except (IOError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load models from {filename}: {error}")
        return []

def filter_models(models: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
    """
    Filter models using all configuration rules from 02_models_filtering_rules.json
    
    Args:
        models: List of all models
        config: Filtering configuration from 02_models_filtering_rules.json
        
    Returns:
        Tuple of (filtered_models, excluded_models_with_reasons)
    """
    filtered_models = []
    excluded_models = []
    
    free_criteria = config.get('free_model_criteria', {})
    exclude_keywords = config.get('exclude_keywords', [])
    exclude_reasons = config.get('exclude_reasons', {})
    
    for model in models:
        model_name = model.get('name', '')
        pricing = model.get('pricing', {})
        prompt_price = pricing.get('prompt', '0')
        completion_price = pricing.get('completion', '0')
        request_price = pricing.get('request', '0')
        
        # Check 1: Free model criteria (pricing)
        is_free = (prompt_price == free_criteria.get('pricing_prompt', 'Unknown') and 
                   completion_price == free_criteria.get('pricing_completion', 'Unknown') and 
                   request_price == free_criteria.get('pricing_request', 'Unknown'))
        
        if not is_free:
            excluded_models.append((model_name, exclude_reasons.get('billing_required', 'Requires billing/payment')))
            continue
        
        # Check 2: Exclude keywords
        model_name_lower = model_name.lower()
        excluded_for_keyword = False
        
        for keyword in exclude_keywords:
            if keyword.lower() in model_name_lower:
                reason = exclude_reasons.get(keyword, f'Contains excluded keyword: {keyword}')
                excluded_models.append((model_name, reason))
                excluded_for_keyword = True
                break
        
        if excluded_for_keyword:
            continue
        
        # If passed all filters, include the model
        filtered_models.append(model)
    
    print(f"Filtered {len(filtered_models)} models from {len(models)} total models")
    print(f"Excluded {len(excluded_models)} models for various criteria")
    
    return filtered_models, excluded_models

def save_filtered_models(models: List[Dict[str, Any]], filename: str) -> bool:
    """
    Save filtered models to JSON file
    
    Args:
        models: List of filtered model dictionaries
        filename: Output filename
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(models, json_file, indent=2)
        print(f"✓ Filtered models saved to: {filename}")
        return True
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save filtered models to {filename}: {error}")
        return False

def generate_filter_report(all_models: List[Dict[str, Any]], 
                          filtered_models: List[Dict[str, Any]], 
                          excluded_models: List[Tuple[str, str]],
                          filename: str) -> bool:
    """
    Generate report of filtering results
    
    Args:
        all_models: List of all models
        filtered_models: List of filtered models
        excluded_models: List of (model_name, reason) tuples
        filename: Output filename
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filename, 'w', encoding='utf-8') as report_file:
            # Header
            report_file.write("=" * 80 + "\n")
            report_file.write("OPENROUTER MODELS FILTER REPORT\n")
            report_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_file.write("=" * 80 + "\n\n")
            
            # Summary
            report_file.write(f"FILTERING SUMMARY:\n")
            report_file.write(f"  Total models processed: {len(all_models)}\n")
            report_file.write(f"  Models passed filters: {len(filtered_models)}\n")
            report_file.write(f"  Models excluded: {len(excluded_models)}\n")
            
            if all_models:
                pass_percentage = (len(filtered_models) / len(all_models)) * 100
                report_file.write(f"  Success rate: {pass_percentage:.1f}%\n\n")
            else:
                report_file.write("\n")
            
            # Exclusion breakdown
            if excluded_models:
                exclusion_stats = {}
                exclusion_details = {}
                for model_name, reason in excluded_models:
                    exclusion_stats[reason] = exclusion_stats.get(reason, 0) + 1
                    if reason not in exclusion_details:
                        exclusion_details[reason] = []
                    exclusion_details[reason].append(model_name)
                
                report_file.write(f"EXCLUSION BREAKDOWN:\n")
                for reason in sorted(exclusion_stats.keys()):
                    count = exclusion_stats[reason]
                    report_file.write(f"  {reason}: {count} models\n")
                report_file.write(f"\nTotal exclusion reasons: {len(exclusion_stats)}\n\n")
                
                # Detailed excluded models list
                report_file.write("DETAILED EXCLUDED MODELS:\n")
                report_file.write("=" * 80 + "\n\n")
                
                for reason in sorted(exclusion_details.keys()):
                    models = exclusion_details[reason]
                    report_file.write(f"EXCLUDED FOR: {reason.upper()} ({len(models)} models)\n")
                    report_file.write("-" * 50 + "\n")
                    
                    for i, model_name in enumerate(sorted(models), 1):
                        report_file.write(f"  {i:3d}. {model_name}\n")
                    
                    report_file.write("\n")
                
                report_file.write("=" * 80 + "\n\n")
            
            # Detailed filtered models list
            report_file.write("DETAILED FILTERED MODELS (PASSED ALL CRITERIA):\n")
            report_file.write("=" * 80 + "\n\n")
            
            # Organize filtered models by provider
            providers = {}
            for model in filtered_models:
                name = model.get('name', '')
                model_id = model.get('id', '')
                
                # Extract provider from name (before colon) or from ID
                if ': ' in name:
                    provider = name.split(': ', 1)[0].strip()
                    model_display_name = name.split(': ', 1)[1].strip()
                else:
                    # Fallback: extract provider from model ID
                    if '/' in model_id:
                        provider = model_id.split('/', 1)[0]
                        model_display_name = name or model_id
                    else:
                        provider = "Unknown"
                        model_display_name = name or model_id
                
                if provider not in providers:
                    providers[provider] = []
                providers[provider].append({
                    'id': model_id,
                    'name': name,
                    'display_name': model_display_name,
                    'pricing': model.get('pricing', {})
                })
            
            # Sort providers by count (descending order)
            sorted_providers = sorted(providers.items(), key=lambda x: len(x[1]), reverse=True)
            
            # Report filtered models by provider
            total_models_listed = 0
            for provider, models in sorted_providers:
                report_file.write(f"PROVIDER: {provider.upper()} ({len(models)} models)\n")
                report_file.write("-" * 50 + "\n")
                
                # Sort models within provider
                sorted_models = sorted(models, key=lambda x: x['display_name'].lower())
                
                for i, model in enumerate(sorted_models, 1):
                    model_id = model['id']
                    model_name = model['name']
                    pricing = model['pricing']
                    
                    report_file.write(f"  {i:2d}. {model_name}\n")
                    report_file.write(f"      ID: {model_id}\n")
                    
                    # Show pricing info
                    prompt_price = pricing.get('prompt', 'N/A')
                    completion_price = pricing.get('completion', 'N/A')
                    request_price = pricing.get('request', 'N/A')
                    report_file.write(f"      Pricing: prompt={prompt_price}, completion={completion_price}, request={request_price}\n")
                    report_file.write("\n")
                
                total_models_listed += len(models)
                report_file.write("\n")
            
            # Summary
            report_file.write("=" * 80 + "\n")
            report_file.write(f"FILTERED MODELS SUMMARY:\n")
            report_file.write(f"  Total providers: {len(providers)}\n")
            report_file.write(f"  Total models listed: {total_models_listed}\n")
            report_file.write(f"  Expected models: {len(filtered_models)}\n")
            
            if total_models_listed != len(filtered_models):
                report_file.write(f"  ⚠️  MISMATCH: {len(filtered_models) - total_models_listed} models missing from report\n")
            else:
                report_file.write(f"  ✓ All filtered models accounted for\n")
        
        print(f"✓ Filter report saved to: {filename}")
        return True
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save filter report to {filename}: {error}")
        return False

def main():
    """Main execution function"""
    print("OpenRouter Models Filter")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)

    # Ensure output directory exists
    ensure_output_dir_exists()

    # Load filtering configuration
    config = load_filtering_config()

    # Input and output filenames with full paths
    input_filename = get_input_file_path("A-api-models.json")
    output_filename = get_output_file_path("B-filtered-models.json")
    report_filename = get_output_file_path("B-filtered-models-report.txt")

    # Load all models
    all_models = load_models_from_json(input_filename)
    
    if not all_models:
        print("No models loaded from input file")
        return False
    
    # Filter models using all config rules
    filtered_models, excluded_models = filter_models(all_models, config)
    
    if not filtered_models:
        print("No models passed the filters")
        return False
    
    # Save filtered models
    save_success = save_filtered_models(filtered_models, output_filename)
    
    # Generate filter report
    report_success = generate_filter_report(all_models, filtered_models, excluded_models, report_filename)
    
    if save_success and report_success:
        print("="*60)
        print("FILTERING COMPLETE")
        print(f"Input: {len(all_models)} total models")
        print(f"Output: {len(filtered_models)} filtered models")
        print(f"Excluded: {len(excluded_models)} models")
        print(f"JSON output: {output_filename}")
        print(f"Report output: {report_filename}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("FILTERING FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)