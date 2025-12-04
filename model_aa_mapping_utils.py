#!/usr/bin/env python3
"""
Shared Model-to-AA Mapping Utilities
=====================================

Single source of truth for refreshing ims.10_model_aa_mapping table.
Used by all pipeline working_version refresh scripts.

Purpose:
- Maps (inference_provider, provider_slug) from working_version to aa_slug
- Uses UPSERT pattern with ON CONFLICT for safe, idempotent updates
- Provides enhanced error reporting for unmatched models

Author: AI Models Discovery Pipeline
Version: 3.0 (Unified)
Last Updated: 2025-12-04
"""

import sys
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
import logging

try:
    import psycopg2
    from psycopg2.extras import execute_values
    import re
except ImportError:
    print("Error: psycopg2 package not found. Install with: pip install psycopg2-binary")
    sys.exit(1)


def normalize_slug(slug: str) -> str:
    """
    Normalize provider_slug to match aa_slug format.

    Converts special characters (periods, spaces, underscores) to hyphens
    to maintain consistency with aa_slug naming convention.

    Examples:
        "gpt-4.0" -> "gpt-4-0"
        "llama 3.1" -> "llama-3-1"
        "model_name_v2" -> "model-name-v2"

    Args:
        slug: Original provider_slug from working_version

    Returns:
        Normalized slug with special characters converted to hyphens
    """
    if not slug:
        return slug

    # Replace periods, spaces, and underscores with hyphens
    normalized = re.sub(r'[.\s_]+', '-', slug)

    # Remove consecutive hyphens
    normalized = re.sub(r'-+', '-', normalized)

    # Remove leading/trailing hyphens
    normalized = normalized.strip('-')

    # Convert to lowercase for consistency
    normalized = normalized.lower()

    return normalized


def fetch_working_version_models(
    conn,
    inference_provider: Optional[str] = None
) -> List[Tuple[str, str]]:
    """
    Fetch all unique (inference_provider, provider_slug) pairs from working_version.

    Args:
        conn: Database connection
        inference_provider: Optional filter for specific provider

    Returns:
        List of (inference_provider, provider_slug) tuples
    """
    try:
        with conn.cursor() as cur:
            if inference_provider:
                cur.execute("""
                    SELECT DISTINCT
                        inference_provider,
                        provider_slug
                    FROM public.working_version
                    WHERE provider_slug IS NOT NULL
                      AND provider_slug != ''
                      AND inference_provider = %s
                    ORDER BY inference_provider, provider_slug
                """, (inference_provider,))
            else:
                cur.execute("""
                    SELECT DISTINCT
                        inference_provider,
                        provider_slug
                    FROM public.working_version
                    WHERE provider_slug IS NOT NULL
                      AND provider_slug != ''
                    ORDER BY inference_provider, provider_slug
                """)

            models = cur.fetchall()
            return models
    except Exception as e:
        print(f"ERROR: Failed to fetch working_version models: {e}")
        return []


def fetch_aa_performance_slugs(conn) -> List[str]:
    """
    Fetch all unique aa_slug values from ims.20_aa_performance_metrics.

    Args:
        conn: Database connection

    Returns:
        List of aa_slug strings
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT aa_slug
                FROM ims."20_aa_performance_metrics"
                ORDER BY aa_slug
            """)
            aa_slugs = [row[0] for row in cur.fetchall()]
            return aa_slugs
    except Exception as e:
        print(f"ERROR: Failed to fetch AA performance slugs: {e}")
        return []


def match_provider_slug_to_aa_slug(
    provider_slug: str,
    inference_provider: str,
    aa_slugs: List[str]
) -> Optional[str]:
    """
    Attempt to match provider_slug to aa_slug using multiple strategies.

    Normalizes provider_slug first to match aa_slug format (converts special
    characters like periods, spaces, underscores to hyphens).

    Matching strategies (in order):
    1. Exact match: normalized_provider_slug == aa_slug
    2. Suffix match: aa_slug ends with normalized_provider_slug
    3. Contains match: normalized_provider_slug in aa_slug

    Args:
        provider_slug: The model slug from provider (will be normalized)
        inference_provider: The provider name (for logging)
        aa_slugs: List of available aa_slug values

    Returns:
        Matched aa_slug or None if no match found
    """
    # Normalize provider_slug to match aa_slug format
    normalized_slug = normalize_slug(provider_slug)

    # Strategy 1: Exact match
    for aa_slug in aa_slugs:
        if aa_slug.lower() == normalized_slug:
            return aa_slug

    # Strategy 2: Suffix match (e.g., "llama-3-1-8b-instant" matches "meta-llama-3-1-8b-instant")
    for aa_slug in aa_slugs:
        if aa_slug.lower().endswith(normalized_slug):
            return aa_slug

    # Strategy 3: Contains match (e.g., "gpt-4o" in "gpt-4o-2024-05-13")
    for aa_slug in aa_slugs:
        if normalized_slug in aa_slug.lower():
            return aa_slug

    return None


def create_mappings(
    models: List[Tuple[str, str]],
    aa_slugs: List[str],
    logger: Optional[logging.Logger] = None
) -> Tuple[List[Tuple], Dict[str, List[str]]]:
    """
    Create mappings between provider_slug and aa_slug with enhanced reporting.

    Args:
        models: List of (inference_provider, provider_slug) tuples
        aa_slugs: List of available aa_slug values
        logger: Optional logger for output

    Returns:
        Tuple of (mappings_list, unmatched_by_provider_dict)
    """
    log = logger.info if logger else print

    mappings = []
    unmatched_by_provider: Dict[str, List[str]] = {}
    matched_by_provider: Dict[str, int] = {}

    log("")
    log("=" * 70)
    log("MATCHING PROVIDER MODELS TO AA PERFORMANCE SLUGS")
    log("=" * 70)

    for inference_provider, provider_slug in models:
        aa_slug = match_provider_slug_to_aa_slug(provider_slug, inference_provider, aa_slugs)

        if aa_slug:
            # Normalize provider_slug to match aa_slug format (convert special chars to hyphens)
            normalized_provider_slug = normalize_slug(provider_slug)

            mappings.append((
                inference_provider,
                normalized_provider_slug,
                aa_slug,
                datetime.utcnow(),
                datetime.utcnow()
            ))
            matched_by_provider[inference_provider] = matched_by_provider.get(inference_provider, 0) + 1
        else:
            if inference_provider not in unmatched_by_provider:
                unmatched_by_provider[inference_provider] = []
            unmatched_by_provider[inference_provider].append(provider_slug)

    # Calculate statistics
    total_models = len(models)
    total_matched = len(mappings)
    total_unmatched = total_models - total_matched
    match_rate = (total_matched / total_models * 100) if total_models > 0 else 0

    log("")
    log("=" * 70)
    log("MAPPING RESULTS SUMMARY")
    log("=" * 70)
    log(f"✅ Total models processed: {total_models}")
    log(f"✅ Successfully matched: {total_matched} ({match_rate:.1f}%)")
    log(f"⚠️  Unmatched models: {total_unmatched}")
    log("")

    # Show matched breakdown by provider
    if matched_by_provider:
        log("Matched by provider:")
        for provider in sorted(matched_by_provider.keys()):
            log(f"  • {provider}: {matched_by_provider[provider]} models")
        log("")

    # Enhanced unmatched reporting - PROMINENT display
    if unmatched_by_provider:
        log("⚠️" * 35)
        log("UNMATCHED MODELS REQUIRING MANUAL REVIEW")
        log("⚠️" * 35)
        log("")
        log("The following models from working_version could not be automatically")
        log("mapped to AA performance metrics. These may need manual investigation:")
        log("")

        for provider in sorted(unmatched_by_provider.keys()):
            slugs = unmatched_by_provider[provider]
            log(f"📋 {provider} ({len(slugs)} unmatched):")
            log(f"   {'-' * 65}")
            for slug in sorted(slugs):
                log(f"   • {slug}")
            log("")

        log("⚠️" * 35)
        log("END OF UNMATCHED MODELS REPORT")
        log("⚠️" * 35)
        log("")

    return mappings, unmatched_by_provider


def upsert_mappings(
    conn,
    mappings: List[Tuple],
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Insert or update mappings in ims.10_model_aa_mapping using UPSERT pattern.

    Uses ON CONFLICT (inference_provider, provider_slug) DO UPDATE
    to safely handle duplicate keys.

    Args:
        conn: Database connection
        mappings: List of (inference_provider, provider_slug, aa_slug, created_at, updated_at) tuples
        logger: Optional logger for output

    Returns:
        True if successful, False otherwise
    """
    log = logger.info if logger else print

    if not mappings:
        log("⚠️  No mappings to insert")
        return True

    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO ims."10_model_aa_mapping"
                (inference_provider, provider_slug, aa_slug, created_at, updated_at)
                VALUES %s
                ON CONFLICT (inference_provider, provider_slug)
                DO UPDATE SET
                    aa_slug = EXCLUDED.aa_slug,
                    updated_at = EXCLUDED.updated_at
                """,
                mappings
            )
            conn.commit()
            log(f"✅ Successfully upserted {len(mappings)} mappings to ims.10_model_aa_mapping")
            return True
    except Exception as e:
        conn.rollback()
        log(f"❌ ERROR: Failed to upsert mappings: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        return False


def refresh_model_aa_mapping(
    conn,
    inference_provider: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Main entry point: Refresh ims.10_model_aa_mapping table from working_version.

    This function:
    1. Fetches models from working_version (optionally filtered by provider)
    2. Fetches AA performance slugs from ims.20_aa_performance_metrics
    3. Matches provider models to AA slugs using smart matching
    4. Upserts mappings with ON CONFLICT handling
    5. Provides enhanced reporting for unmatched models

    Args:
        conn: Database connection (must be open)
        inference_provider: Optional provider filter (e.g., "Groq")
        logger: Optional logger for structured output

    Returns:
        True if successful, False on critical error
    """
    log = logger.info if logger else print

    try:
        log("")
        log("=" * 70)
        if inference_provider:
            log(f"REFRESHING MODEL-AA MAPPINGS FOR: {inference_provider}")
        else:
            log("REFRESHING MODEL-AA MAPPINGS FOR: ALL PROVIDERS")
        log("=" * 70)
        log(f"Started: {datetime.now().isoformat()}")
        log("")

        # Step 1: Fetch models from working_version
        log("📁 Fetching models from working_version...")
        models = fetch_working_version_models(conn, inference_provider)
        if not models:
            log("⚠️  No models found in working_version")
            return False
        log(f"✅ Found {len(models)} unique models")

        # Step 2: Fetch AA performance slugs
        log("📁 Fetching AA performance metric slugs...")
        aa_slugs = fetch_aa_performance_slugs(conn)
        if not aa_slugs:
            log("⚠️  No AA performance slugs found")
            return False
        log(f"✅ Found {len(aa_slugs)} AA performance slugs")

        # Step 3: Create mappings with enhanced reporting
        mappings, unmatched_by_provider = create_mappings(models, aa_slugs, logger)

        # Step 4: Upsert mappings to database
        if not upsert_mappings(conn, mappings, logger):
            return False

        log("")
        log("=" * 70)
        log("✅ MODEL-AA MAPPING REFRESH COMPLETED")
        log("=" * 70)
        log(f"Completed: {datetime.now().isoformat()}")
        log("")

        return True

    except Exception as e:
        log(f"❌ ERROR: Unexpected error during mapping refresh: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    """
    Standalone execution for testing or manual runs.
    Requires PIPELINE_SUPABASE_URL environment variable.
    """
    import os

    DATABASE_URL = os.environ.get('PIPELINE_SUPABASE_URL')

    if not DATABASE_URL:
        print("ERROR: PIPELINE_SUPABASE_URL environment variable not set")
        sys.exit(1)

    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Connected to database")

        success = refresh_model_aa_mapping(conn)

        conn.close()
        print("Database connection closed")

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        sys.exit(1)
