#!/usr/bin/env python3
"""
OpenRouter Pipeline Orchestrator
Executes the complete OpenRouter AI models discovery pipeline from A to S

Pipeline Flow:
A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P → Q → R → S
"""

import subprocess
import sys
import time
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Import output utilities
import sys; import os; sys.path.append(os.path.join(os.path.dirname(__file__), "..", "04_utils")); from output_utils import get_output_file_path

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
        
        # Use virtual environment Python if it exists
        if os.path.exists("../openrouter_env/bin/python"):
            python_exec = "../openrouter_env/bin/python"
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
        print(f"⏰ {script_name} timed out after 10 minutes")
        return False, "Timed out after 10 minutes"
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
    report_file = get_output_file_path("Z-pipeline-execution-report.txt")
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("OPENROUTER PIPELINE EXECUTION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            total_stages = len(execution_log)
            successful_stages = sum(1 for _, success, _ in execution_log if success)
            failed_stages = total_stages - successful_stages
            
            f.write(f"EXECUTION SUMMARY:\n")
            f.write(f"  Total execution time : {total_time:.1f} seconds ({total_time/60:.1f} minutes)\n")
            f.write(f"  Total stages         : {total_stages}\n")
            f.write(f"  Successful stages    : {successful_stages}\n")
            f.write(f"  Failed stages        : {failed_stages}\n")
            f.write(f"  Success rate         : {(successful_stages/total_stages)*100:.1f}%\n\n")
            
            # Stage-by-stage results
            f.write("STAGE-BY-STAGE RESULTS:\n")
            f.write("=" * 80 + "\n")
            
            for i, (stage, success, message) in enumerate(execution_log, 1):
                status = "✅ SUCCESS" if success else "❌ FAILED"
                f.write(f"Stage {i:2d}: {stage}\n")
                f.write(f"  Status: {status}\n")
                f.write(f"  Details: {message}\n")
                f.write(f"\n")
            
            # Pipeline flow diagram
            f.write("PIPELINE FLOW DIAGRAM:\n")
            f.write("=" * 80 + "\n")
            f.write("A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P → Q → R → S\n\n")
            
            # Final status
            if failed_stages == 0:
                f.write("🎉 PIPELINE COMPLETED SUCCESSFULLY!\n")
                f.write("All stages executed without errors. Data is ready for deployment.\n")
            else:
                f.write("⚠️  PIPELINE COMPLETED WITH ERRORS!\n")
                f.write(f"{failed_stages} stage(s) failed. Check individual stage outputs for details.\n")
        
        print(f"📊 Pipeline execution report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Failed to generate pipeline report: {e}")

def setup_environment() -> bool:
    """
    Setup local development environment
    Creates virtual environment, installs dependencies, and creates utility scripts
    
    Returns:
        bool: True if setup successful, False otherwise
    """
    print("\n" + "=" * 60)
    print("🔧 ENVIRONMENT SETUP")
    print("=" * 60)
    
    try:
        # 1. Create virtual environment
        print("🔄 Creating virtual environment...")
        if os.path.exists("../openrouter_env"):
            print("   Virtual environment already exists, skipping creation")
        else:
            result = subprocess.run([
                sys.executable, "-m", "venv", "../openrouter_env"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Virtual environment created successfully")
            else:
                print(f"❌ Failed to create virtual environment: {result.stderr}")
                return False
        
        # 2. Create environment cleanup script
        print("🔄 Creating environment cleanup script...")
        cleanup_script = """#!/bin/bash
# OpenRouter Environment Cleanup Script
echo "🧹 Cleaning OpenRouter environment..."

# Remove virtual environment
if [ -d "openrouter_env" ]; then
    echo "  Removing virtual environment..."
    rm -rf openrouter_env
    echo "  ✅ Virtual environment removed"
fi

# Remove Python cache
if [ -d "01_scripts/__pycache__" ]; then
    echo "  Removing Python cache..."
    rm -rf 01_scripts/__pycache__
    echo "  ✅ Python cache removed"
fi

# Remove any .pyc files
echo "  Removing .pyc files..."
find . -name "*.pyc" -delete
echo "  ✅ .pyc files removed"

echo "🎉 Environment cleanup completed!"
"""
        
        with open("../openrouter_envclear", "w") as f:
            f.write(cleanup_script)

        # Make it executable
        os.chmod("../openrouter_envclear", 0o755)
        print("✅ Environment cleanup script created")
        
        # 3. Install dependencies (if requirements.txt exists)
        requirements_paths = [
            Path("../requirements.txt"),           # Parent directory
            Path("../03_configs/requirements.txt") # Config directory
        ]

        requirements_file = None
        for req_path in requirements_paths:
            if req_path.exists():
                requirements_file = req_path
                break

        if requirements_file:
            print(f"🔄 Installing dependencies from {requirements_file}...")

            # Determine pip path based on OS
            if os.name == 'nt':  # Windows
                pip_path = os.path.join("..", "openrouter_env", "Scripts", "pip")
            else:  # Unix/Linux/Mac
                pip_path = os.path.join("..", "openrouter_env", "bin", "pip")

            result = subprocess.run([
                pip_path, "install", "-r", str(requirements_file)
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
            else:
                print(f"❌ Failed to install dependencies: {result.stderr}")
                return False
        else:
            print("⚠️  No requirements.txt found in ../requirements.txt or ../03_configs/requirements.txt, skipping dependency installation")
        
        print("\n🎉 Environment setup completed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        print("⏰ Environment setup timed out")
        return False
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

    print("\n" + "=" * 60)
    print("📋 SCRIPT SELECTION MENU")
    print("=" * 60)
    print("Available scripts:")
    for i, script in enumerate(pipeline_scripts):
        letter = chr(65 + i)  # A, B, C, etc.
        print(f"  {letter}: {script}")

    print("\nExecution options:")
    print("  1. Run all scripts (A to S)")
    print("  2. Run script range (e.g., C to P)")
    print("  3. Run specific scripts (e.g., R, S)")

    while True:
        choice = input("\nEnter your choice (1/2/3): ").strip()

        if choice == "1":
            return pipeline_scripts

        elif choice == "2":
            while True:
                range_input = input("Enter range (e.g., 'C P' for C to P): ").strip().upper()
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
                    print("Invalid format. Use format like 'C P' for range.")

        elif choice == "3":
            while True:
                scripts_input = input("Enter script letters (e.g., 'R S' or 'A C E'): ").strip().upper()
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
                    print("Invalid format. Use format like 'R S' for specific scripts.")
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def main():
    """Main pipeline orchestrator"""
    print("=" * 60)
    print("🚀 OPENROUTER PIPELINE ORCHESTRATOR")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # ===============================================
    # ENVIRONMENT SETUP SECTION
    # ===============================================
    print("\n🔧 Setting up local development environment...")
    if not setup_environment():
        print("💥 Pipeline aborted due to environment setup failure")
        return False
    
    start_time = time.time()
    execution_log = []
    
    # Sequential Pipeline Execution: A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P → Q → R → S
    # Note: T and U scripts are manual-only and run via separate workflow
    print("\n📍 SEQUENTIAL PIPELINE EXECUTION")
    print("Flow: A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P → Q → R → S")
    print("Note: T & U deployment scripts available via manual workflow trigger")
    
    pipeline_scripts = [
        "A_fetch_api_models.py",
        "B_filter_models.py",
        "C_extract_google_licenses.py",
        "D_extract_meta_licenses.py",
        "E_fetch_other_license_info_urls_from_hf.py",
        "F_fetch_other_license_names_from_hf.py",
        "G_standardize_other_license_names_from_hf.py",
        "H_bucketize_other_license_names.py",
        "I_opensource_license_urls.py",
        "J_custom_license_urls.py",
        "K_collate_opensource_licenses.py",
        "L_collate_custom_licenses.py",
        "M_final_list_of_licenses.py",
        "N_extract_raw_modalities.py",
        "O_standardize_raw_modalities.py",
        "P_enrich_provider_info.py",
        "Q_create_db_data.py",
        "R_filter_db_data.py",
        "S_compare_pipeline_with_supabase.py"
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
    
    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Total execution time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"All {len(execution_log)} selected stages executed successfully")
    if len(selected_scripts) == len(pipeline_scripts):
        print("Full pipeline (A to S) completed")
    else:
        executed_letters = [chr(64 + pipeline_scripts.index(script) + 1) for script in selected_scripts]
        print(f"Executed scripts: {', '.join(executed_letters)}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Generate final report
    generate_pipeline_report(execution_log, total_time)
    
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