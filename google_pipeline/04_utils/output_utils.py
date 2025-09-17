#!/usr/bin/env python3
"""
Output utilities for Google Pipeline
Provides centralized output directory management and cleanup functions
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
import pytz


def get_output_dir() -> str:
    """
    Get the absolute path to the 02_outputs directory
    Works from any script location within the pipeline
    """
    # Get the directory of this utils file (04_utils)
    utils_dir = Path(__file__).parent
    # Navigate to pipeline root and then to outputs
    output_dir = utils_dir.parent / "02_outputs"
    return str(output_dir.resolve())


def get_output_file_path(filename: str) -> str:
    """
    Get the full path for an output file

    Args:
        filename: Name of the output file

    Returns:
        Full path to the output file
    """
    output_dir = Path(get_output_dir())
    return str(output_dir / filename)


def ensure_output_directory():
    """
    Ensure the 02_outputs directory exists
    Creates it if it doesn't exist
    """
    output_dir = Path(get_output_dir())
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output directory ensured: {output_dir}")


def clean_output_directory():
    """
    Clean the 02_outputs directory by removing all files
    Keeps the directory structure but removes all contents
    """
    output_dir = Path(get_output_dir())

    if output_dir.exists():
        print(f"🧹 Cleaning output directory: {output_dir}")
        # Remove all files and subdirectories except .gitkeep
        for item in output_dir.iterdir():
            if item.name == '.gitkeep':
                continue  # Keep .gitkeep file

            if item.is_file():
                item.unlink()
                print(f"   Removed file: {item.name}")
            elif item.is_dir():
                shutil.rmtree(item)
                print(f"   Removed directory: {item.name}")

    # Ensure the directory exists (recreate if it was deleted)
    output_dir.mkdir(exist_ok=True)
    print(f"✅ Output directory cleaned and ready")


def should_clean_on_pipeline_start() -> bool:
    """
    Determine if output directory should be cleaned at pipeline start
    Only clean if this is the first stage of the pipeline (Stage A)
    """
    # Check if this is being called from the main pipeline orchestrator
    import inspect

    # Get the calling script name
    frame = inspect.currentframe()
    try:
        # Go up the call stack to find the calling script
        caller_frame = frame.f_back
        while caller_frame:
            filename = caller_frame.f_code.co_filename
            script_name = Path(filename).name

            # If called from A_fetch_api_models.py or the orchestrator, clean
            if script_name in ['A_fetch_api_models.py', 'Z_run_A_to_F.py']:
                return True

            caller_frame = caller_frame.f_back
    finally:
        del frame

    return False


def force_clean_output_directory():
    """
    Force clean the output directory regardless of calling context
    Used in GitHub Actions or when explicit cleanup is needed
    """
    print("🔄 Force cleaning output directory...")
    clean_output_directory()


def get_ist_timestamp() -> str:
    """
    Get current timestamp in IST (Indian Standard Time) in readable format

    Returns:
        Formatted timestamp string in IST
    """
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    return now_ist.strftime('%Y-%m-%d %H:%M:%S IST')


def get_ist_timestamp_iso() -> str:
    """
    Get current timestamp in IST (Indian Standard Time) in ISO format

    Returns:
        ISO formatted timestamp string in IST
    """
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    return now_ist.isoformat()


def get_ist_timestamp_detailed() -> str:
    """
    Get current timestamp in IST with full weekday and month names

    Returns:
        Detailed formatted timestamp string in IST
    """
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    return now_ist.strftime('%a %b %d %H:%M:%S IST %Y')