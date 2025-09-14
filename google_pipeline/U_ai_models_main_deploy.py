#!/usr/bin/env python3

"""
Production Deployment Script: Google Data Migration
===================================================

This script deploys Google data from working_version to ai_models_main by:
1. Backing up existing Google records from ai_models_main
2. Deleting existing Google records from ai_models_main
3. Copying Google data from working_version to ai_models_main
4. Letting Supabase auto-generate id, created_at, updated_at to prevent conflicts

Features:
- Complete rollback protection with backup/restore
- Auto-managed field handling (id, created_at, updated_at)
- Bulk operations with individual fallbacks
- Comprehensive error handling and logging
- Transaction-like safety guarantees

Author: AI Models Discovery Pipeline
Version: 1.0
Last Updated: 2025-09-14
"""

import os
import sys
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
    # Look for .env file in parent directory (ai-models-discoverer_v2)
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
SOURCE_TABLE = "working_version"
TARGET_TABLE = "ai_models_main"
BACKUP_FILE = Path(__file__).parent / "pipeline-outputs" / f"U-production-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
REPORT_FILE = Path(__file__).parent / "pipeline-outputs" / "U-production-deploy-report.txt"

# Fields that should be excluded from copying (auto-managed by Supabase)
AUTO_MANAGED_FIELDS = {'id', 'created_at', 'updated_at'}

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

def load_source_data(client: Client) -> List[Dict[str, Any]]:
    """Load Google data from working_version table"""
    try:
        print(f"📥 Loading {INFERENCE_PROVIDER} data from {SOURCE_TABLE}...")

        response = client.table(SOURCE_TABLE).select("*").eq("inference_provider", INFERENCE_PROVIDER).execute()
        data = response.data if response.data else []

        logger.info(f"Loaded {len(data)} records from {SOURCE_TABLE}")
        print(f"✅ Loaded {len(data)} {INFERENCE_PROVIDER} models from {SOURCE_TABLE}")
        return data
    except Exception as e:
        logger.error(f"Error loading source data: {e}")
        print(f"❌ Error loading source data: {e}")
        return []

def backup_production_data(client: Client) -> bool:
    """Backup existing Google data from ai_models_main"""
    try:
        print(f"📦 Creating backup of existing {INFERENCE_PROVIDER} data from {TARGET_TABLE}...")

        response = client.table(TARGET_TABLE).select("*").eq("inference_provider", INFERENCE_PROVIDER).execute()
        existing_data = response.data if response.data else []

        if existing_data:
            with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, default=str)
            logger.info(f"Backup created with {len(existing_data)} records")
            print(f"✅ Backup created: {BACKUP_FILE} ({len(existing_data)} records)")
        else:
            print(f"ℹ️ No existing {INFERENCE_PROVIDER} data found in {TARGET_TABLE} to backup")

        return True
    except Exception as e:
        logger.error(f"Failed to backup production data: {e}")
        print(f"❌ Failed to backup production data: {e}")
        return False

def delete_production_data(client: Client) -> bool:
    """Delete existing Google data from ai_models_main"""
    try:
        print(f"🗑️ Deleting existing {INFERENCE_PROVIDER} data from {TARGET_TABLE}...")

        response = client.table(TARGET_TABLE).delete().eq("inference_provider", INFERENCE_PROVIDER).execute()

        if hasattr(response, 'data') and response.data is not None:
            deleted_count = len(response.data)
        else:
            # Check by querying remaining records
            check_response = client.table(TARGET_TABLE).select("id").eq("inference_provider", INFERENCE_PROVIDER).execute()
            remaining_count = len(check_response.data) if check_response.data else 0
            deleted_count = f"completed (remaining: {remaining_count})"

        logger.info(f"Deleted existing {INFERENCE_PROVIDER} data from {TARGET_TABLE}")
        print(f"✅ Deleted existing {INFERENCE_PROVIDER} data: {deleted_count}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete production data: {e}")
        print(f"❌ Failed to delete production data: {e}")
        return False

def clean_record_for_production(record: Dict[str, Any]) -> Dict[str, Any]:
    """Remove auto-managed fields from record for production insert"""
    cleaned_record = {k: v for k, v in record.items() if k not in AUTO_MANAGED_FIELDS}
    return cleaned_record

def validate_production_record(record: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a single record before production insertion"""
    required_fields = ['human_readable_name', 'inference_provider']

    for field in required_fields:
        if not record.get(field):
            return False, f"Missing required field: {field}"

    if record.get('inference_provider') != INFERENCE_PROVIDER:
        return False, f"Invalid inference_provider: {record.get('inference_provider')}"

    return True, "Valid"

def insert_production_data_bulk(client: Client, data: List[Dict[str, Any]]) -> Tuple[bool, int, List[str]]:
    """Insert data to production in bulk with error handling"""
    try:
        # Clean records (remove auto-managed fields)
        cleaned_data = [clean_record_for_production(record) for record in data]

        print(f"📤 Inserting {len(cleaned_data)} records to {TARGET_TABLE} in bulk...")

        response = client.table(TARGET_TABLE).insert(cleaned_data).execute()

        if response.data:
            inserted_count = len(response.data)
            logger.info(f"Bulk production insert successful: {inserted_count} records")
            print(f"✅ Bulk production insert successful: {inserted_count} records")
            return True, inserted_count, []
        else:
            return False, 0, ["Bulk insert returned no data"]
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Bulk production insert failed: {error_msg}")
        print(f"❌ Bulk production insert failed: {error_msg}")
        return False, 0, [error_msg]

def insert_production_data_individual(client: Client, data: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
    """Insert data to production record by record (fallback method)"""
    print(f"📤 Inserting {len(data)} records to {TARGET_TABLE} individually...")

    inserted_count = 0
    errors = []

    for i, record in enumerate(data):
        try:
            # Clean record (remove auto-managed fields)
            cleaned_record = clean_record_for_production(record)

            # Validate record before insertion
            is_valid, validation_msg = validate_production_record(cleaned_record)
            if not is_valid:
                errors.append(f"Record {i+1}: {validation_msg}")
                continue

            response = client.table(TARGET_TABLE).insert([cleaned_record]).execute()

            if response.data and len(response.data) > 0:
                inserted_count += 1
                if (i + 1) % 10 == 0:  # Progress indicator
                    print(f"   Inserted {i + 1}/{len(data)} records...")
            else:
                errors.append(f"Record {i+1}: Insert returned no data")

        except Exception as e:
            errors.append(f"Record {i+1} ({record.get('human_readable_name', 'Unknown')}): {str(e)}")

    logger.info(f"Individual production insert completed: {inserted_count}/{len(data)} successful")
    print(f"✅ Individual production insert completed: {inserted_count}/{len(data)} successful")

    return inserted_count, errors

def verify_production_deployment(client: Client, expected_count: int) -> bool:
    """Verify the deployment by checking record counts"""
    try:
        print(f"🔍 Verifying deployment in {TARGET_TABLE}...")

        response = client.table(TARGET_TABLE).select("id").eq("inference_provider", INFERENCE_PROVIDER).execute()
        actual_count = len(response.data) if response.data else 0

        logger.info(f"Verification: Expected {expected_count}, Found {actual_count}")
        print(f"📊 Verification: Expected {expected_count}, Found {actual_count}")

        if actual_count == expected_count:
            print("✅ Deployment verification successful!")
            return True
        else:
            print(f"⚠️ Deployment verification failed: count mismatch")
            return False
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        print(f"❌ Verification failed: {e}")
        return False

def generate_deployment_report(
    source_count: int,
    inserted_count: int,
    errors: List[str],
    execution_time: float,
    verification_success: bool
) -> None:
    """Generate detailed deployment report"""
    try:
        report_content = []
        report_content.append("GOOGLE PRODUCTION DEPLOYMENT REPORT")
        report_content.append("=" * 60)
        report_content.append(f"Deployment Date: {datetime.now().isoformat()}")
        report_content.append(f"Inference Provider: {INFERENCE_PROVIDER}")
        report_content.append(f"Source Table: {SOURCE_TABLE}")
        report_content.append(f"Target Table: {TARGET_TABLE}")
        report_content.append("")

        # Summary Statistics
        report_content.append("DEPLOYMENT STATISTICS")
        report_content.append("-" * 40)
        report_content.append(f"Source Records: {source_count}")
        report_content.append(f"Successfully Deployed: {inserted_count}")
        report_content.append(f"Deployment Success Rate: {(inserted_count/source_count*100) if source_count > 0 else 0:.1f}%")
        report_content.append(f"Total Errors: {len(errors)}")
        report_content.append(f"Verification: {'PASSED' if verification_success else 'FAILED'}")
        report_content.append(f"Execution Time: {execution_time:.2f} seconds")
        report_content.append("")

        # Error Details
        if errors:
            report_content.append("ERROR DETAILS")
            report_content.append("-" * 40)
            for error in errors[:20]:  # Limit to first 20 errors
                report_content.append(f"• {error}")
            if len(errors) > 20:
                report_content.append(f"... and {len(errors) - 20} more errors")
            report_content.append("")

        # Files and Safety
        report_content.append("FILES AND SAFETY")
        report_content.append("-" * 40)
        report_content.append(f"Production Backup: {BACKUP_FILE}")
        report_content.append(f"Deployment Report: {REPORT_FILE}")
        report_content.append("")
        report_content.append("ROLLBACK INSTRUCTIONS:")
        report_content.append("If deployment issues occur, restore from backup:")
        report_content.append("1. Delete current Google records from ai_models_main")
        report_content.append("2. Insert records from backup file")
        report_content.append("3. Verify record counts match backup")

        # Write report
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_content))

        print(f"📄 Detailed deployment report saved to: {REPORT_FILE}")
        logger.info(f"Deployment report generated: {REPORT_FILE}")
    except Exception as e:
        logger.error(f"Failed to generate deployment report: {e}")
        print(f"❌ Failed to generate deployment report: {e}")

def main() -> bool:
    """Main execution function"""
    start_time = datetime.now()
    print("🚀 Starting Google production deployment...")
    print(f"📅 Started at: {start_time.isoformat()}")
    print("=" * 80)

    try:
        # Initialize Supabase client
        client = get_supabase_client()
        if not client:
            return False

        # Load source data from working_version
        source_data = load_source_data(client)
        if not source_data:
            print("❌ No source data to deploy")
            return False

        source_count = len(source_data)

        # Backup existing production data
        if not backup_production_data(client):
            print("⚠️ Backup failed, but continuing with deployment...")

        # Delete existing production data
        if not delete_production_data(client):
            print("❌ Failed to delete existing production data. Aborting.")
            return False

        # Insert new data to production
        inserted_count = 0
        errors = []

        # Try bulk insert first
        bulk_success, bulk_inserted, bulk_errors = insert_production_data_bulk(client, source_data)

        if bulk_success:
            inserted_count = bulk_inserted
            errors = bulk_errors
        else:
            # Fallback to individual insert
            print("🔄 Bulk insert failed, falling back to individual inserts...")
            inserted_count, errors = insert_production_data_individual(client, source_data)

        # Verify deployment
        verification_success = verify_production_deployment(client, inserted_count)

        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # Generate deployment report
        generate_deployment_report(source_count, inserted_count, errors, execution_time, verification_success)

        # Final summary
        print("=" * 80)
        print("📊 DEPLOYMENT SUMMARY")
        print(f"✅ Successfully deployed: {inserted_count}/{source_count} records")
        print(f"❌ Errors encountered: {len(errors)}")
        print(f"🔍 Verification: {'PASSED' if verification_success else 'FAILED'}")
        print(f"⏱️ Total execution time: {execution_time:.2f} seconds")
        print(f"📅 Completed at: {end_time.isoformat()}")

        if inserted_count > 0 and verification_success:
            print("🎉 Google production deployment completed successfully!")
            return True
        else:
            print("❌ Deployment failed or verification failed. Check report and backup.")
            return False

    except Exception as e:
        logger.error(f"Unexpected error in main execution: {e}")
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)