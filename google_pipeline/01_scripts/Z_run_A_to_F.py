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
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Import IST timestamp utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '04_utils'))
from output_utils import get_ist_timestamp, get_ist_timestamp_detailed


def run_script(script_name: str) -> Tuple[bool, str]:
    """
    Run a pipeline script and return success status and output

    Args:
        script_name: Name of the script to run

    Returns:
        Tuple of (success, output_message)
    """
    try:
        print(f"🔄 Running {script_name}...")
        start_time = time.time()

        result = subprocess.run(
            [sys.executable, script_name],
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

def setup_environment() -> bool:
    """
    Setup local development environment

    Returns:
        bool: True if setup successful, False otherwise
    """
    print("\n" + "=" * 80)
    print("🔧 ENVIRONMENT SETUP")
    print("=" * 80)

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

def main():
    """Main pipeline orchestrator"""
    print("=" * 80)
    print("🚀 GOOGLE PIPELINE ORCHESTRATOR")
    print(f"Started at: {get_ist_timestamp()}")
    print("=" * 80)

    # ===============================================
    # ENVIRONMENT SETUP SECTION
    # ===============================================
    print("\n🔧 Setting up local development environment...")
    if not setup_environment():
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

    # Get user selection for which scripts to run
    selected_scripts = get_user_script_selection(pipeline_scripts)

    # Display selected scripts and ask for confirmation
    print(f"\n📋 SELECTED SCRIPTS ({len(selected_scripts)} total):")
    for i, script in enumerate(selected_scripts, 1):
        original_idx = pipeline_scripts.index(script) + 1
        letter = chr(64 + original_idx)  # A, B, C, etc.
        print(f"  {i:2d}. {letter}: {script}")

    # Ask for confirmation
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
        success, message = run_script(script)
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