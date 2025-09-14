#!/usr/bin/env python3
"""
Test script to demonstrate enhanced difference reporting
Simulates having both pipeline and Supabase data with differences
"""

import json
from pathlib import Path

# Mock data to simulate pipeline vs Supabase differences
pipeline_data = [
    {
        "human_readable_name": "Test Model A",
        "license_name": "MIT",
        "license_info_text": "info",
        "model_provider": "OpenAI",
        "input_modalities": "Text"
    },
    {
        "human_readable_name": "Test Model B",
        "license_name": "Apache-2.0",
        "license_info_text": "",
        "model_provider": "Google",
        "input_modalities": "Text, Image"
    },
    {
        "human_readable_name": "Test Model C",
        "license_name": "QWEN",
        "license_info_text": "info",
        "model_provider": "Alibaba Cloud",
        "input_modalities": "Text"
    }
]

supabase_data = [
    {
        "human_readable_name": "Test Model A",
        "license_name": "MIT",
        "license_info_text": "info",
        "model_provider": "OpenAI",
        "input_modalities": "Text"
    },
    {
        "human_readable_name": "Test Model B",
        "license_name": "Apache-2.0",
        "license_info_text": None,  # NULL value from Supabase (should match empty string in pipeline)
        "model_provider": "Google",
        "input_modalities": "Text, Image"
    },
    {
        "human_readable_name": "Test Model C",
        "license_name": "Qwen",  # Different case from pipeline
        "license_info_text": "info",
        "model_provider": "Alibaba Cloud",
        "input_modalities": "Text"
    }
]

def create_test_comparison_report():
    """Generate test comparison report with differences"""

    # Create lookup dictionaries by human_readable_name
    pipeline_lookup = {model.get('human_readable_name', ''): model for model in pipeline_data}
    supabase_lookup = {model.get('human_readable_name', ''): model for model in supabase_data}

    # Get all unique model names
    all_model_names = set(pipeline_lookup.keys()) | set(supabase_lookup.keys())
    all_model_names.discard('')

    # Fields to compare
    fields_to_compare = [
        'license_name',
        'license_info_text',
        'model_provider',
        'input_modalities'
    ]

    # Calculate statistics
    models_in_both = []
    models_pipeline_only = []
    models_supabase_only = []
    field_stats = {field: {'exact_matches': 0, 'differences': 0, 'pipeline_missing': 0, 'supabase_missing': 0, 'difference_details': []} for field in fields_to_compare}

    for model_name in all_model_names:
        pipeline_model = pipeline_lookup.get(model_name, {})
        supabase_model = supabase_lookup.get(model_name, {})

        if pipeline_model and supabase_model:
            models_in_both.append(model_name)
            # Compare fields for models in both systems
            for field in fields_to_compare:
                pipeline_value = str(pipeline_model.get(field, '')).strip()
                # Handle Supabase NULL values properly - convert None to empty string
                supabase_raw = supabase_model.get(field, '')
                supabase_value = '' if supabase_raw is None else str(supabase_raw).strip()

                if pipeline_value == supabase_value:
                    field_stats[field]['exact_matches'] += 1
                else:
                    field_stats[field]['differences'] += 1
                    # Store detailed difference information
                    diff_detail = {
                        'model': model_name,
                        'pipeline_value': pipeline_value,
                        'supabase_value': supabase_value
                    }
                    field_stats[field]['difference_details'].append(diff_detail)

                    if not pipeline_value:
                        field_stats[field]['pipeline_missing'] += 1
                    if not supabase_value:
                        field_stats[field]['supabase_missing'] += 1
        elif pipeline_model:
            models_pipeline_only.append(model_name)
        elif supabase_model:
            models_supabase_only.append(model_name)

    # Generate test report
    report_content = []
    report_content.append("FIELD COMPARISON REPORT: PIPELINE vs SUPABASE (TEST)")
    report_content.append("=" * 80)
    report_content.append("")

    # Summary Statistics
    report_content.append("SUMMARY STATISTICS")
    report_content.append("-" * 80)
    report_content.append("")

    # Calculate models with differences for overall statistics
    models_with_differences_count = 0
    if models_in_both:
        for model_name in models_in_both:
            pipeline_model = pipeline_lookup[model_name]
            supabase_model = supabase_lookup[model_name]
            has_differences = False
            for field in fields_to_compare:
                pipeline_value = str(pipeline_model.get(field, '')).strip()
                # Handle Supabase NULL values properly
                supabase_raw = supabase_model.get(field, '')
                supabase_value = '' if supabase_raw is None else str(supabase_raw).strip()
                if pipeline_value != supabase_value:
                    has_differences = True
                    break
            if has_differences:
                models_with_differences_count += 1

    # Overall Statistics
    report_content.append("1. OVERALL STATISTICS:")
    report_content.append(f"   • Total models processed: {len(all_model_names)}")
    report_content.append(f"   • Models in both systems: {len(models_in_both)}")
    if models_in_both:
        report_content.append(f"   • Models with differences: {models_with_differences_count}")
    report_content.append(f"   • Models in pipeline only (not in Supabase): {len(models_pipeline_only)}")
    report_content.append(f"   • Models in Supabase only (not in pipeline): {len(models_supabase_only)}")
    report_content.append("")

    # Field-by-Field Analysis (only if there are models in both systems)
    if models_in_both:
        report_content.append("2. FIELD-BY-FIELD ANALYSIS (for models in both systems):")
        for field in fields_to_compare:
            stats = field_stats[field]
            report_content.append(f"   • {field}:")
            report_content.append(f"     - Exact matches: {stats['exact_matches']}")
            report_content.append(f"     - Differences: {stats['differences']}")
            if stats['pipeline_missing'] > 0:
                report_content.append(f"     - Missing in pipeline: {stats['pipeline_missing']}")
            if stats['supabase_missing'] > 0:
                report_content.append(f"     - Missing in Supabase: {stats['supabase_missing']}")

            # Show detailed differences for each field
            if stats['difference_details']:
                report_content.append(f"     - Specific differences:")
                for diff in stats['difference_details']:  # Show all differences
                    model_name = diff['model'][:30] + "..." if len(diff['model']) > 30 else diff['model']
                    pipeline_val = diff['pipeline_value'][:20] + "..." if len(diff['pipeline_value']) > 20 else diff['pipeline_value']
                    supabase_val = diff['supabase_value'][:20] + "..." if len(diff['supabase_value']) > 20 else diff['supabase_value']
                    report_content.append(f"       * {model_name}: Pipeline='{pipeline_val}' vs Supabase='{supabase_val}'")
        report_content.append("")

    return '\n'.join(report_content)

if __name__ == "__main__":
    report = create_test_comparison_report()
    print(report)