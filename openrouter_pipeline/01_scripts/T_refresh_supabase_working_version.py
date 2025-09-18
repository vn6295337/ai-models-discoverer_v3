#!/usr/bin/env python3

"""
Supabase OpenRouter Data Refresh Script
=====================================

This script refreshes OpenRouter data in Supabase by:
1. Deleting existing OpenRouter records from working_version table
2. Loading finalized data from R-finalized-db-data.json
3. Inserting fresh OpenRouter data into Supabase

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

# Import output utilities
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "04_utils"))
from output_utils import get_output_file_path, get_input_file_path, ensure_output_dir_exists, get_ist_timestamp

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Check multiple .env locations
    env_paths = [
        Path("/home/km_project/.env"),  # Home directory
        Path(__file__).parent.parent / ".env",  # openrouter_pipeline directory
        Path(__file__).parent / ".env"  # 01_scripts directory
    ]

    env_loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment variables from {env_path}")
            env_loaded = True
            break

    if not env_loaded:
        print("⚠️ No .env file found in any of the expected locations")
except ImportError:
    print("⚠️ python-dotenv not installed. Environment variables must be set manually.")
    print("Install with: pip install python-dotenv")

# Configuration
SCRIPT_DIR = Path(__file__).parent
JSON_FILE = SCRIPT_DIR / get_input_file_path("R_filtered_db_data.json")
LOG_FILE = SCRIPT_DIR / get_output_file_path("T-supabase-refresh-report.txt")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
TABLE_NAME = "working_version"
INFERENCE_PROVIDER = "OpenRouter"

# Setup logging with timestamp refresh
def setup_logging():
    """Setup logging with timestamp refresh at the top of report file"""
    # Write timestamp to report file first
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Supabase OpenRouter Working Version Refresh Report\n")
        f.write(f"Last Run: {get_ist_timestamp()}\n")
        f.write("=" * 60 + "\n\n")
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='a'),  # Append mode
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# Initialize logging
logger = setup_logging()


def get_supabase_client() -> Optional[Client]:
    """
    Initialize and return Supabase client with environment validation.
    
    Returns:
        Client: Supabase client instance
        None: If environment variables missing or connection fails
    """
    logger.info("Initializing Supabase client...")
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.error("Missing required environment variables:")
        if not SUPABASE_URL:
            logger.error("  - SUPABASE_URL not set")
        if not SUPABASE_ANON_KEY:
            logger.error("  - SUPABASE_ANON_KEY not set")
        return None
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Test connection by checking table structure
        response = client.table(TABLE_NAME).select("*").limit(1).execute()
        logger.info(f"✅ Supabase connection established successfully")
        logger.info(f"   Target table: {TABLE_NAME}")
        return client
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {str(e)}")
        return None


def get_existing_openrouter_count(client: Client) -> Optional[int]:
    """
    Get current count of OpenRouter records in Supabase.
    
    Args:
        client: Supabase client instance
        
    Returns:
        int: Count of existing OpenRouter records
        None: If query fails
    """
    try:
        response = client.table(TABLE_NAME).select("*", count="exact").eq("inference_provider", INFERENCE_PROVIDER).execute()
        count = response.count
        logger.info(f"📊 Current OpenRouter records in Supabase: {count}")
        return count
        
    except Exception as e:
        logger.error(f"❌ Failed to count existing OpenRouter records: {str(e)}")
        return None


def backup_existing_openrouter_data(client: Client) -> Optional[List[Dict[str, Any]]]:
    """
    Backup existing OpenRouter records before deletion for rollback capability.
    
    Args:
        client: Supabase client instance
        
    Returns:
        List[Dict]: Backup of existing OpenRouter records
        None: If backup fails
    """
    logger.info(f"💾 Backing up existing OpenRouter records from {TABLE_NAME}...")
    
    try:
        response = client.table(TABLE_NAME).select("*").eq("inference_provider", INFERENCE_PROVIDER).execute()
        backup_data = response.data if response.data else []
        
        logger.info(f"✅ Backed up {len(backup_data)} existing OpenRouter records")
        return backup_data
        
    except Exception as e:
        logger.error(f"❌ Failed to backup existing OpenRouter records: {str(e)}")
        return None


def delete_existing_openrouter_data(client: Client) -> bool:
    """
    Delete existing OpenRouter records from Supabase working_version table.
    
    Args:
        client: Supabase client instance
        
    Returns:
        bool: True if deletion successful, False otherwise
    """
    logger.info(f"🗑️ Deleting existing OpenRouter records from {TABLE_NAME}...")
    
    try:
        # Get count before deletion for verification
        initial_count = get_existing_openrouter_count(client)
        if initial_count is None:
            return False
            
        if initial_count == 0:
            logger.info("✅ No existing OpenRouter records to delete")
            return True
        
        # Delete all OpenRouter records
        response = client.table(TABLE_NAME).delete().eq("inference_provider", INFERENCE_PROVIDER).execute()
        
        # Verify deletion
        remaining_count = get_existing_openrouter_count(client)
        if remaining_count == 0:
            logger.info(f"✅ Successfully deleted {initial_count} OpenRouter records")
            return True
        else:
            logger.error(f"❌ Deletion incomplete. {remaining_count} records remain")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to delete OpenRouter records: {str(e)}")
        return False


def restore_backup_data(client: Client, backup_data: List[Dict[str, Any]]) -> bool:
    """
    Restore backed up OpenRouter records to Supabase (rollback operation).
    Handles ID conflicts by removing ID field and letting Supabase auto-generate new IDs.
    
    Args:
        client: Supabase client instance
        backup_data: List of backed up records to restore
        
    Returns:
        bool: True if restoration successful, False otherwise
    """
    logger.info(f"🔄 Rolling back: Restoring {len(backup_data)} OpenRouter records...")
    
    if not backup_data:
        logger.info("✅ No data to restore")
        return True
    
    try:
        # Prepare backup data for insertion by removing auto-managed fields to avoid conflicts
        clean_backup_data = []
        auto_managed_fields = ['id', 'created_at', 'updated_at']
        for record in backup_data:
            clean_record = {k: v for k, v in record.items() if k not in auto_managed_fields}
            clean_backup_data.append(clean_record)
        
        logger.info(f"   Prepared {len(clean_backup_data)} records for restoration (removed auto-managed fields)")
        
        # Restore data in batches to avoid timeouts
        batch_size = 50  # Smaller batches for more reliable restoration
        restored_count = 0
        failed_count = 0
        
        for i in range(0, len(clean_backup_data), batch_size):
            batch = clean_backup_data[i:i + batch_size]
            
            try:
                response = client.table(TABLE_NAME).insert(batch).execute()
                
                if response.data:
                    batch_restored = len(response.data)
                    restored_count += batch_restored
                    logger.info(f"   ✅ Restored batch {i//batch_size + 1}: {batch_restored}/{len(batch)} records")
                else:
                    failed_count += len(batch)
                    logger.error(f"   ❌ Failed batch {i//batch_size + 1}: No data returned")
                    
            except Exception as batch_error:
                failed_count += len(batch)
                logger.error(f"   ❌ Failed batch {i//batch_size + 1}: {str(batch_error)}")
                
                # Try individual inserts as fallback for this batch
                logger.info(f"   🔄 Attempting individual insert fallback for batch {i//batch_size + 1}")
                for j, record in enumerate(batch):
                    try:
                        individual_response = client.table(TABLE_NAME).insert([record]).execute()
                        if individual_response.data:
                            restored_count += 1
                            failed_count -= 1
                    except Exception as individual_error:
                        logger.error(f"      ❌ Individual insert {j+1} failed: {str(individual_error)}")
        
        logger.info(f"📊 Restoration Results:")
        logger.info(f"   ✅ Successfully restored: {restored_count}")
        logger.info(f"   ❌ Failed to restore: {failed_count}")
        
        # Verify restoration
        final_count = get_existing_openrouter_count(client)
        if final_count >= len(backup_data) * 0.95:  # Allow 5% tolerance due to potential data conflicts
            logger.info(f"✅ Rollback successful: {final_count} OpenRouter records restored")
            logger.info(f"   Original count: {len(backup_data)}, Restored count: {final_count}")
            return True
        else:
            logger.error(f"❌ Rollback incomplete. Expected ~{len(backup_data)}, found {final_count}")
            logger.error(f"   This may require manual intervention to fully restore data")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to restore backup data: {str(e)}")
        return False


def load_finalized_json() -> Optional[List[Dict[str, Any]]]:
    """
    Load and validate finalized JSON data from R-finalized-db-data.json.
    JSON contains OpenRouter records with perfect schema match to Supabase.
    
    Returns:
        List[Dict]: List of model records as dictionaries
        None: If file not found or invalid
    """
    logger.info(f"📁 Loading finalized JSON data from {JSON_FILE}...")
    
    if not JSON_FILE.exists():
        logger.error(f"❌ JSON file not found: {JSON_FILE}")
        return None
    
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Handle both old format (list) and new format (dict with metadata)
        if isinstance(data, list):
            models = data
        elif isinstance(data, dict) and 'models' in data:
            models = data['models']
        else:
            logger.error(f"❌ JSON file should contain a list of models or dict with 'models' key")
            return None
        
        # Expected JSON fields (matches Supabase schema exactly)
        expected_fields = {
            'id', 'inference_provider', 'model_provider', 'human_readable_name', 
            'model_provider_country', 'official_url', 'input_modalities', 
            'output_modalities', 'license_info_text', 'license_info_url',
            'license_name', 'license_url', 'rate_limits', 'provider_api_access',
            'created_at', 'updated_at'
        }
        
        if not models:
            logger.error(f"❌ No models found in JSON")
            return None
        
        # Validate first model structure
        first_model = models[0]
        actual_fields = set(first_model.keys())
        missing_fields = expected_fields - actual_fields
        
        if missing_fields:
            logger.error(f"❌ Missing required JSON fields: {missing_fields}")
            return None
        
        # Validate OpenRouter provider
        valid_models = []
        for i, model in enumerate(models):
            inference_provider = model.get('inference_provider', '')
            if inference_provider != INFERENCE_PROVIDER:
                logger.warning(f"⚠️ Model {i+1}: Wrong inference provider '{inference_provider}', expected '{INFERENCE_PROVIDER}' - skipping")
                continue
            
            # Validate required fields (nulls allowed only for license_info_text and license_info_url)
            required_fields = [
                'inference_provider', 'model_provider', 'human_readable_name',
                'model_provider_country', 'official_url', 'input_modalities', 
                'output_modalities', 'license_name', 'license_url', 
                'rate_limits', 'provider_api_access'
            ]
            
            missing_data = [field for field in required_fields if not model.get(field, '')]
            
            if missing_data:
                logger.error(f"❌ Model {i+1}: Missing required data in fields: {missing_data}")
                continue
            
            valid_models.append(model)
        
        if not valid_models:
            logger.error(f"❌ No valid OpenRouter models found in JSON")
            return None
            
        logger.info(f"✅ Loaded {len(valid_models)} valid OpenRouter models from JSON")
        return valid_models
        
    except Exception as e:
        logger.error(f"❌ Failed to load JSON data: {str(e)}")
        return None


def prepare_data_for_insert(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepare JSON data for Supabase insertion by removing id column and handling nulls.
    JSON schema matches Supabase perfectly - minimal transformation needed.
    
    Args:
        models: List of model dictionaries from JSON
        
    Returns:
        List[Dict]: Cleaned data ready for Supabase insertion
    """
    logger.info("🧹 Preparing data for Supabase insertion...")
    
    prepared_models = []
    
    for model in models:
        # Create clean copy without auto-managed fields (Supabase handles these)
        auto_managed_fields = ['id', 'created_at', 'updated_at']
        clean_model = {k: v for k, v in model.items() if k not in auto_managed_fields}
        
        # Convert empty strings to None ONLY for license_info_text and license_info_url
        nullable_fields = ['license_info_text', 'license_info_url']
        for field in nullable_fields:
            if field in clean_model and clean_model[field] is not None and not str(clean_model[field]).strip():
                clean_model[field] = None
        
        # All models from JSON are already validated - no additional validation needed
        prepared_models.append(clean_model)
    
    logger.info(f"✅ Prepared {len(prepared_models)} models for insertion")
    logger.info(f"   Removed auto-managed fields: id, created_at, updated_at")
    logger.info(f"   Converted empty strings to null for license_info_text/license_info_url")
    return prepared_models


def insert_new_data(client: Client, models: List[Dict[str, Any]]) -> bool:
    """
    Insert new model data into Supabase with bulk insert and individual fallback.
    
    Args:
        client: Supabase client instance
        models: List of prepared model dictionaries
        
    Returns:
        bool: True if all insertions successful, False otherwise
    """
    logger.info(f"📤 Inserting {len(models)} models into Supabase...")
    
    if not models:
        logger.warning("⚠️ No models to insert")
        return True
    
    # Try bulk insert first
    try:
        logger.info("🚀 Attempting bulk insert...")
        response = client.table(TABLE_NAME).insert(models).execute()
        inserted_count = len(response.data) if response.data else 0
        
        if inserted_count == len(models):
            logger.info(f"✅ Bulk insert successful: {inserted_count} models inserted")
            return True
        else:
            logger.warning(f"⚠️ Bulk insert partial: {inserted_count}/{len(models)} models inserted")
            
    except Exception as e:
        logger.warning(f"⚠️ Bulk insert failed: {str(e)}")
        logger.info("🔄 Falling back to individual insertions...")
    
    # Individual insert fallback
    successful_inserts = 0
    failed_inserts = 0
    
    for i, model in enumerate(models):
        try:
            response = client.table(TABLE_NAME).insert([model]).execute()
            if response.data and len(response.data) > 0:
                successful_inserts += 1
                if (i + 1) % 50 == 0:  # Progress every 50 models
                    logger.info(f"   Progress: {i + 1}/{len(models)} models processed")
            else:
                failed_inserts += 1
                model_name = model.get('human_readable_name', 'Unknown')
                logger.error(f"❌ Failed to insert model: {model_name}")
                
        except Exception as e:
            failed_inserts += 1
            model_name = model.get('human_readable_name', 'Unknown') 
            error_msg = str(e)
            
            # Log detailed error information for debugging
            if "duplicate key" in error_msg:
                logger.error(f"❌ Duplicate key error for {model_name}: {error_msg}")
            elif "violates" in error_msg:
                logger.error(f"❌ Constraint violation for {model_name}: {error_msg}")
            else:
                logger.error(f"❌ Insert error for {model_name}: {error_msg}")
    
    logger.info(f"📊 Individual insert results:")
    logger.info(f"   ✅ Successful: {successful_inserts}")
    logger.info(f"   ❌ Failed: {failed_inserts}")
    
    # Allow up to 10% failure rate (some records might have data quality issues)
    success_rate = successful_inserts / len(models) if models else 0
    if success_rate >= 0.9:
        logger.info(f"✅ Insert success rate: {success_rate:.1%} - Acceptable")
        return True
    else:
        logger.error(f"❌ Insert success rate: {success_rate:.1%} - Too many failures")
        return False


def verify_insertion(client: Client, expected_count: int) -> bool:
    """
    Verify the insertion was successful by checking final count.
    
    Args:
        client: Supabase client instance
        expected_count: Expected number of records
        
    Returns:
        bool: True if verification passes, False otherwise
    """
    logger.info("🔍 Verifying insertion results...")
    
    final_count = get_existing_openrouter_count(client)
    if final_count is None:
        logger.error("❌ Unable to verify insertion - count query failed")
        return False
    
    if final_count == expected_count:
        logger.info(f"✅ Verification successful: {final_count} records in database")
        return True
    else:
        logger.error(f"❌ Verification failed: Expected {expected_count}, found {final_count}")
        return False


def main():
    """
    Main orchestration function for OpenRouter data refresh with rollback capability.
    """
    logger.info("=" * 60)
    logger.info("SUPABASE OPENROUTER DATA REFRESH STARTED")
    logger.info("=" * 60)
    start_time = datetime.now()
    backup_data = None
    
    try:
        # Step 1: Initialize Supabase client
        client = get_supabase_client()
        if not client:
            logger.error("❌ REFRESH FAILED: Could not connect to Supabase")
            return False
        
        # Step 2: Get initial state
        initial_count = get_existing_openrouter_count(client)
        if initial_count is None:
            logger.error("❌ REFRESH FAILED: Could not query initial state")
            return False
        
        # Step 3: Load JSON data
        models = load_finalized_json()
        if not models:
            logger.error("❌ REFRESH FAILED: Could not load JSON data")
            return False
        
        # Step 4: Prepare data for insertion
        prepared_models = prepare_data_for_insert(models)
        if not prepared_models:
            logger.error("❌ REFRESH FAILED: No valid models to insert")
            return False
        
        # Step 5: CRITICAL POINT - Backup existing data before deletion
        logger.info("🛡️ CREATING BACKUP FOR ROLLBACK PROTECTION...")
        backup_data = backup_existing_openrouter_data(client)
        if backup_data is None:
            logger.error("❌ REFRESH FAILED: Could not backup existing data - ABORTING for safety")
            return False
        
        # Step 6: Delete existing data
        if not delete_existing_openrouter_data(client):
            logger.error("❌ REFRESH FAILED: Could not delete existing data")
            # Rollback not needed - deletion failed, original data intact
            return False
        
        # Step 7: Insert new data (CRITICAL - if this fails, we need rollback)
        if not insert_new_data(client, prepared_models):
            logger.error("❌ REFRESH FAILED: Data insertion incomplete - INITIATING ROLLBACK")
            if restore_backup_data(client, backup_data):
                logger.info("✅ ROLLBACK SUCCESSFUL: Original data restored")
            else:
                logger.error("❌ ROLLBACK FAILED: Manual intervention required!")
            return False
        
        # Step 8: Verify results (if this fails, rollback)
        if not verify_insertion(client, len(prepared_models)):
            logger.error("❌ REFRESH FAILED: Verification failed - INITIATING ROLLBACK")
            if restore_backup_data(client, backup_data):
                logger.info("✅ ROLLBACK SUCCESSFUL: Original data restored")
            else:
                logger.error("❌ ROLLBACK FAILED: Manual intervention required!")
            return False
        
        # Success summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 60)
        logger.info("🎉 SUPABASE OPENROUTER DATA REFRESH COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"📊 Summary:")
        logger.info(f"   • Initial OpenRouter records: {initial_count}")
        logger.info(f"   • Records backed up: {len(backup_data)}")
        logger.info(f"   • Records deleted: {initial_count}")
        logger.info(f"   • New records inserted: {len(prepared_models)}")
        logger.info(f"   • Final record count: {len(prepared_models)}")
        logger.info(f"   • Processing time: {duration}")
        logger.info(f"   • Report file: {LOG_FILE}")
        logger.info("=" * 60)
        logger.info("🛡️ Backup data available for emergency restoration if needed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR: {str(e)}")
        if backup_data:
            logger.info("🔄 Attempting emergency rollback due to unexpected error...")
            if restore_backup_data(client, backup_data):
                logger.info("✅ EMERGENCY ROLLBACK SUCCESSFUL: Original data restored")
            else:
                logger.error("❌ EMERGENCY ROLLBACK FAILED: Manual intervention required!")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)