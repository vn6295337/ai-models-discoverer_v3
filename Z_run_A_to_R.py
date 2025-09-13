#!/usr/bin/env python3
"""
OpenRouter Pipeline Orchestrator
Executes the complete OpenRouter AI models discovery pipeline from A to T

Pipeline Flow:
A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P → Q → R → S → T
"""

import subprocess
import sys
import time
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

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
            timeout=900  # 15 minute timeout per script
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
    report_file = "Z-pipeline-execution-report.txt"
    
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
            f.write("A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P → Q → R\n\n")
            
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
        if os.path.exists("openrouter_env"):
            print("   Virtual environment already exists, skipping creation")
        else:
            result = subprocess.run([
                sys.executable, "-m", "venv", "openrouter_env"
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
if [ -d "__pycache__" ]; then
    echo "  Removing Python cache..."
    rm -rf __pycache__
    echo "  ✅ Python cache removed"
fi

# Remove any .pyc files
echo "  Removing .pyc files..."
find . -name "*.pyc" -delete
echo "  ✅ .pyc files removed"

echo "🎉 Environment cleanup completed!"
"""
        
        with open("openrouter_envclear", "w") as f:
            f.write(cleanup_script)
        
        # Make it executable
        os.chmod("openrouter_envclear", 0o755)
        print("✅ Environment cleanup script created")
        
        # 3. Install dependencies (if requirements.txt exists)
        requirements_file = Path("requirements.txt")
        if requirements_file.exists():
            print("🔄 Installing dependencies from requirements.txt...")
            
            # Determine pip path based on OS
            if os.name == 'nt':  # Windows
                pip_path = os.path.join("openrouter_env", "Scripts", "pip")
            else:  # Unix/Linux/Mac
                pip_path = os.path.join("openrouter_env", "bin", "pip")
            
            result = subprocess.run([
                pip_path, "install", "-r", "requirements.txt"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
            else:
                print(f"❌ Failed to install dependencies: {result.stderr}")
                return False
        else:
            print("⚠️  No requirements.txt found, skipping dependency installation")
        
        print("\n🎉 Environment setup completed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        print("⏰ Environment setup timed out")
        return False
    except Exception as e:
        print(f"💥 Environment setup failed: {str(e)}")
        return False

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
    
    # Sequential Pipeline Execution: A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P → Q → R
    # Note: S and T scripts are manual-only and run via separate workflow
    print("\n📍 SEQUENTIAL PIPELINE EXECUTION")
    print("Flow: A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P → Q → R")
    print("Note: S & T deployment scripts available via manual workflow trigger")
    
    pipeline_scripts = [
        "A_api_models_fetch.py",
        "B_models_filter.py",
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
        "R_finalize_db_data.py"
    ]
    
    for i, script in enumerate(pipeline_scripts, 1):
        print(f"\n📍 STAGE {i:2d}/18: {script}")
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
    print(f"All {len(execution_log)} stages executed successfully")
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