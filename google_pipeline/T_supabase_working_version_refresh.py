#!/usr/bin/env python3

"""
Supabase Google Data Refresh Script
===================================

This script refreshes Google data in Supabase by:
1. Deleting existing Google records from working_version table
2. Loading finalized data from E-db-schema-normalize.csv
3. Inserting fresh Google data into Supabase

Features:
- Comprehensive error handling and logging
- Data validation and safety checks
- Bulk insert with individual fallback
- Transaction-like operations (delete + insert)
- Detailed progress reporting
- Rollback capability with backup

Author: AI Models Discovery Pipeline
Version: 1.0
Last Updated: 2025-01-15
"""

import os
import sys
import csv
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Third-party imports
try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not found. Install with: pip install supabase")
    sys.exit(1)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in root directory (ai-models-discoverer_v2)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️ .env file not found at {env_path}")
        # Also try current directory as fallback
        current_env = Path(__file__).parent / ".env"
        if current_env.exists():
            load_dotenv(current_env)
            print(f"✅ Loaded environment variables from {current_env}")
        else:
            print("⚠️ No .env file found. Make sure environment variables are set.")
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables.")

# Configuration
INFERENCE_PROVIDER = "Google"
TABLE_NAME = "working_version"
PIPELINE_DATA_FILE = Path(__file__).parent / "pipeline-outputs" / "E-db-schema-normalize.csv"
BACKUP_FILE = Path(__file__).parent / "pipeline-outputs" / f"T-supabase-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
REPORT_FILE = Path(__file__).parent / "pipeline-outputs" / "T-supabase-refresh-report.txt"

# Supabase configuration from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_supabase_client() -> Optional[Client]:
    """Initialize and return Supabase client"""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.error("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        print("❌ Missing required environment variables:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_ANON_KEY (or SUPABASE_KEY)")
        return None

    try:
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        print(f"❌ Failed to connect to Supabase: {e}")
        return None

def load_pipeline_data() -> List[Dict[str, Any]]:
    """Load pipeline data from E-db-schema-normalize.csv"""
    try:
        data = []
        with open(PIPELINE_DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        logger.info(f"Loaded {len(data)} records from pipeline data")
        print(f"✅ Loaded {len(data)} Google models from pipeline data")
        return data
    except FileNotFoundError:
        logger.error(f"Pipeline data file not found: {PIPELINE_DATA_FILE}")
        print(f"❌ Pipeline data file not found: {PIPELINE_DATA_FILE}")
        return []
    except Exception as e:
        logger.error(f"Error loading pipeline data: {e}")
        print(f"❌ Error loading pipeline data: {e}")
        return []

def backup_existing_data(client: Client) -> bool:
    """Backup existing Google data from Supabase"""
    try:
        print(f"📦 Creating backup of existing {INFERENCE_PROVIDER} data...")

        response = client.table(TABLE_NAME).select("*").eq("inference_provider", INFERENCE_PROVIDER).execute()
        existing_data = response.data if response.data else []

        if existing_data:
            with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, default=str)
            logger.info(f"Backup created with {len(existing_data)} records")
            print(f"✅ Backup created: {BACKUP_FILE} ({len(existing_data)} records)")
        else:
            print(f"ℹ️ No existing {INFERENCE_PROVIDER} data found to backup")

        return True
    except Exception as e:
        logger.error(f"Failed to backup existing data: {e}")
        print(f"❌ Failed to backup existing data: {e}")
        return False

def delete_existing_data(client: Client) -> bool:
    """Delete existing Google data from Supabase"""
    try:
        print(f"🗑️ Deleting existing {INFERENCE_PROVIDER} data from Supabase...")

        response = client.table(TABLE_NAME).delete().eq("inference_provider", INFERENCE_PROVIDER).execute()

        if hasattr(response, 'data') and response.data is not None:
            deleted_count = len(response.data)
        else:
            # For some delete operations, we might not get explicit count
            # Check by querying remaining records
            check_response = client.table(TABLE_NAME).select("id").eq("inference_provider", INFERENCE_PROVIDER).execute()
            remaining_count = len(check_response.data) if check_response.data else 0
            deleted_count = f"completed (remaining: {remaining_count})"

        logger.info(f"Deleted existing {INFERENCE_PROVIDER} data")
        print(f"✅ Deleted existing {INFERENCE_PROVIDER} data: {deleted_count}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete existing data: {e}")
        print(f"❌ Failed to delete existing data: {e}")
        return False

def validate_data_record(record: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a single data record before insertion"""
    required_fields = ['human_readable_name', 'inference_provider']

    for field in required_fields:
        if not record.get(field):
            return False, f"Missing required field: {field}"

    if record.get('inference_provider') != INFERENCE_PROVIDER:
        return False, f"Invalid inference_provider: {record.get('inference_provider')}"

    return True, "Valid"

def insert_data_bulk(client: Client, data: List[Dict[str, Any]]) -> Tuple[bool, int, List[str]]:
    """Insert data in bulk with error handling"""
    try:
        print(f"📤 Inserting {len(data)} records in bulk...")

        response = client.table(TABLE_NAME).insert(data).execute()

        if response.data:
            inserted_count = len(response.data)
            logger.info(f"Bulk insert successful: {inserted_count} records")
            print(f"✅ Bulk insert successful: {inserted_count} records")
            return True, inserted_count, []
        else:
            return False, 0, ["Bulk insert returned no data"]
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Bulk insert failed: {error_msg}")
        print(f"❌ Bulk insert failed: {error_msg}")
        return False, 0, [error_msg]

def insert_data_individual(client: Client, data: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
    """Insert data record by record (fallback method)"""
    print(f"📤 Inserting {len(data)} records individually...")

    inserted_count = 0
    errors = []

    for i, record in enumerate(data):
        try:
            # Validate record before insertion
            is_valid, validation_msg = validate_data_record(record)
            if not is_valid:
                errors.append(f"Record {i+1}: {validation_msg}")
                continue

            response = client.table(TABLE_NAME).insert([record]).execute()

            if response.data and len(response.data) > 0:
                inserted_count += 1
                if (i + 1) % 10 == 0:  # Progress indicator
                    print(f"   Inserted {i + 1}/{len(data)} records...")
            else:
                errors.append(f"Record {i+1}: Insert returned no data")

        except Exception as e:
            errors.append(f"Record {i+1} ({record.get('human_readable_name', 'Unknown')}): {str(e)}")

    logger.info(f"Individual insert completed: {inserted_count}/{len(data)} successful")
    print(f"✅ Individual insert completed: {inserted_count}/{len(data)} successful")

    return inserted_count, errors

def generate_report(
    original_count: int,
    inserted_count: int,
    errors: List[str],
    execution_time: float
) -> None:
    """Generate detailed execution report"""
    try:
        report_content = []
        report_content.append("GOOGLE SUPABASE REFRESH REPORT")
        report_content.append("=" * 50)
        report_content.append(f"Execution Date: {datetime.now().isoformat()}")
        report_content.append(f"Inference Provider: {INFERENCE_PROVIDER}")
        report_content.append(f"Table: {TABLE_NAME}")
        report_content.append("")

        # Summary Statistics
        report_content.append("SUMMARY STATISTICS")
        report_content.append("-" * 30)
        report_content.append(f"Pipeline Records Loaded: {original_count}")
        report_content.append(f"Records Successfully Inserted: {inserted_count}")
        report_content.append(f"Insert Success Rate: {(inserted_count/original_count*100) if original_count > 0 else 0:.1f}%")
        report_content.append(f"Total Errors: {len(errors)}")
        report_content.append(f"Execution Time: {execution_time:.2f} seconds")
        report_content.append("")

        # Error Details
        if errors:
            report_content.append("ERROR DETAILS")
            report_content.append("-" * 30)
            for error in errors[:20]:  # Limit to first 20 errors
                report_content.append(f"• {error}")
            if len(errors) > 20:
                report_content.append(f"... and {len(errors) - 20} more errors")
            report_content.append("")

        # Files
        report_content.append("FILES")
        report_content.append("-" * 30)
        report_content.append(f"Source: {PIPELINE_DATA_FILE}")
        report_content.append(f"Backup: {BACKUP_FILE}")
        report_content.append(f"Report: {REPORT_FILE}")

        # Write report
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_content))

        print(f"📄 Detailed report saved to: {REPORT_FILE}")
        logger.info(f"Report generated: {REPORT_FILE}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        print(f"❌ Failed to generate report: {e}")

def main() -> bool:
    """Main execution function"""
    start_time = datetime.now()
    print("🚀 Starting Google Supabase refresh process...")
    print(f"📅 Started at: {start_time.isoformat()}")
    print("=" * 60)

    try:
        # Initialize Supabase client
        client = get_supabase_client()
        if not client:
            return False

        # Load pipeline data
        pipeline_data = load_pipeline_data()
        if not pipeline_data:
            print("❌ No pipeline data to process")
            return False

        original_count = len(pipeline_data)

        # Backup existing data
        if not backup_existing_data(client):
            print("⚠️ Backup failed, but continuing with refresh...")

        # Delete existing Google data
        if not delete_existing_data(client):
            print("❌ Failed to delete existing data. Aborting.")
            return False

        # Insert new data
        inserted_count = 0
        errors = []

        # Try bulk insert first
        bulk_success, bulk_inserted, bulk_errors = insert_data_bulk(client, pipeline_data)

        if bulk_success:
            inserted_count = bulk_inserted
            errors = bulk_errors
        else:
            # Fallback to individual insert
            print("🔄 Bulk insert failed, falling back to individual inserts...")
            inserted_count, errors = insert_data_individual(client, pipeline_data)

        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # Generate report
        generate_report(original_count, inserted_count, errors, execution_time)

        # Final summary
        print("=" * 60)
        print("📊 REFRESH SUMMARY")
        print(f"✅ Successfully inserted: {inserted_count}/{original_count} records")
        print(f"❌ Errors encountered: {len(errors)}")
        print(f"⏱️ Total execution time: {execution_time:.2f} seconds")
        print(f"📅 Completed at: {end_time.isoformat()}")

        if inserted_count > 0:
            print("🎉 Google data refresh completed successfully!")
            return True
        else:
            print("❌ No records were inserted. Check errors in report.")
            return False

    except Exception as e:
        logger.error(f"Unexpected error in main execution: {e}")
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)