#!/usr/bin/env python3
"""
Google Models Data Loading - Stage 1 Only

This script handles Stage 1: Loading existing model data from A-api-models-fetch.json.
It loads the complete model list and generates a human-readable report.

SPECIALIZED PIPELINE APPROACH:
- Stage 1: Data Loading (THIS SCRIPT)
- Stage 2: Model Filtering → B_models_filter.py
- Stage 3: Modality Scraping → C_modalities_scrape.py
- Stage 4: Modality Enrichment → D_modalities_enrich.py
- Stage 5: Database Normalization → E_db_schema_normalize.py

Use Z_run_complete_pipeline.py for orchestrated execution of all stages.

DOCUMENTATION SOURCES:
- API Reference: https://ai.google.dev/api/generate-text
- Rate Limits: https://ai.google.dev/gemini-api/docs/rate-limits  
- Official Model URLs: https://deepmind.google/models/[gemini|gemma|imagen|veo]
- License Terms: https://ai.google.dev/[gemini-api|gemma]/terms
"""
import json
import os
import requests
from datetime import datetime
from typing import Any, Dict, List
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# =============================================================================
# PIPELINE CONFIGURATION - OFFICIAL URL-DRIVEN REQUIREMENTS
# =============================================================================

# Documentation-First Data Architecture
# This configuration codifies the official URL-driven requirements pattern where
# Google's official documentation serves as the authoritative source for all data
# enrichment and validation, superseding API responses when conflicts arise.

PIPELINE_CONFIG = {
    # Core pipeline file outputs
    'output_files': {
        'stage_1': 'pipeline-outputs/A-api-models-fetch.json',
    },
    
    # AUTHORITATIVE SOURCE: Google Official Documentation URLs
    # These URLs serve as the ground truth for modality information extraction
    # Pattern: User provided URLs → Gap identified → Pipeline corrected
    'documentation_sources': {
        'modality_extraction_urls': [
            'https://ai.google.dev/gemini-api/docs/models',      # Gemini models (14 models)
            'https://ai.google.dev/gemini-api/docs/imagen',      # Image generation (2 families)
            'https://ai.google.dev/gemini-api/docs/video',       # Video generation (3 models)  
            'https://ai.google.dev/gemini-api/docs/embeddings'   # Text embedding (1 model)
        ],
        'rate_limits_authority': 'https://ai.google.dev/gemini-api/docs/rate-limits',
        'gemini_terms': 'https://ai.google.dev/gemini-api/terms',
        'gemma_terms': 'https://ai.google.dev/gemma/terms'
    },
    
    # OFFICIAL URLS: Model-family-specific documentation assignment
    # Rationale: "Direct user to the most relevant official documentation"
    # User instruction: "official urls for gemini models - https://deepmind.google/models/gemini/"
    'official_urls': {
        'Gemini': 'https://deepmind.google/models/gemini/',
        'Gemma': 'https://deepmind.google/models/gemma/', 
        'Embedding': 'https://ai.google.dev/gemini-api/docs/embeddings',
        'Imagen': 'https://deepmind.google/models/imagen/',
        'Veo': 'https://deepmind.google/models/veo/',
        'AQA': 'https://deepmind.google/models/gemini/'  # AQA uses Gemini URL per user instruction
    },
    
    # RATE LIMITS: Populated from official Google documentation
    # User instruction: "Rate limits are mentioned in https://ai.google.dev/gemini-api/docs/rate-limits"
    # Principle: Official documentation supersedes empty API fields
    'rate_limits_official': {
        # Gemini 2.5 models (latest)
        'gemini-2.5-pro': '5 requests/min, 250K tokens/min, 100 requests/day',
        'gemini-2.5-flash': '10 requests/min, 250K tokens/min, 250 requests/day',
        'gemini-2.5-flash-lite': '15 requests/min, 250K tokens/min, 1,000 requests/day',
        
        # Gemini 2.0 models
        'gemini-2.0-flash': '15 requests/min, 1M tokens/min, 200 requests/day',
        'gemini-2.0-flash-lite': '30 requests/min, 1M tokens/min, 200 requests/day',
        'gemini-2.0-flash-live': '15 requests/min, 1M tokens/min, 200 requests/day',
        
        # Gemini 1.5 models - Updated per user correction
        'gemini-1.5-pro': '15 requests/min, 250K tokens/min, 50 requests/day',
        'gemini-1.5-pro-002': '15 requests/min, 250K tokens/min, 50 requests/day',
        'gemini-1.5-flash': '15 requests/min, 250K tokens/min, 50 requests/day',
        'gemini-1.5-flash-8b': '15 requests/min, 250K tokens/min, 50 requests/day',
        
        # Gemma models (Open Source)
        'gemma': '30 requests/min, 15K tokens/min, 14,400 requests/day',
        
        # Embedding models
        'embedding': '100 requests/min, 30K tokens/min, 1,000 requests/day',
        
        # Image generation models  
        'imagen': 'Input: 480 tokens, Output: up to 4 images',
        
        # Video generation models
        'veo': 'Image input: up to 20MB, Output video: up to 2 minutes'
    },
    
    # LICENSE INFORMATION: Loaded from 01_google_models_licenses.json
    # Configuration file contains official license terms for each model family
    
    # DATA QUALITY STANDARDS: Documentation-first validation principles
    'quality_standards': {
        'modality_authority': 'official_documentation',  # Not API responses
        'embedding_output_correction': 'Text Embeddings',  # Not "Text" 
        'rate_limits_source': 'official_documentation',   # Not empty fields
        'url_assignment': 'model_family_specific',        # Not generic URLs
        'license_completeness': 'per_family_requirements' # Not assumptions
    }
}

# =============================================================================
# STAGE 1: RAW DATA EXTRACTION
# =============================================================================

def fetch_google_models_with_pagination() -> List[Dict[str, Any]]:
    """
    Fetch Google AI models with pagination support
    """
    import sys
    import os
    
    # Add utils directory to path for key_client import
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from utils.key_client import get_api_key, log_usage
    
    # Get API key from secure key management system
    api_key = get_api_key('google')
    if not api_key:
        print("ERROR: Failed to retrieve Google API key from secure storage")
        print("Please check key management system")
        return []
    
    try:
        print("Fetching Google AI models with pagination...")
        
        all_models = []
        page_token = None
        page_num = 1
        
        while True:
            url = 'https://generativelanguage.googleapis.com/v1beta/models'
            headers = {'x-goog-api-key': api_key}
            params = {}
            
            if page_token:
                params['pageToken'] = page_token
            
            print(f"Fetching page {page_num}...")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Log API usage for rate limit tracking
            if response.status_code == 200:
                log_usage('google', 'rpm', 1)  # 1 request per minute
                log_usage('google', 'rpd', 1)  # 1 request per day
            
            if response.status_code != 200:
                print(f"API error: {response.status_code}")
                break
            
            data = response.json()
            page_models = data.get('models', [])
            all_models.extend(page_models)
            
            print(f"Page {page_num}: {len(page_models)} models")
            
            # Check for next page
            page_token = data.get('nextPageToken')
            if not page_token:
                break
                
            page_num += 1
        
        print(f"Total models fetched: {len(all_models)}")
        return all_models
        
    except Exception as e:
        print(f"Error fetching Google models: {e}")
        return []

def stage_1_fetch_google_data() -> List[Dict[str, Any]]:
    """
    Stage 1: Fetch Google model data from API
    
    Returns:
        List of model dictionaries in raw JSON format
    """
    print("="*80)
    print("STAGE 1: FETCH DATA FROM GOOGLE API")
    print("="*80)
    
    filename = PIPELINE_CONFIG['output_files']['stage_1']
    
    # Fetch fresh data from API
    print("Fetching fresh data from Google API...")
    raw_data = fetch_google_models_with_pagination()
    if not raw_data:
        print("ERROR: Failed to fetch data from Google API")
        return []
    
    # Save the fetched data to JSON file
    try:
        with open(filename, 'w') as f:
            json.dump(raw_data, f, indent=2)
        print(f"Fresh data saved to: {filename}")
        print(f"Total models fetched: {len(raw_data)}")
    except Exception as e:
        print(f"ERROR: Failed to save data to {filename}: {e}")
        return raw_data  # Return data even if save failed
    
    # Generate human-readable text version
    txt_filename = 'A-api-models-fetch-report.txt'
    try:
        with open(txt_filename, 'w') as f:
            f.write(f"Total Models: {len(raw_data)}\n\n")
            
            for i, model in enumerate(raw_data, 1):
                name = model.get('name', 'Unknown')
                f.write(f"{i}. {name}\n")
        
        print(f"Human-readable version saved to: {txt_filename}")
    except Exception as e:
        print(f"Warning: Could not save report file: {e}")
    
    print(f"Stage 1 Complete: {len(raw_data)} models fetched")
    print()
    
    return raw_data


# =============================================================================
# PIPELINE ORCHESTRATOR
# =============================================================================

def run_google_stage_1():
    """
    Execute Stage 1: Load existing data from JSON file
    """
    print("Google Models Data Transformation Pipeline - Stage 1 Data Loading")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*80)
    
    try:
        # Stage 1: Fetch data from API
        raw_data = stage_1_fetch_google_data()
        if not raw_data:
            print("Pipeline aborted: No data from Stage 1")
            return False
        
        print("="*80)
        print("STAGE 1 COMPLETE - DATA LOADING")
        print("="*80)
        print(f"Loaded {len(raw_data)} models from existing JSON file")
        print(f"Source: {PIPELINE_CONFIG['output_files']['stage_1']}")
        print("\nNote: Stages 2-4 are now handled by specialized scripts:")
        print("  - Stage 2: B_models_filter.py")
        print("  - Stage 3: C_modalities_scrape.py")
        print("  - Stage 4: D_modalities_enrich.py")
        print("  - Use Z_run_complete_pipeline.py for full orchestration")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"Pipeline failed with error: {e}")
        print("Pipeline Status: FAILED")
        return False

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    success = run_google_stage_1()
    exit(0 if success else 1)