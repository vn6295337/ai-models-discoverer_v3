#!/usr/bin/env python3
"""
Output Directory Utilities
Provides centralized path management for pipeline outputs
"""
import os
import shutil
from pathlib import Path

def get_output_dir() -> str:
    """
    Get the pipeline outputs directory path

    Returns:
        str: Path to pipeline-outputs directory
    """
    script_dir = Path(__file__).parent
    output_dir = script_dir / "pipeline-outputs"

    # Ensure the directory exists
    output_dir.mkdir(exist_ok=True)

    return str(output_dir)

def get_output_file_path(filename: str) -> str:
    """
    Get the full path for an output file

    Args:
        filename: Name of the output file

    Returns:
        str: Full path to the output file in pipeline-outputs directory
    """
    return os.path.join(get_output_dir(), filename)

def get_input_file_path(filename: str) -> str:
    """
    Get the full path for an input file from previous pipeline stages
    Input files are read from pipeline-outputs directory

    Args:
        filename: Name of the input file

    Returns:
        str: Full path to the input file in pipeline-outputs directory
    """
    return os.path.join(get_output_dir(), filename)

def ensure_output_dir_exists():
    """
    Ensure the pipeline-outputs directory exists
    """
    output_dir = Path(get_output_dir())
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output directory ensured: {output_dir}")

def clean_output_directory():
    """
    Clean the pipeline-outputs directory by removing all files
    Keeps the directory structure but removes all contents
    """
    output_dir = Path(get_output_dir())

    if output_dir.exists():
        print(f"🧹 Cleaning output directory: {output_dir}")
        # Remove all files and subdirectories
        for item in output_dir.iterdir():
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
    Only clean if this is the first stage of the pipeline
    """
    # Check if this is being called from the main pipeline orchestrator
    import inspect

    # Get the calling script name
    frame = inspect.currentframe()
    try:
        caller_frame = frame.f_back.f_back if frame.f_back else None
        if caller_frame:
            caller_filename = caller_frame.f_code.co_filename
            caller_script = Path(caller_filename).name

            # Clean only if called from stage A or the main orchestrator
            return caller_script in ['A_api_models_fetch.py', 'Z_run_A_to_R.py']
    finally:
        del frame

    return False