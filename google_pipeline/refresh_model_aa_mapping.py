#!/usr/bin/env python3
"""
Google Pipeline: Auto-refresh ims.10_model_aa_mapping table
============================================================

Standalone wrapper for refreshing model-AA mappings for Google provider.
Uses the shared model_aa_mapping_utils module.

This script is maintained for backward compatibility and can be run manually.
The main pipeline scripts now automatically call the shared utility.

Usage:
    python3 refresh_model_aa_mapping.py

Environment:
    PIPELINE_SUPABASE_URL - Database connection string (required)

Author: AI Models Discovery Pipeline
Version: 3.0 (Uses shared utility)
Last Updated: 2025-12-04
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    import psycopg2
    from model_aa_mapping_utils import refresh_model_aa_mapping
except ImportError as e:
    print(f"ERROR: Required imports failed: {e}")
    print("Ensure psycopg2-binary is installed: pip install psycopg2-binary")
    sys.exit(1)

# Configuration
INFERENCE_PROVIDER = "Google"
DATABASE_URL = os.environ.get('PIPELINE_SUPABASE_URL')

if not DATABASE_URL:
    print("ERROR: PIPELINE_SUPABASE_URL environment variable not set")
    sys.exit(1)


def main():
    """Main execution wrapper for Google pipeline mapping refresh."""
    print("=" * 70)
    print(f"Google Pipeline: Model-AA Mapping Refresh")
    print("=" * 70)
    print(f"Provider: {INFERENCE_PROVIDER}")
    print("")

    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Connected to database")
        print("")

        # Call shared utility
        success = refresh_model_aa_mapping(
            conn,
            inference_provider=INFERENCE_PROVIDER,
            logger=None  # Uses print() for output
        )

        # Cleanup
        conn.close()
        print("")
        print("Database connection closed")

        return success

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
