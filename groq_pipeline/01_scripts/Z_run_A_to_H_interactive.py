#!/usr/bin/env python3
"""
Groq Pipeline Orchestrator
Executes the complete Groq AI models discovery pipeline from A to H

Pipeline Flow:
A → B → C → D → E → F → G → H
"""

import subprocess
import sys
import time
import os
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Import utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '04_utils'))

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
        elif os.path.exists("groq_env/bin/python"):
            python_exec = "groq_env/bin/python"
        else:
            python_exec = sys.executable

        result = subprocess.run(
            [python_exec, script_name],
            capture_output=True,
            text=True,
            timeout=900,  # 15 minute timeout per script
            cwd=os.path.dirname(__file__),  # Run from 01_scripts directory
            env=os.environ  # Pass through all environment variables
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
    report_file = script_dir.parent / "02_outputs" / "Z-groq-pipeline-report.txt"

    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("GROQ PIPELINE EXECUTION REPORT\n")
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
            f.write("A → B → C → D → E → F → G → H\n\n")

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

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Groq Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python Z_run_A_to_H_interactive.py                    # Interactive mode
  python Z_run_A_to_H_interactive.py --auto-all        # Run all scripts automatically
  python Z_run_A_to_H_interactive.py --no-venv         # Skip virtual environment setup
  python Z_run_A_to_H_interactive.py --scripts A B C   # Run specific scripts
  python Z_run_A_to_H_interactive.py --range C F       # Run script range C to F
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
        help='Run script range (e.g., --range C F)'
    )

    return parser.parse_args()

def setup_environment(skip_venv: bool = False) -> bool:
    """
    Setup development environment
    Creates virtual environment and installs dependencies

    Args:
        skip_venv: If True, skip virtual environment setup (for CI/CD environments)

    Returns:
        bool: True if setup successful, False otherwise
    """
    print("\n" + "=" * 60)
    print("🔧 ENVIRONMENT SETUP")
    print("=" * 60)

    # Auto-detect GitHub Actions or use explicit flag
    github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    dependencies = ["selenium", "webdriver-manager", "beautifulsoup4", "requests", "supabase", "psycopg2-binary", "python-dotenv"]

    if skip_venv or github_actions:
        print("📝 Skipping virtual environment setup (CI/CD mode)")
        print("   Installing dependencies with system Python...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", *dependencies
        ], capture_output=True, text=True, timeout=300, env={**os.environ, "PIP_BREAK_SYSTEM_PACKAGES": "1"})

        if result.returncode != 0:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
        print("✅ Dependencies installed for system environment")
        return True

    # Check if virtual environment exists
    venv_path = Path("groq_env")
    if not venv_path.exists():
        print("🏗️  Creating Python virtual environment...")
        result = subprocess.run([sys.executable, "-m", "venv", "groq_env"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to create virtual environment: {result.stderr}")
            return False
        print("✅ Virtual environment created")

    # Install dependencies
    pip_path = venv_path / "bin" / "pip" if os.name != 'nt' else venv_path / "Scripts" / "pip.exe"

    if pip_path.exists():
        print("📦 Installing dependencies...")
        result = subprocess.run([
            str(pip_path), "install", *dependencies
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"⚠️  Some dependencies may not have installed: {result.stderr}")
            print("Continuing with system Python...")
        else:
            print("✅ Dependencies installed")

    return True

def get_pipeline_scripts():
    """Get the list of pipeline scripts"""
    return [
        "A_scrape_production_models.py",
        "B_scrape_rate_limits.py",
        "C_scrape_modalities.py",
        "D_extract_meta_licenses.py",
        "E_extract_opensource_licenses.py",
        "F_consolidate_all_licenses.py",
        "G_normalize_data.py",
        "H_compare_pipeline_with_supabase.py"
    ]

def filter_scripts_by_selection(all_scripts: List[str], scripts_arg: List[str] = None, range_arg: List[str] = None) -> List[str]:
    """
    Filter scripts based on user selection

    Args:
        all_scripts: List of all available scripts
        scripts_arg: Specific scripts to run (e.g., ['A', 'B', 'C'])
        range_arg: Range of scripts to run (e.g., ['C', 'F'])

    Returns:
        List of filtered script names
    """
    if scripts_arg:
        # Convert script letters to full script names
        selected_scripts = []
        for script_letter in scripts_arg:
            matching_scripts = [s for s in all_scripts if s.startswith(f"{script_letter.upper()}_")]
            if matching_scripts:
                selected_scripts.extend(matching_scripts)
            else:
                print(f"⚠️  Warning: No script found for '{script_letter}'")
        return selected_scripts

    elif range_arg:
        start_letter, end_letter = range_arg[0].upper(), range_arg[1].upper()

        # Find start and end indices
        start_idx = None
        end_idx = None

        for i, script in enumerate(all_scripts):
            if script.startswith(f"{start_letter}_"):
                start_idx = i
            if script.startswith(f"{end_letter}_"):
                end_idx = i

        if start_idx is None:
            print(f"❌ Start script '{start_letter}' not found")
            return []
        if end_idx is None:
            print(f"❌ End script '{end_letter}' not found")
            return []
        if start_idx > end_idx:
            print(f"❌ Invalid range: {start_letter} comes after {end_letter}")
            return []

        return all_scripts[start_idx:end_idx+1]

    else:
        return all_scripts

def main():
    """Main pipeline orchestrator"""
    args = parse_arguments()

    print("=" * 60)
    print("🚀 GROQ PIPELINE ORCHESTRATOR")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.no_venv or os.getenv('GITHUB_ACTIONS') == 'true':
        print("Mode: CI/CD (No virtual environment)")
    else:
        print("Mode: Local development (With virtual environment)")
    print("=" * 60)

    # ===============================================
    # ENVIRONMENT SETUP SECTION
    # ===============================================
    print("\n🔧 Setting up development environment...")
    if not setup_environment(skip_venv=args.no_venv):
        print("💥 Pipeline aborted due to environment setup failure")
        return False

    start_time = time.time()
    execution_log = []

    # Sequential Pipeline Execution: A → B → C → D → E → F → G → H
    print("\n📍 SEQUENTIAL PIPELINE EXECUTION")
    print("Flow: A → B → C → D → E → F → G → H")
    print("Note: I & J deployment scripts available via manual workflow trigger")

    all_scripts = get_pipeline_scripts()

    # Filter scripts based on arguments
    pipeline_scripts = filter_scripts_by_selection(all_scripts, args.scripts, args.range)

    if not pipeline_scripts:
        print("❌ No scripts to execute")
        return False

    print(f"\nScripts to execute: {len(pipeline_scripts)}")
    for i, script in enumerate(pipeline_scripts, 1):
        print(f"  {i}. {script}")

    # Auto-all mode or interactive confirmation
    if not args.auto_all:
        try:
            response = input(f"\n🚦 Execute {len(pipeline_scripts)} scripts? (y/n): ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ Pipeline execution cancelled")
                return False
        except KeyboardInterrupt:
            print("\n❌ Pipeline execution cancelled")
            return False

    # Execute pipeline scripts
    print(f"\n🏃 Executing {len(pipeline_scripts)} scripts...")

    for i, script_name in enumerate(pipeline_scripts, 1):
        print(f"\n{'='*60}")
        print(f"📍 STAGE {i}/{len(pipeline_scripts)}: {script_name}")
        print(f"{'='*60}")

        success, message = run_script(script_name, use_venv=not args.no_venv)
        execution_log.append((script_name, success, message))

        if not success:
            print(f"⚠️  Stage {i} ({script_name}) failed: {message}")

            # For interactive mode, ask user how to proceed
            if not args.auto_all:
                try:
                    response = input("Continue with remaining scripts? (y/n): ").strip().lower()
                    if response not in ['y', 'yes']:
                        print("🛑 Pipeline execution stopped by user")
                        break
                except KeyboardInterrupt:
                    print("\n🛑 Pipeline execution stopped by user")
                    break

        # Brief pause between scripts
        if i < len(pipeline_scripts):
            time.sleep(1)

    total_time = time.time() - start_time

    # Generate comprehensive report
    generate_pipeline_report(execution_log, total_time)

    # Final summary
    successful_stages = sum(1 for _, success, _ in execution_log if success)
    failed_stages = len(execution_log) - successful_stages

    print(f"\n{'='*60}")
    print("🏁 PIPELINE EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"📊 Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"📊 Stages: {len(execution_log)} total, {successful_stages} successful, {failed_stages} failed")
    print(f"📊 Success rate: {(successful_stages/len(execution_log)*100):.1f}%")

    if failed_stages == 0:
        print("🎉 All scripts completed successfully!")
        return True
    else:
        print(f"⚠️  {failed_stages} scripts failed - check logs for details")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Pipeline execution interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)