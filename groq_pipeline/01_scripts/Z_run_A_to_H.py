#!/usr/bin/env python3
"""
Groq Pipeline Orchestrator (Scripts A to H)
==========================================

This script orchestrates the execution of Groq pipeline scripts A through H:

A. A_scrape_production_models.py - Extract production models from Groq docs
B. B_scrape_rate_limits.py - Extract rate limits from Groq docs
C. C_scrape_modalities.py - Extract input/output modalities for each model
D. D_extract_meta_licenses.py - Extract Meta/Llama license information
E. E_extract_opensource_licenses.py - Extract HuggingFace-scraped & Google licenses
F. F_consolidate_all_licenses.py - Consolidate all license information
G. G_normalize_data.py - Normalize all extracted data into database-ready format
H. H_compare_pipeline_with_supabase.py - Compare pipeline with Supabase

Features:
- Sequential execution with dependency management
- Comprehensive error handling and logging
- Real-time progress reporting
- Execution timing and statistics
- Graceful failure handling with detailed error reporting

Author: AI Models Discovery Pipeline
Version: 1.0
Last Updated: 2025-09-20
"""

import os
import sys
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Script execution order and metadata
PIPELINE_SCRIPTS = [
    {
        'script': 'A_scrape_production_models.py',
        'name': 'Production Models Extraction',
        'description': 'Extract production models from Groq docs',
        'required': True
    },
    {
        'script': 'B_scrape_rate_limits.py',
        'name': 'Rate Limits Extraction',
        'description': 'Extract rate limits from Groq docs',
        'required': False  # Rate limits are not critical
    },
    {
        'script': 'C_scrape_modalities.py',
        'name': 'Modalities Extraction',
        'description': 'Extract input/output modalities for each model',
        'required': False  # Modalities are not critical
    },
    {
        'script': 'D_extract_meta_licenses.py',
        'name': 'Meta/Llama License Extraction',
        'description': 'Extract official Meta/Llama license information',
        'required': True
    },
    {
        'script': 'E_extract_opensource_licenses.py',
        'name': 'HuggingFace & Google License Extraction',
        'description': 'Extract HF-scraped and Google model licenses',
        'required': True
    },
    {
        'script': 'F_consolidate_all_licenses.py',
        'name': 'License Consolidation',
        'description': 'Consolidate all license information sources',
        'required': True
    },
    {
        'script': 'G_normalize_data.py',
        'name': 'Data Normalization',
        'description': 'Normalize all extracted data into database-ready format',
        'required': True
    },
    {
        'script': 'H_compare_pipeline_with_supabase.py',
        'name': 'Pipeline vs Supabase Comparison',
        'description': 'Compare pipeline output with Supabase data',
        'required': False  # Can fail without stopping pipeline
    }
]

def get_ist_timestamp() -> str:
    """Get current timestamp in IST format"""
    from datetime import timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime('%Y-%m-%d %I:%M:%S %p IST')

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def check_script_exists(script_path: Path) -> bool:
    """Check if script file exists and is executable"""
    return script_path.exists() and script_path.is_file()

def execute_script(script_info: Dict) -> Tuple[bool, str, float]:
    """
    Execute a single pipeline script.

    Args:
        script_info: Dictionary with script metadata

    Returns:
        Tuple of (success, output, duration_seconds)
    """
    script_name = script_info['script']
    script_path = Path(script_name)

    print(f"\n{'='*80}")
    print(f"EXECUTING: {script_info['name']}")
    print(f"{'='*80}")
    print(f"Script: {script_name}")
    print(f"Description: {script_info['description']}")
    print(f"Started at: {get_ist_timestamp()}")
    print(f"Required: {'Yes' if script_info['required'] else 'No'}")

    if not check_script_exists(script_path):
        error_msg = f"❌ ERROR: Script not found: {script_path}"
        print(error_msg)
        return False, error_msg, 0.0

    start_time = time.time()

    try:
        # Execute script with real-time output
        print(f"\n🚀 Starting execution...")
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )

        duration = time.time() - start_time

        # Print captured output
        if result.stdout:
            print(f"\n📤 STDOUT:")
            print(result.stdout)

        if result.stderr:
            print(f"\n📤 STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print(f"\n✅ SUCCESS: {script_info['name']} completed")
            print(f"Duration: {format_duration(duration)}")
            return True, result.stdout, duration
        else:
            error_msg = f"❌ FAILED: {script_info['name']} (exit code: {result.returncode})"
            print(error_msg)
            if result.stderr:
                print(f"Error details: {result.stderr}")
            return False, result.stderr or "Unknown error", duration

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        error_msg = f"❌ TIMEOUT: {script_info['name']} exceeded 30 minutes"
        print(error_msg)
        return False, error_msg, duration

    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"❌ EXCEPTION: {script_info['name']} failed with: {str(e)}"
        print(error_msg)
        return False, error_msg, duration

def generate_execution_report(results: List[Tuple[Dict, bool, str, float]]) -> str:
    """Generate comprehensive execution report"""

    total_duration = sum(result[3] for result in results)
    successful_scripts = [r for r in results if r[1]]
    failed_scripts = [r for r in results if not r[1]]

    report_lines = [
        "GROQ PIPELINE EXECUTION REPORT (A to H)",
        "=" * 80,
        f"Generated: {get_ist_timestamp()}",
        f"Total Execution Time: {format_duration(total_duration)}",
        "",
        "EXECUTION SUMMARY",
        "-" * 80,
        f"Total Scripts: {len(results)}",
        f"Successful: {len(successful_scripts)}",
        f"Failed: {len(failed_scripts)}",
        f"Success Rate: {(len(successful_scripts)/len(results)*100):.1f}%",
        ""
    ]

    # Detailed results
    report_lines.extend([
        "DETAILED RESULTS",
        "-" * 80
    ])

    for i, (script_info, success, output, duration) in enumerate(results, 1):
        status = "✅ SUCCESS" if success else "❌ FAILED"
        required = "REQUIRED" if script_info['required'] else "OPTIONAL"

        report_lines.extend([
            f"{i}. {script_info['name']}",
            f"   Script: {script_info['script']}",
            f"   Status: {status} ({required})",
            f"   Duration: {format_duration(duration)}",
            f"   Description: {script_info['description']}"
        ])

        if not success and output:
            # Include first few lines of error for debugging
            error_lines = output.split('\n')[:3]
            for line in error_lines:
                if line.strip():
                    report_lines.append(f"   Error: {line.strip()}")

        report_lines.append("")

    # Critical failures
    critical_failures = [r for r in failed_scripts if r[0]['required']]
    if critical_failures:
        report_lines.extend([
            "CRITICAL FAILURES",
            "-" * 80
        ])

        for script_info, success, output, duration in critical_failures:
            report_lines.extend([
                f"❌ {script_info['name']} ({script_info['script']})",
                f"   This is a REQUIRED script that failed",
                f"   Pipeline integrity may be compromised",
                ""
            ])

    # Recommendations
    report_lines.extend([
        "RECOMMENDATIONS",
        "-" * 80
    ])

    if len(failed_scripts) == 0:
        report_lines.append("✅ All scripts executed successfully! Pipeline is ready for I&J scripts.")
    elif len(critical_failures) > 0:
        report_lines.extend([
            "❌ Critical failures detected. Before proceeding:",
            "   1. Review and fix errors in required scripts",
            "   2. Re-run this orchestrator script",
            "   3. Only proceed to I&J scripts after all required scripts pass"
        ])
    else:
        report_lines.extend([
            "⚠️ Some optional scripts failed, but pipeline can continue:",
            "   1. Review optional script failures if needed",
            "   2. Pipeline data should be valid for I&J scripts",
            "   3. Consider fixing optional scripts for complete functionality"
        ])

    return "\n".join(report_lines)

def save_execution_report(report_content: str) -> str:
    """Save execution report to file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"../02_outputs/Z-groq-pipeline-A-to-H-report-{timestamp}.txt"

    try:
        os.makedirs("../02_outputs", exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"📄 Execution report saved to: {report_file}")
        return report_file
    except Exception as e:
        print(f"❌ Failed to save report: {e}")
        return ""

def main():
    """Main orchestrator function"""

    print("=" * 80)
    print("GROQ PIPELINE ORCHESTRATOR (SCRIPTS A TO H)")
    print("=" * 80)
    print(f"Started at: {get_ist_timestamp()}")
    print(f"Scripts to execute: {len(PIPELINE_SCRIPTS)}")
    print()

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"Working directory: {os.getcwd()}")

    # Show execution plan
    print("\nEXECUTION PLAN")
    print("-" * 80)
    for i, script_info in enumerate(PIPELINE_SCRIPTS, 1):
        required_status = "REQUIRED" if script_info['required'] else "OPTIONAL"
        print(f"{i}. {script_info['name']} ({required_status})")
        print(f"   Script: {script_info['script']}")
        print(f"   Description: {script_info['description']}")

    # Check if running in automated environment (GitHub Actions, etc.)
    # Note: Use Z_run_A_to_H_interactive.py for full interactive local execution
    is_automated = (
        os.getenv('GITHUB_ACTIONS') == 'true' or
        os.getenv('CI') == 'true' or
        os.getenv('AUTOMATED_EXECUTION') == 'true' or
        '--automated' in sys.argv
    )

    if is_automated:
        print(f"\n🤖 Running in automated mode - starting execution immediately...")
    else:
        print(f"\nPress Enter to start execution, or Ctrl+C to cancel...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Execution cancelled by user")
            return False

    # Execute all scripts
    results = []
    overall_start_time = time.time()

    for i, script_info in enumerate(PIPELINE_SCRIPTS, 1):
        print(f"\n🎯 STEP {i}/{len(PIPELINE_SCRIPTS)}")

        success, output, duration = execute_script(script_info)
        results.append((script_info, success, output, duration))

        # Check if we should continue
        if not success and script_info['required']:
            print(f"\n💥 CRITICAL FAILURE: Required script {script_info['script']} failed")
            print("Pipeline execution will continue, but results may be incomplete")
            # Continue execution but mark as critical failure

        # Brief pause between scripts
        if i < len(PIPELINE_SCRIPTS):
            time.sleep(2)

    overall_duration = time.time() - overall_start_time

    # Generate and display final report
    print(f"\n{'='*80}")
    print("EXECUTION COMPLETED")
    print(f"{'='*80}")

    report_content = generate_execution_report(results)
    print(report_content)

    # Save report
    report_file = save_execution_report(report_content)

    # Final summary
    successful_count = len([r for r in results if r[1]])
    failed_count = len(results) - successful_count
    critical_failures = len([r for r in results if not r[1] and r[0]['required']])

    print(f"\n🏁 FINAL SUMMARY")
    print(f"Total time: {format_duration(overall_duration)}")
    print(f"Success: {successful_count}/{len(results)} scripts")

    if critical_failures > 0:
        print(f"❌ Critical failures: {critical_failures}")
        print("⚠️ Pipeline integrity may be compromised")
        return False
    elif failed_count > 0:
        print(f"⚠️ Optional failures: {failed_count}")
        print("✅ Pipeline can proceed to I&J scripts")
        return True
    else:
        print("✅ All scripts completed successfully!")
        print("✅ Pipeline ready for I&J scripts")
        return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        sys.exit(1)