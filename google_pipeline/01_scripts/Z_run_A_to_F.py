#!/usr/bin/env python3
"""
Google Pipeline Orchestrator
Executes the complete Google AI models discovery pipeline from A to F

Pipeline Flow:
A → B → C → D → E → F
"""

import subprocess
import sys
import time
import os
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Import IST timestamp utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '04_utils'))
from output_utils import get_ist_timestamp, get_ist_timestamp_detailed


def run_script(script_name: str, use_venv: bool = True) -> Tuple[bool, str]:
    """
    Run a pipeline script and return success status and output

    Args:
        script_name: Name of the script to run
        use_venv: Whether to use virtual environment Python

    Returns:
        Tuple of (success, output_message)
    """
    try:
        print(f"🔄 Running {script_name}...")
        start_time = time.time()

        # Determine Python executable
        github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        if github_actions or not use_venv:
            python_exec = sys.executable
        elif os.path.exists("google_env/bin/python"):
            python_exec = "google_env/bin/python"
        else:
            python_exec = sys.executable

        result = subprocess.run(
            [python_exec, script_name],
            capture_output=True,
            text=True,
            timeout=900,  # 15 minute timeout per script
            cwd=os.path.dirname(__file__)  # Run from 01_scripts directory
        )

        end_time = time.time()
        duration = end_time - start_time

        if result.returncode == 0:
            print(f"✅ {script_name} completed successfully ({duration:.1f}s)")
            return True, f"Success in {duration:.1f}s"
        else:
            print(f"❌ {script_name} failed with return code {result.returncode}")
            print(f"   Error output: {result.stderr[:1000]}")
            if result.stdout:
                print(f"   Standard output: {result.stdout[-500:]}")
            return False, f"Failed: {result.stderr[:1000]}"

    except subprocess.TimeoutExpired:
        print(f"⏰ {script_name} timed out after 15 minutes")
        return False, "Timed out after 15 minutes"
    except Exception as e:
        print(f"💥 {script_name} crashed: {str(e)}")
        return False, f"Crashed: {str(e)}"


def generate_pipeline_report(execution_log: List[Tuple[str, bool, str]], total_time: float) -> None:
    """
    Generate comprehensive pipeline execution report

    Args:
        execution_log: List of (stage, success, message) tuples
        total_time: Total pipeline execution time in seconds
    """
    script_dir = Path(__file__).parent
    report_file = script_dir.parent / "02_outputs" / "Z-pipeline-report.txt"

    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("GOOGLE MODELS PIPELINE EXECUTION REPORT\n")
            f.write(f"Execution Date: {get_ist_timestamp()}\n")
            f.write(f"Total Pipeline Duration: {total_time:.1f} seconds\n")
            f.write("\n")

            # Summary
            total_stages = len(execution_log)
            successful_stages = sum(1 for _, success, _ in execution_log if success)
            failed_stages = total_stages - successful_stages

            f.write("=== EXECUTION SUMMARY ===\n")
            f.write(f"Stages Executed: {total_stages}\n")
            f.write(f"Successful: {successful_stages}\n")
            f.write(f"Failed: {failed_stages}\n")
            f.write("\n")

            # Stage-by-stage results
            f.write("=== STAGE EXECUTION DETAILS ===\n")
            stage_names = {
                "A_fetch_api_models.py": "API Data Extraction",
                "B_filter_models.py": "Model Filtering",
                "C_scrape_modalities.py": "Modality Scraping",
                "D_enrich_modalities.py": "Modality Enrichment",
                "E_create_db_data.py": "Data Normalization",
                "F_compare_pipeline_with_supabase.py": "Pipeline Comparison"
            }

            for i, (stage, success, message) in enumerate(execution_log, 1):
                status = "✅ SUCCESS" if success else "❌ FAILED"
                stage_name = stage_names.get(stage, "Unknown")
                duration = message.split()[-1] if "Success in" in message else "N/A"

                f.write(f"Stage {i}: {stage_name}\n")
                f.write(f"  Script: {stage}\n")
                f.write(f"  Status: {status}\n")
                if "Success in" in message:
                    f.write(f"  Duration: {duration}\n")
                f.write(f"\n")

        print(f"📄 Pipeline report saved to: {report_file}")

    except Exception as e:
        print(f"❌ Failed to generate pipeline report: {e}")

def setup_environment(skip_venv: bool = False) -> bool:
    """
    Setup development environment

    Args:
        skip_venv: If True, skip virtual environment setup (for CI/CD environments)

    Returns:
        bool: True if setup successful, False otherwise
    """
    print("\n" + "=" * 80)
    print("🔧 ENVIRONMENT SETUP")
    print("=" * 80)

    # Auto-detect GitHub Actions or use explicit flag
    github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    if github_actions or skip_venv:
        environment_type = "GitHub Actions" if github_actions else "CI/CD"
        print(f"🚀 Detected {environment_type} environment")
        print("   Skipping virtual environment setup - using pre-installed dependencies")
        print(f"✅ Environment setup completed ({environment_type} mode)")
        return True

    try:
        # Use script directory as reference point for consistent path resolution
        script_dir = Path(__file__).parent  # 01_scripts
        config_dir = script_dir.parent / "03_configs"  # google_pipeline/03_configs
        output_dir = script_dir.parent / "02_outputs"  # google_pipeline/02_outputs

        # Check configuration directory
        if not config_dir.exists():
            print("❌ Configuration directory not found")
            return False
        print("✅ Configuration directory found")

        # Check output directory
        if not output_dir.exists():
            output_dir.mkdir(exist_ok=True)
            print("✅ Output directory created")
        else:
            print(f"✅ Output directory exists: {output_dir.resolve()}")

        # Check requirements file
        requirements_file = config_dir / "requirements.txt"
        if requirements_file.exists():
            print(f"✅ Requirements file found: {requirements_file}")
        else:
            print("⚠️  No requirements.txt found")

        print("\n🎉 Environment setup completed successfully!")
        return True

    except Exception as e:
        print(f"💥 Environment setup failed: {str(e)}")
        return False


def get_user_script_selection(pipeline_scripts: List[str]) -> List[str]:
    """
    Get user selection for which scripts to run

    Args:
        pipeline_scripts: List of all available pipeline scripts

    Returns:
        List of selected scripts to execute
    """
    script_map = {chr(65 + i): script for i, script in enumerate(pipeline_scripts)}

    print("\n" + "=" * 80)
    print("📋 SCRIPT SELECTION MENU")
    print("=" * 80)
    print("Available scripts:")
    for i, script in enumerate(pipeline_scripts):
        letter = chr(65 + i)  # A, B, C, etc.
        print(f"  {letter}: {script}")

    print("\nExecution options:")
    print("  1. Run all scripts (A to F)")
    print("  2. Run script range (e.g., C to E)")
    print("  3. Run specific scripts (e.g., A, C, F)")

    while True:
        choice = input("\nEnter your choice (1/2/3): ").strip()

        if choice == "1":
            return pipeline_scripts

        elif choice == "2":
            while True:
                range_input = input("Enter range (e.g., 'C E' for C to E): ").strip().upper()
                try:
                    start_letter, end_letter = range_input.split()
                    start_idx = ord(start_letter) - 65
                    end_idx = ord(end_letter) - 65

                    if 0 <= start_idx <= end_idx < len(pipeline_scripts):
                        selected = pipeline_scripts[start_idx:end_idx + 1]
                        print(f"Selected scripts: {[chr(65 + start_idx + i) for i in range(len(selected))]}")
                        return selected
                    else:
                        print("Invalid range. Please try again.")
                except ValueError:
                    print("Invalid format. Use format like 'C E' for range.")

        elif choice == "3":
            while True:
                scripts_input = input("Enter script letters (e.g., 'A C F'): ").strip().upper()
                try:
                    letters = scripts_input.split()
                    selected = []
                    indices = []

                    for letter in letters:
                        if letter in script_map:
                            idx = ord(letter) - 65
                            indices.append(idx)
                            selected.append(script_map[letter])
                        else:
                            print(f"Invalid script letter: {letter}")
                            break
                    else:
                        # Sort by original pipeline order
                        sorted_pairs = sorted(zip(indices, selected))
                        selected = [script for _, script in sorted_pairs]
                        print(f"Selected scripts: {[chr(65 + idx) for idx, _ in sorted_pairs]}")
                        return selected
                except ValueError:
                    print("Invalid format. Use format like 'A C F' for specific scripts.")
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Google Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python Z_run_A_to_F.py                    # Interactive mode with virtual environment
  python Z_run_A_to_F.py --auto-all        # Run all scripts automatically
  python Z_run_A_to_F.py --no-venv         # Skip virtual environment setup
  python Z_run_A_to_F.py --scripts A B C   # Run specific scripts
  python Z_run_A_to_F.py --range C E       # Run script range C to E
        """
    )

    parser.add_argument(
        '--no-venv', action='store_true',
        help='Skip virtual environment setup (for CI/CD environments)'
    )
    parser.add_argument(
        '--auto-all', action='store_true',
        help='Automatically run all scripts without user interaction'
    )
    parser.add_argument(
        '--scripts', nargs='+', metavar='SCRIPT',
        help='Run specific scripts (e.g., --scripts A B C)'
    )
    parser.add_argument(
        '--range', nargs=2, metavar=('START', 'END'),
        help='Run script range (e.g., --range C E)'
    )

    return parser.parse_args()

def main():
    """Main pipeline orchestrator"""
    args = parse_arguments()

    print("=" * 80)
    print("🚀 GOOGLE PIPELINE ORCHESTRATOR")
    print(f"Started at: {get_ist_timestamp()}")
    if args.no_venv or os.getenv('GITHUB_ACTIONS') == 'true':
        print("Mode: CI/CD (No virtual environment)")
    else:
        print("Mode: Local development (With virtual environment)")
    print("=" * 80)

    # ===============================================
    # ENVIRONMENT SETUP SECTION
    # ===============================================
    print("\n🔧 Setting up development environment...")
    if not setup_environment(skip_venv=args.no_venv):
        print("💥 Pipeline aborted due to environment setup failure")
        return False

    start_time = time.time()
    execution_log = []

    # Sequential Pipeline Execution: A → B → C → D → E → F
    # Note: G & H deployment scripts available via manual workflow trigger
    print("\n📍 SEQUENTIAL PIPELINE EXECUTION")
    print("Flow: A → B → C → D → E → F")
    print("Note: G & H deployment scripts available via manual workflow trigger")

    pipeline_scripts = [
        "A_fetch_api_models.py",
        "B_filter_models.py",
        "C_scrape_modalities.py",
        "D_enrich_modalities.py",
        "E_create_db_data.py",
        "F_compare_pipeline_with_supabase.py"
    ]

    # Determine which scripts to run based on arguments
    if args.auto_all:
        selected_scripts = pipeline_scripts
        print("🤖 Auto-run mode: Running all scripts (A to F)")
    elif args.scripts:
        # Convert script letters to script names
        script_map = {chr(65 + i): script for i, script in enumerate(pipeline_scripts)}
        selected_scripts = []
        for script_letter in args.scripts:
            script_letter = script_letter.upper()
            if script_letter in script_map:
                selected_scripts.append(script_map[script_letter])
            else:
                print(f"❌ Invalid script letter: {script_letter}")
                return False
        print(f"📋 Command-line selection: Running scripts {args.scripts}")
    elif args.range:
        # Convert range to script indices
        start_letter, end_letter = args.range[0].upper(), args.range[1].upper()
        start_idx = ord(start_letter) - 65
        end_idx = ord(end_letter) - 65
        if 0 <= start_idx <= end_idx < len(pipeline_scripts):
            selected_scripts = pipeline_scripts[start_idx:end_idx + 1]
            print(f"📋 Range selection: Running scripts {start_letter} to {end_letter}")
        else:
            print(f"❌ Invalid range: {start_letter} to {end_letter}")
            return False
    else:
        # Interactive mode
        selected_scripts = get_user_script_selection(pipeline_scripts)

    # Display selected scripts
    print(f"\n📋 SELECTED SCRIPTS ({len(selected_scripts)} total):")
    for i, script in enumerate(selected_scripts, 1):
        original_idx = pipeline_scripts.index(script) + 1
        letter = chr(64 + original_idx)  # A, B, C, etc.
        print(f"  {i:2d}. {letter}: {script}")

    # Ask for confirmation only in interactive mode
    if not (args.auto_all or args.scripts or args.range):
        while True:
            confirm = input(f"\nProceed with executing {len(selected_scripts)} script(s)? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                break
            elif confirm in ['n', 'no']:
                print("Pipeline execution cancelled.")
                return False
            else:
                print("Please enter 'y' or 'n'.")


    # Execute selected scripts
    total_stages = len(selected_scripts)
    for i, script in enumerate(selected_scripts, 1):
        original_idx = pipeline_scripts.index(script) + 1
        letter = chr(64 + original_idx)  # A, B, C, etc.
        print(f"\n📍 STAGE {i:2d}/{total_stages}: {letter} - {script}")
        success, message = run_script(script, use_venv=not args.no_venv)
        execution_log.append((script, success, message))
        if not success:
            print(f"💥 Pipeline stopped due to failure in {script}")
            generate_pipeline_report(execution_log, time.time() - start_time)
            return False

    # Pipeline completed successfully
    end_time = time.time()
    total_time = end_time - start_time

    print("\n" + "=" * 80)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Total execution time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"All {len(execution_log)} selected stages executed successfully")
    if len(selected_scripts) == len(pipeline_scripts):
        print("Full pipeline (A to F) completed")
    else:
        executed_letters = [chr(64 + pipeline_scripts.index(script) + 1) for script in selected_scripts]
        print(f"Executed scripts: {', '.join(executed_letters)}")
    print(f"Completed at: {get_ist_timestamp()}")
    print("=" * 80)

    # Generate final report
    generate_pipeline_report(execution_log, total_time)

    # Save completion timestamp
    try:
        script_dir = Path(__file__).parent
        last_run_file = script_dir.parent / "02_outputs" / "last-run.txt"
        with open(last_run_file, "w") as f:
            f.write(f"Google Pipeline completed: {get_ist_timestamp_detailed()}\n")
            f.write(f"Local execution: {get_ist_timestamp()}\n")
            f.write(f"Pipeline duration: {total_time:.1f} seconds\n")
    except Exception as e:
        print(f"⚠️  Could not save completion timestamp: {e}")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Pipeline crashed: {e}")
        sys.exit(1)