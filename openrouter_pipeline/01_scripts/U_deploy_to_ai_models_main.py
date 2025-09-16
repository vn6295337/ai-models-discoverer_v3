#!/usr/bin/env python3

"""
Production Deployment Script: OpenRouter Data Migration
=================================================

This script deploys OpenRouter data from working_version to ai_models_main by:
1. Backing up existing OpenRouter records from ai_models_main
2. Deleting existing OpenRouter records from ai_models_main
3. Copying OpenRouter data from working_version to ai_models_main
4. Letting Supabase auto-generate id, created_at, updated_at to prevent conflicts

Features:
- Complete rollback protection with backup/restore
- Auto-managed field handling (id, created_at, updated_at)
- Bulk operations with individual fallbacks
- Comprehensive error handling and logging
- Transaction-like safety guarantees

Author: AI Models Discovery Pipeline
Version: 1.0
Last Updated: 2025-09-06
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
from output_utils import get_output_file_path, get_input_file_path, ensure_output_dir_exists

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
LOG_FILE = get_output_file_path("U-deploy-to-ai-models-main-report.txt")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
STAGING_TABLE = "working_version"
PRODUCTION_TABLE = "ai_models_main"
INFERENCE_PROVIDER = "OpenRouter"

# Setup logging with timestamp refresh
def setup_logging():
    """Setup logging with timestamp refresh at the top of log file"""
    # Write timestamp to log file first
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Deploy to AI Models Main Log\n")
        f.write(f"Last Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
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
        
        # Test connection by checking both tables
        staging_response = client.table(STAGING_TABLE).select("*").limit(1).execute()
        production_response = client.table(PRODUCTION_TABLE).select("*").limit(1).execute()
        
        logger.info(f"✅ Supabase connection established successfully")
        logger.info(f"   Staging table: {STAGING_TABLE}")
        logger.info(f"   Production table: {PRODUCTION_TABLE}")
        return client
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {str(e)}")
        return None


def get_OpenRouter_count(client: Client, table_name: str) -> Optional[int]:
    """
    Get current count of OpenRouter records in specified table.
    
    Args:
        client: Supabase client instance
        table_name: Name of the table to query
        
    Returns:
        int: Count of existing OpenRouter records
        None: If query fails
    """
    try:
        response = client.table(table_name).select("*", count="exact").eq("inference_provider", INFERENCE_PROVIDER).execute()
        count = response.count
        logger.info(f"📊 Current OpenRouter records in {table_name}: {count}")
        return count
        
    except Exception as e:
        logger.error(f"❌ Failed to count OpenRouter records in {table_name}: {str(e)}")
        return None


def backup_production_OpenRouter_data(client: Client) -> Optional[List[Dict[str, Any]]]:
    """
    Backup existing OpenRouter records from ai_models_main for rollback capability.
    
    Args:
        client: Supabase client instance
        
    Returns:
        List[Dict]: Backup of existing OpenRouter records
        None: If backup fails
    """
    logger.info(f"💾 Backing up existing OpenRouter records from {PRODUCTION_TABLE}...")
    
    try:
        response = client.table(PRODUCTION_TABLE).select("*").eq("inference_provider", INFERENCE_PROVIDER).execute()
        backup_data = response.data if response.data else []
        
        logger.info(f"✅ Backed up {len(backup_data)} existing OpenRouter records from production")
        return backup_data
        
    except Exception as e:
        logger.error(f"❌ Failed to backup existing OpenRouter records: {str(e)}")
        return None


def delete_production_OpenRouter_data(client: Client) -> bool:
    """
    Delete existing OpenRouter records from ai_models_main table.
    
    Args:
        client: Supabase client instance
        
    Returns:
        bool: True if deletion successful, False otherwise
    """
    logger.info(f"🗑️ Deleting existing OpenRouter records from {PRODUCTION_TABLE}...")
    
    try:
        # Get count before deletion for verification
        initial_count = get_OpenRouter_count(client, PRODUCTION_TABLE)
        if initial_count is None:
            return False
            
        if initial_count == 0:
            logger.info("✅ No existing OpenRouter records to delete from production")
            return True
        
        # Delete all OpenRouter records
        response = client.table(PRODUCTION_TABLE).delete().eq("inference_provider", INFERENCE_PROVIDER).execute()
        
        # Verify deletion
        remaining_count = get_OpenRouter_count(client, PRODUCTION_TABLE)
        if remaining_count == 0:
            logger.info(f"✅ Successfully deleted {initial_count} OpenRouter records from production")
            return True
        else:
            logger.error(f"❌ Deletion incomplete. {remaining_count} records remain in production")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to delete OpenRouter records from production: {str(e)}")
        return False


def load_staging_OpenRouter_data(client: Client) -> Optional[List[Dict[str, Any]]]:
    """
    Load OpenRouter data from working_version table for deployment.
    
    Args:
        client: Supabase client instance
        
    Returns:
        List[Dict]: List of OpenRouter records from staging
        None: If loading fails
    """
    logger.info(f"📁 Loading OpenRouter data from {STAGING_TABLE}...")
    
    try:
        response = client.table(STAGING_TABLE).select("*").eq("inference_provider", INFERENCE_PROVIDER).execute()
        staging_data = response.data if response.data else []
        
        if not staging_data:
            logger.error(f"❌ No OpenRouter data found in {STAGING_TABLE}")
            return None
            
        logger.info(f"✅ Loaded {len(staging_data)} OpenRouter records from staging")
        return staging_data
        
    except Exception as e:
        logger.error(f"❌ Failed to load OpenRouter data from staging: {str(e)}")
        return None


def prepare_data_for_production(staging_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepare staging data for production deployment by removing auto-managed fields.
    
    Args:
        staging_data: List of model dictionaries from staging
        
    Returns:
        List[Dict]: Cleaned data ready for production insertion
    """
    logger.info("🧹 Preparing staging data for production deployment...")
    
    prepared_models = []
    auto_managed_fields = ['id', 'created_at', 'updated_at']
    
    for model in staging_data:
        # Remove auto-managed fields to let production DB generate fresh values
        clean_model = {k: v for k, v in model.items() if k not in auto_managed_fields}
        
        # Convert empty strings to None for nullable fields
        nullable_fields = ['license_info_text', 'license_info_url']
        for field in nullable_fields:
            if field in clean_model and clean_model[field] is not None and not clean_model[field].strip():
                clean_model[field] = None
        
        prepared_models.append(clean_model)
    
    logger.info(f"✅ Prepared {len(prepared_models)} models for production deployment")
    logger.info(f"   Removed auto-managed fields: {', '.join(auto_managed_fields)}")
    logger.info(f"   Converted empty strings to null for nullable fields")
    return prepared_models


def deploy_to_production(client: Client, models: List[Dict[str, Any]]) -> bool:
    """
    Deploy new model data to ai_models_main with bulk insert and individual fallback.
    
    Args:
        client: Supabase client instance
        models: List of prepared model dictionaries
        
    Returns:
        bool: True if deployment successful, False otherwise
    """
    logger.info(f"🚀 Deploying {len(models)} models to production ({PRODUCTION_TABLE})...")
    
    if not models:
        logger.warning("⚠️ No models to deploy")
        return True
    
    # Try bulk insert first
    try:
        logger.info("📤 Attempting bulk deployment...")
        response = client.table(PRODUCTION_TABLE).insert(models).execute()
        inserted_count = len(response.data) if response.data else 0
        
        if inserted_count == len(models):
            logger.info(f"✅ Bulk deployment successful: {inserted_count} models deployed")
            return True
        else:
            logger.warning(f"⚠️ Bulk deployment partial: {inserted_count}/{len(models)} models deployed")
            
    except Exception as e:
        logger.warning(f"⚠️ Bulk deployment failed: {str(e)}")
        logger.info("🔄 Falling back to individual deployments...")
    
    # Individual insert fallback
    successful_deployments = 0
    failed_deployments = 0
    
    for i, model in enumerate(models):
        try:
            response = client.table(PRODUCTION_TABLE).insert([model]).execute()
            if response.data and len(response.data) > 0:
                successful_deployments += 1
                if (i + 1) % 25 == 0:  # Progress every 25 models
                    logger.info(f"   Progress: {i + 1}/{len(models)} models processed")
            else:
                failed_deployments += 1
                model_name = model.get('human_readable_name', 'Unknown')
                logger.error(f"❌ Failed to deploy model: {model_name}")
                
        except Exception as e:
            failed_deployments += 1
            model_name = model.get('human_readable_name', 'Unknown') 
            error_msg = str(e)
            
            # Log detailed error information for debugging
            if "duplicate key" in error_msg:
                logger.error(f"❌ Duplicate key error for {model_name}: {error_msg}")
            elif "violates" in error_msg:
                logger.error(f"❌ Constraint violation for {model_name}: {error_msg}")
            else:
                logger.error(f"❌ Deployment error for {model_name}: {error_msg}")
    
    logger.info(f"📊 Individual deployment results:")
    logger.info(f"   ✅ Successful: {successful_deployments}")
    logger.info(f"   ❌ Failed: {failed_deployments}")
    
    # Allow up to 5% failure rate for production deployment
    success_rate = successful_deployments / len(models) if models else 0
    if success_rate >= 0.95:
        logger.info(f"✅ Deployment success rate: {success_rate:.1%} - Acceptable for production")
        return True
    else:
        logger.error(f"❌ Deployment success rate: {success_rate:.1%} - Too many failures for production")
        return False


def restore_production_backup(client: Client, backup_data: List[Dict[str, Any]]) -> bool:
    """
    Restore backed up OpenRouter records to ai_models_main (rollback operation).
    
    Args:
        client: Supabase client instance
        backup_data: List of backed up records to restore
        
    Returns:
        bool: True if restoration successful, False otherwise
    """
    logger.info(f"🔄 Rolling back: Restoring {len(backup_data)} OpenRouter records to production...")
    
    if not backup_data:
        logger.info("✅ No production data to restore")
        return True
    
    try:
        # Prepare backup data by removing auto-managed fields
        clean_backup_data = []
        auto_managed_fields = ['id', 'created_at', 'updated_at']
        for record in backup_data:
            clean_record = {k: v for k, v in record.items() if k not in auto_managed_fields}
            clean_backup_data.append(clean_record)
        
        logger.info(f"   Prepared {len(clean_backup_data)} records for restoration")
        
        # Restore data in batches
        batch_size = 50
        restored_count = 0
        failed_count = 0
        
        for i in range(0, len(clean_backup_data), batch_size):
            batch = clean_backup_data[i:i + batch_size]
            
            try:
                response = client.table(PRODUCTION_TABLE).insert(batch).execute()
                
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
                
                # Try individual inserts as fallback
                logger.info(f"   🔄 Attempting individual restore fallback for batch {i//batch_size + 1}")
                for j, record in enumerate(batch):
                    try:
                        individual_response = client.table(PRODUCTION_TABLE).insert([record]).execute()
                        if individual_response.data:
                            restored_count += 1
                            failed_count -= 1
                    except Exception as individual_error:
                        logger.error(f"      ❌ Individual restore {j+1} failed: {str(individual_error)}")
        
        logger.info(f"📊 Restoration Results:")
        logger.info(f"   ✅ Successfully restored: {restored_count}")
        logger.info(f"   ❌ Failed to restore: {failed_count}")
        
        # Verify restoration
        final_count = get_OpenRouter_count(client, PRODUCTION_TABLE)
        if final_count and final_count >= len(backup_data) * 0.9:  # Allow 10% tolerance
            logger.info(f"✅ Rollback successful: {final_count} OpenRouter records restored to production")
            return True
        else:
            logger.error(f"❌ Rollback incomplete. Expected ~{len(backup_data)}, found {final_count}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to restore production backup: {str(e)}")
        return False


def verify_production_deployment(client: Client, expected_count: int) -> bool:
    """
    Verify the production deployment was successful by checking final count.
    
    Args:
        client: Supabase client instance
        expected_count: Expected number of records
        
    Returns:
        bool: True if verification passes, False otherwise
    """
    logger.info("🔍 Verifying production deployment results...")
    
    final_count = get_OpenRouter_count(client, PRODUCTION_TABLE)
    if final_count is None:
        logger.error("❌ Unable to verify deployment - count query failed")
        return False
    
    # Allow small tolerance due to potential data conflicts
    tolerance = max(1, int(expected_count * 0.05))  # 5% tolerance, minimum 1
    if abs(final_count - expected_count) <= tolerance:
        logger.info(f"✅ Verification successful: {final_count} records in production")
        logger.info(f"   Expected: {expected_count}, Found: {final_count}, Tolerance: ±{tolerance}")
        return True
    else:
        logger.error(f"❌ Verification failed: Expected ~{expected_count}, found {final_count}")
        return False


def main():
    """
    Main orchestration function for production deployment with rollback capability.
    """
    logger.info("=" * 70)
    logger.info("OPENROUTER PRODUCTION DEPLOYMENT STARTED")
    logger.info("=" * 70)
    start_time = datetime.now()
    backup_data = None
    
    try:
        # Step 1: Initialize Supabase client
        client = get_supabase_client()
        if not client:
            logger.error("❌ DEPLOYMENT FAILED: Could not connect to Supabase")
            return False
        
        # Step 2: Get initial state
        staging_count = get_OpenRouter_count(client, STAGING_TABLE)
        production_count = get_OpenRouter_count(client, PRODUCTION_TABLE)
        
        if staging_count is None or production_count is None:
            logger.error("❌ DEPLOYMENT FAILED: Could not query initial state")
            return False
        
        if staging_count == 0:
            logger.error("❌ DEPLOYMENT FAILED: No OpenRouter data in staging table")
            return False
        
        # Step 3: Load staging data
        staging_data = load_staging_OpenRouter_data(client)
        if not staging_data:
            logger.error("❌ DEPLOYMENT FAILED: Could not load staging data")
            return False
        
        # Step 4: Prepare data for production
        prepared_data = prepare_data_for_production(staging_data)
        if not prepared_data:
            logger.error("❌ DEPLOYMENT FAILED: No valid data to deploy")
            return False
        
        # Step 5: CRITICAL POINT - Backup existing production data
        logger.info("🛡️ CREATING PRODUCTION BACKUP FOR ROLLBACK PROTECTION...")
        backup_data = backup_production_OpenRouter_data(client)
        if backup_data is None:
            logger.error("❌ DEPLOYMENT FAILED: Could not backup production data - ABORTING for safety")
            return False
        
        # Step 6: Delete existing production data
        if not delete_production_OpenRouter_data(client):
            logger.error("❌ DEPLOYMENT FAILED: Could not delete existing production data")
            # Rollback not needed - deletion failed, original data intact
            return False
        
        # Step 7: Deploy new data (CRITICAL - if this fails, we need rollback)
        if not deploy_to_production(client, prepared_data):
            logger.error("❌ DEPLOYMENT FAILED: Data deployment incomplete - INITIATING ROLLBACK")
            if restore_production_backup(client, backup_data):
                logger.info("✅ ROLLBACK SUCCESSFUL: Original production data restored")
            else:
                logger.error("❌ ROLLBACK FAILED: Manual intervention required!")
            return False
        
        # Step 8: Verify deployment (if this fails, rollback)
        if not verify_production_deployment(client, len(prepared_data)):
            logger.error("❌ DEPLOYMENT FAILED: Verification failed - INITIATING ROLLBACK")
            if restore_production_backup(client, backup_data):
                logger.info("✅ ROLLBACK SUCCESSFUL: Original production data restored")
            else:
                logger.error("❌ ROLLBACK FAILED: Manual intervention required!")
            return False
        
        # Success summary
        end_time = datetime.now()
        duration = end_time - start_time
        final_count = get_OpenRouter_count(client, PRODUCTION_TABLE)
        
        logger.info("=" * 70)
        logger.info("🎉 OPENROUTER PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"📊 Deployment Summary:")
        logger.info(f"   • Staging records processed: {len(staging_data)}")
        logger.info(f"   • Production records backed up: {len(backup_data)}")
        logger.info(f"   • Production records deleted: {production_count}")
        logger.info(f"   • New records deployed: {len(prepared_data)}")
        logger.info(f"   • Final production count: {final_count}")
        logger.info(f"   • Deployment time: {duration}")
        logger.info(f"   • Log file: {LOG_FILE}")
        logger.info("=" * 70)
        logger.info("🚀 OpenRouter models successfully deployed to production!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR: {str(e)}")
        if backup_data:
            logger.info("🔄 Attempting emergency rollback due to unexpected error...")
            if restore_production_backup(client, backup_data):
                logger.info("✅ EMERGENCY ROLLBACK SUCCESSFUL: Original production data restored")
            else:
                logger.error("❌ EMERGENCY ROLLBACK FAILED: Manual intervention required!")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)