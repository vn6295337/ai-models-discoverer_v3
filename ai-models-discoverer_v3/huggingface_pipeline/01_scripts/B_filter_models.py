#!/usr/bin/env python3
"""
HuggingFace Models Post-Fetch Filter
Applies metadata-based filters to fetched models

Post-fetch filters applied (from 03_postfetch_filters.json):
- not_private: Check if private field is false

Note: Inference API filtering now done at pre-fetch level (inference=warm)

Outputs: Filtered models JSON and summary report
"""
import json
import sys
from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path


def ensure_output_dir_exists():
    """Create output directory if it doesn't exist"""
    output_dir = Path(__file__).parent.parent / "02_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_output_file_path(filename: str) -> Path:
    """Get full path for output file"""
    output_dir = ensure_output_dir_exists()
    return output_dir / filename


def load_postfetch_filters() -> Dict[str, Any]:
    """Load post-fetch filters from 03_postfetch_filters.json"""
    config_file = Path(__file__).parent.parent / "03_configs" / "03_postfetch_filters.json"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"WARNING: Failed to load postfetch filters from {config_file}: {error}")
        print("Using no postfetch filters")
        return {}


def apply_filters(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply post-fetch filters to models

    Args:
        models: List of model dictionaries

    Returns:
        List of filtered model dictionaries
    """
    config = load_postfetch_filters()
    required_filters = config.get('required_filters', {})

    print(f"\nApplying post-fetch filters...")
    print(f"Total models before filtering: {len(models)}")

    filtered_models = []
    filter_stats = {
        'total': len(models),
        'private_models': 0,
        'passed': 0
    }

    for model in models:
        # Check not_private filter
        if required_filters.get('not_private', {}).get('value') is False:
            if model.get('private', False):
                filter_stats['private_models'] += 1
                continue

        # Model passed all filters
        filtered_models.append(model)
        filter_stats['passed'] += 1

    print(f"\nFilter Statistics:")
    print(f"  Total input models: {filter_stats['total']}")
    print(f"  Rejected - private models: {filter_stats['private_models']}")
    print(f"  Passed all filters: {filter_stats['passed']}")
    print(f"  Pass rate: {filter_stats['passed']/filter_stats['total']*100:.1f}%")

    return filtered_models


def save_models_to_compact_json(models: List[Dict[str, Any]], filename: Path) -> bool:
    """
    Save models data to compact JSON file (no pretty printing)

    Args:
        models: List of model dictionaries
        filename: Output filename

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(models, json_file, separators=(',', ':'))
        print(f"✓ Filtered models saved to: {filename}")
        return True
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save models to {filename}: {error}")
        return False


def generate_summary_report(models: List[Dict[str, Any]], filename: Path) -> bool:
    """
    Generate summary report of filtered models

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
            report_file.write("HUGGINGFACE FILTERED MODELS REPORT\n")
            report_file.write(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
            report_file.write("=" * 80 + "\n\n")

            # Summary
            report_file.write(f"SUMMARY:\n")
            report_file.write(f"  Total models after filtering: {len(models)}\n\n")

            # Pipeline tag distribution
            pipeline_tags = {}
            for model in models:
                tag = model.get('pipeline_tag', 'unknown')
                pipeline_tags[tag] = pipeline_tags.get(tag, 0) + 1

            report_file.write(f"PIPELINE TAG DISTRIBUTION:\n")
            for tag, count in sorted(pipeline_tags.items(), key=lambda x: x[1], reverse=True):
                report_file.write(f"  {tag}: {count}\n")
            report_file.write(f"\nTotal pipeline tags: {len(pipeline_tags)}\n\n")

            # Filters applied
            report_file.write(f"FILTERS APPLIED:\n")
            report_file.write(f"  ✓ private = false\n")
            report_file.write(f"\nNOTE: inference=warm filter applied at pre-fetch level (free serverless API only)\n")

        print(f"✓ Summary report saved to: {filename}")
        return True

    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {filename}: {error}")
        return False


def main():
    """Main execution function"""
    print("HuggingFace Models Post-Fetch Filter")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)

    # Input/output filenames
    input_filename = get_output_file_path("A-fetched-api-models.json")
    output_filename = get_output_file_path("B-filtered-models.json")
    report_filename = get_output_file_path("B-filtered-models-report.txt")

    # Load fetched models
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            models = json.load(f)
        print(f"Loaded {len(models)} models from: {input_filename}")
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load input file {input_filename}: {error}")
        return False

    # Apply filters
    filtered_models = apply_filters(models)

    if not filtered_models:
        print("WARNING: No models passed filters")
        return False

    # Save filtered models to JSON
    json_success = save_models_to_compact_json(filtered_models, output_filename)

    # Generate summary report
    report_success = generate_summary_report(filtered_models, report_filename)

    if json_success and report_success:
        print("="*60)
        print("FILTERING COMPLETE")
        print(f"Total filtered models: {len(filtered_models)}")
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
