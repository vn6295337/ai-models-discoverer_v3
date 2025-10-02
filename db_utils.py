#!/usr/bin/env python3
"""
Database Utility Module for Pipeline Scripts
Provides PostgreSQL connection helpers for pipeline_writer role
"""

import os
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_pipeline_db_connection():
    """
    Create PostgreSQL connection using PIPELINE_SUPABASE_URL.

    Returns:
        connection: psycopg2 connection instance
        None: If connection fails
    """
    pipeline_url = os.getenv("PIPELINE_SUPABASE_URL")

    if not pipeline_url:
        logger.error("Missing required environment variable: PIPELINE_SUPABASE_URL")
        return None

    try:
        conn = psycopg2.connect(pipeline_url)
        conn.autocommit = False  # Use transactions
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return None


def get_record_count(conn, table_name: str, inference_provider: str) -> Optional[int]:
    """Get count of records for a specific inference provider."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE inference_provider = %s",
                (inference_provider,)
            )
            return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Failed to count records: {str(e)}")
        return None


def backup_records(conn, table_name: str, inference_provider: str) -> Optional[List[Dict[str, Any]]]:
    """Backup all records for a specific inference provider."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT * FROM {table_name} WHERE inference_provider = %s",
                (inference_provider,)
            )
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Failed to backup records: {str(e)}")
        return None


def delete_records(conn, table_name: str, inference_provider: str) -> bool:
    """Delete all records for a specific inference provider."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {table_name} WHERE inference_provider = %s",
                (inference_provider,)
            )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to delete records: {str(e)}")
        conn.rollback()
        return False


def insert_records_batch(conn, table_name: str, records: List[Dict[str, Any]], batch_size: int = 100) -> bool:
    """
    Insert records in batches.

    Args:
        conn: Database connection
        table_name: Target table
        records: List of dictionaries with column:value pairs
        batch_size: Number of records per batch

    Returns:
        bool: True if successful
    """
    if not records:
        return True

    try:
        # Get column names from first record
        columns = list(records[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)

        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        # Convert records to tuples
        values = [tuple(record[col] for col in columns) for record in records]

        with conn.cursor() as cur:
            execute_batch(cur, insert_sql, values, page_size=batch_size)

        conn.commit()
        return True

    except Exception as e:
        logger.error(f"Failed to insert records: {str(e)}")
        conn.rollback()
        return False


def load_staging_data(conn, staging_table: str, inference_provider: str) -> Optional[List[Dict[str, Any]]]:
    """Load data from staging table for specific provider."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT * FROM {staging_table} WHERE inference_provider = %s",
                (inference_provider,)
            )
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Failed to load staging data: {str(e)}")
        return None
