#!/usr/bin/env python3
"""
Inspect how NULL values are returned from Supabase
"""

import json
from pathlib import Path

# Check how the comparison data looks in the current report
report_file = Path(__file__).parent / "pipeline-outputs" / "S-field-comparison-report.txt"

if report_file.exists():
    print("Checking current report for NULL/None patterns...")
    with open(report_file, 'r') as f:
        lines = f.readlines()

    # Look for lines with "vs Supabase=" to see how NULL values appear
    supabase_patterns = []
    for i, line in enumerate(lines):
        if "vs Supabase=" in line and "None" in line:
            supabase_patterns.append(line.strip())

    print(f"\nFound {len(supabase_patterns)} lines with 'None' in Supabase values:")
    for pattern in supabase_patterns[:5]:  # Show first 5 examples
        print(f"  {pattern}")

    if len(supabase_patterns) > 5:
        print(f"  ... and {len(supabase_patterns) - 5} more")

# Also check what the actual pipeline data looks like for empty fields
pipeline_file = Path(__file__).parent / "pipeline-outputs" / "R_filtered_db_data.json"
if pipeline_file.exists():
    print(f"\nChecking pipeline data for empty field patterns...")
    with open(pipeline_file, 'r') as f:
        data = json.load(f)

    if data:
        # Check first few models for empty/null patterns
        sample_model = data[0]
        print(f"\nSample pipeline model fields:")
        for field in ['license_info_text', 'license_info_url']:
            value = sample_model.get(field)
            print(f"  {field}: {repr(value)} (type: {type(value).__name__})")

        # Count empty vs non-empty for these problematic fields
        for field in ['license_info_text', 'license_info_url']:
            empty_count = sum(1 for model in data if not model.get(field, '').strip())
            non_empty_count = sum(1 for model in data if model.get(field, '').strip())
            print(f"\n{field} in pipeline:")
            print(f"  Empty/blank: {empty_count}")
            print(f"  Has data: {non_empty_count}")

else:
    print("Pipeline data file not found")