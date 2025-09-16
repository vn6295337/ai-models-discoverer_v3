#!/usr/bin/env python3
"""
OpenRouter Models Filter
Filters models from A-fetched-api-models.json for free models only
"""
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Tuple

# Import output utilities
import sys; import os; sys.path.append(os.path.join(os.path.dirname(__file__), "..", "04_utils")); from output_utils import get_output_file_path, get_input_file_path, ensure_output_dir_exists

def load_filtering_config() -> Dict[str, Any]:
    """Load filtering configuration from JSON file"""
    config_file = "../03_configs/02_models_filtering_rules.json"
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

def filter_models(models: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, List[Tuple[str, str]]]]:
    """
    Filter models using sequential filtering steps

    Args:
        models: List of all models
        config: Filtering configuration from 02_models_filtering_rules.json

    Returns:
        Tuple of (filtered_models, excluded_models_by_step)
    """
    free_criteria = config.get('free_model_criteria', {})
    billing_keywords = config.get('billing_keywords', [])
    exclude_keywords = config.get('exclude_keywords', [])
    exclude_reasons = config.get('exclude_reasons', {})

    # Initialize tracking for each step
    excluded_by_step = {
        'step1_pricing': [],
        'step2_billing': [],
        'step3_keywords': []
    }

    print(f"Starting sequential filtering with {len(models)} total models")

    # STEP 1: Free model criteria (pricing check)
    step1_passed = []
    for model in models:
        model_name = model.get('name', '')
        pricing = model.get('pricing', {})
        prompt_price = pricing.get('prompt', '0')
        completion_price = pricing.get('completion', '0')
        request_price = pricing.get('request', '0')

        is_free = (prompt_price == free_criteria.get('pricing_prompt', 'Unknown') and
                   completion_price == free_criteria.get('pricing_completion', 'Unknown') and
                   request_price == free_criteria.get('pricing_request', 'Unknown'))

        if is_free:
            step1_passed.append(model)
        else:
            excluded_by_step['step1_pricing'].append((model_name, exclude_reasons.get('billing_required', 'Requires billing/payment')))

    print(f"Step 1 (Pricing): {len(step1_passed)} models passed, {len(excluded_by_step['step1_pricing'])} excluded")

    # STEP 2: Billing description check
    step2_passed = []
    for model in step1_passed:
        model_name = model.get('name', '')
        description = model.get('description', '').lower()

        has_billing_requirement = False
        for billing_keyword in billing_keywords:
            if billing_keyword.lower() in description:
                excluded_by_step['step2_billing'].append((model_name, f"{exclude_reasons.get('billing_in_description', 'Description indicates billing requirements')}: '{billing_keyword}'"))
                has_billing_requirement = True
                break

        if not has_billing_requirement:
            step2_passed.append(model)

    print(f"Step 2 (Billing): {len(step2_passed)} models passed, {len(excluded_by_step['step2_billing'])} excluded")

    # STEP 3: Keyword exclusion
    step3_passed = []
    for model in step2_passed:
        model_name = model.get('name', '')
        model_name_lower = model_name.lower()

        excluded_for_keyword = False
        for keyword in exclude_keywords:
            if keyword.lower() in model_name_lower:
                reason = exclude_reasons.get(keyword, f'Contains excluded keyword: {keyword}')
                excluded_by_step['step3_keywords'].append((model_name, reason))
                excluded_for_keyword = True
                break

        if not excluded_for_keyword:
            step3_passed.append(model)

    print(f"Step 3 (Keywords): {len(step3_passed)} models passed, {len(excluded_by_step['step3_keywords'])} excluded")

    # Final summary
    total_excluded = sum(len(excluded_list) for excluded_list in excluded_by_step.values())
    print(f"Sequential filtering complete: {len(step3_passed)} final models, {total_excluded} total excluded")

    return step3_passed, excluded_by_step

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
                          excluded_by_step: Dict[str, List[Tuple[str, str]]],
                          filename: str) -> bool:
    """
    Generate report of sequential filtering results

    Args:
        all_models: List of all models
        filtered_models: List of filtered models
        excluded_by_step: Dict with excluded models by filtering step
        filename: Output filename

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filename, 'w', encoding='utf-8') as report_file:
            # Header
            report_file.write("=" * 80 + "\n")
            report_file.write("OPENROUTER MODELS SEQUENTIAL FILTER REPORT\n")
            report_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_file.write("=" * 80 + "\n\n")

            # Calculate totals
            total_excluded = sum(len(excluded_list) for excluded_list in excluded_by_step.values())

            # Summary
            report_file.write(f"SEQUENTIAL FILTERING SUMMARY:\n")
            report_file.write(f"  Total models processed: {len(all_models)}\n")
            report_file.write(f"  Models passed all filters: {len(filtered_models)}\n")
            report_file.write(f"  Models excluded: {total_excluded}\n")

            if all_models:
                pass_percentage = (len(filtered_models) / len(all_models)) * 100
                report_file.write(f"  Success rate: {pass_percentage:.1f}%\n\n")
            else:
                report_file.write("\n")

            # Step-by-step breakdown
            report_file.write(f"STEP-BY-STEP FILTERING BREAKDOWN:\n")
            models_remaining = len(all_models)

            # Step 1: Pricing Filter
            step1_excluded = len(excluded_by_step['step1_pricing'])
            models_remaining -= step1_excluded
            report_file.write(f"  Step 1 - Free Pricing Filter:\n")
            report_file.write(f"    Input: {len(all_models)} models\n")
            report_file.write(f"    Excluded: {step1_excluded} models (non-free pricing)\n")
            report_file.write(f"    Remaining: {models_remaining} models\n\n")

            # Step 2: Billing Description Filter
            step2_excluded = len(excluded_by_step['step2_billing'])
            models_remaining -= step2_excluded
            report_file.write(f"  Step 2 - Billing Description Filter:\n")
            report_file.write(f"    Input: {models_remaining + step2_excluded} models\n")
            report_file.write(f"    Excluded: {step2_excluded} models (billing requirements in description)\n")
            report_file.write(f"    Remaining: {models_remaining} models\n\n")

            # Step 3: Keyword Filter
            step3_excluded = len(excluded_by_step['step3_keywords'])
            models_remaining -= step3_excluded
            report_file.write(f"  Step 3 - Keyword Filter:\n")
            report_file.write(f"    Input: {models_remaining + step3_excluded} models\n")
            report_file.write(f"    Excluded: {step3_excluded} models (preview/experimental/beta)\n")
            report_file.write(f"    Final: {models_remaining} models\n\n")

            # Step 1 Summary (no details as requested)
            report_file.write("=" * 80 + "\n")
            report_file.write("STEP 1 - FREE PRICING FILTER RESULTS\n")
            report_file.write("=" * 80 + "\n")
            report_file.write(f"Excluded {step1_excluded} models with non-free pricing (details omitted due to volume)\n\n")

            # Step 2 Detailed Results (as requested)
            report_file.write("=" * 80 + "\n")
            report_file.write("STEP 2 - BILLING DESCRIPTION FILTER RESULTS (DETAILED)\n")
            report_file.write("=" * 80 + "\n")

            if excluded_by_step['step2_billing']:
                report_file.write(f"Found {step2_excluded} models with billing requirements in description:\n\n")

                for i, (model_name, reason) in enumerate(excluded_by_step['step2_billing'], 1):
                    report_file.write(f"  {i:2d}. {model_name}\n")
                    report_file.write(f"      Reason: {reason}\n\n")
            else:
                report_file.write("No models found with billing requirements in description.\n\n")

            # Step 3 Detailed Results
            report_file.write("=" * 80 + "\n")
            report_file.write("STEP 3 - KEYWORD FILTER RESULTS (DETAILED)\n")
            report_file.write("=" * 80 + "\n")

            if excluded_by_step['step3_keywords']:
                # Group by reason for better organization
                keyword_groups = {}
                for model_name, reason in excluded_by_step['step3_keywords']:
                    if reason not in keyword_groups:
                        keyword_groups[reason] = []
                    keyword_groups[reason].append(model_name)

                for reason in sorted(keyword_groups.keys()):
                    models = keyword_groups[reason]
                    report_file.write(f"EXCLUDED FOR: {reason.upper()} ({len(models)} models)\n")
                    report_file.write("-" * 50 + "\n")

                    for i, model_name in enumerate(sorted(models), 1):
                        report_file.write(f"  {i:2d}. {model_name}\n")

                    report_file.write("\n")
            else:
                report_file.write("No models excluded for keywords.\n\n")

            # Final filtered models organized by provider
            report_file.write("=" * 80 + "\n")
            report_file.write("FINAL FILTERED MODELS (PASSED ALL FILTERS)\n")
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
                    'pricing': model.get('pricing', {}),
                    'description': model.get('description', '')
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

            # Final Summary
            report_file.write("=" * 80 + "\n")
            report_file.write(f"FINAL SUMMARY:\n")
            report_file.write(f"  Total providers: {len(providers)}\n")
            report_file.write(f"  Total models passed all filters: {len(filtered_models)}\n")
            report_file.write(f"  Models excluded by pricing: {step1_excluded}\n")
            report_file.write(f"  Models excluded by billing description: {step2_excluded}\n")
            report_file.write(f"  Models excluded by keywords: {step3_excluded}\n")
            report_file.write(f"  Total exclusions: {total_excluded}\n")

            if total_models_listed != len(filtered_models):
                report_file.write(f"  ⚠️  MISMATCH: {len(filtered_models) - total_models_listed} models missing from report\n")
            else:
                report_file.write(f"  ✓ All filtered models accounted for\n")

        print(f"✓ Sequential filter report saved to: {filename}")
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
    input_filename = get_input_file_path("A-fetched-api-models.json")
    output_filename = get_output_file_path("B-filtered-models.json")
    report_filename = get_output_file_path("B-filtered-models-report.txt")

    # Load all models
    all_models = load_models_from_json(input_filename)
    
    if not all_models:
        print("No models loaded from input file")
        return False
    
    # Filter models using sequential filtering
    filtered_models, excluded_by_step = filter_models(all_models, config)

    if not filtered_models:
        print("No models passed the filters")
        return False

    # Save filtered models
    save_success = save_filtered_models(filtered_models, output_filename)

    # Generate filter report
    report_success = generate_filter_report(all_models, filtered_models, excluded_by_step, report_filename)

    if save_success and report_success:
        total_excluded = sum(len(excluded_list) for excluded_list in excluded_by_step.values())
        print("="*60)
        print("FILTERING COMPLETE")
        print(f"Input: {len(all_models)} total models")
        print(f"Output: {len(filtered_models)} filtered models")
        print(f"Excluded: {total_excluded} models")
        print(f"  Step 1 (Pricing): {len(excluded_by_step['step1_pricing'])} excluded")
        print(f"  Step 2 (Billing): {len(excluded_by_step['step2_billing'])} excluded")
        print(f"  Step 3 (Keywords): {len(excluded_by_step['step3_keywords'])} excluded")
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