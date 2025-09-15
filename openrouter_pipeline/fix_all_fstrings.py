#!/usr/bin/env python3
"""
Fix f-string issues across all Python files in the pipeline
"""
import os
import re
import glob

def fix_fstrings_in_file(filename):
    """Fix f-string issues in a single file"""
    print(f"Processing {filename}...")

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count initial issues
    initial_issues = len(re.findall(r'"[^"]*\{[^}]+\}[^"]*"', content))

    # Find and fix f-string patterns
    # Pattern: "text {variable} more text" -> f"text {variable} more text"
    def fix_fstring(match):
        line = match.group(0)
        # Skip if it's already an f-string or raw string
        if line.startswith(('f"', 'rf"', 'fr"', 'r"')) or '\\{' in line:
            return line
        # Add f prefix
        return 'f' + line

    # Fix print statements and variable assignments with interpolation
    content = re.sub(r'(?<!f)(?<!r)(?<!rf)(?<!fr)"[^"]*\{[^}]+\}[^"]*"', fix_fstring, content)

    # Count final issues
    final_issues = len(re.findall(r'(?<!f)(?<!r)(?<!rf)(?<!fr)"[^"]*\{[^}]+\}[^"]*"', content))

    # Write back only if changes were made
    if initial_issues > final_issues:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Fixed {initial_issues - final_issues} f-string issues")
    else:
        print(f"  No f-string issues found")

def main():
    """Fix f-strings in all Python files"""
    python_files = glob.glob("*.py")

    for filename in python_files:
        if filename != 'fix_all_fstrings.py':  # Skip this script
            fix_fstrings_in_file(filename)

    print("F-string fixing complete!")

if __name__ == "__main__":
    main()