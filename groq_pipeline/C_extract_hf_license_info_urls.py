#!/usr/bin/env python3
"""
Open source license mappings and utilities
Handles open source model licensing with priority-based detection from HuggingFace
"""

from typing import Dict
import requests


def check_url_accessible(url: str) -> bool:
    """Check if a URL is accessible with a HEAD request"""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except (requests.RequestException, requests.Timeout):
        return False


# =============================================================================
# HUGGINGFACE MODELS SECTION
# =============================================================================

def get_huggingface_license_info(hf_id: str) -> Dict[str, str]:
    """Get license information for HuggingFace models with priority order"""
    
    # HUGGINGFACE MODELS - Priority-Based LICENSE Detection
    if not hf_id:
        return {
            'license_info_text': '',
            'license_info_url': '',
            'license_name': '',
            'license_url': ''
        }
    
    base_url = f"https://huggingface.co/{hf_id}"
    
    # Priority 1: Try LICENSE first
    license_url = f"{base_url}/blob/main/LICENSE"
    if check_url_accessible(license_url):
        return {
            'license_info_text': 'info',
            'license_info_url': license_url,
            'license_name': '',
            'license_url': ''
        }
    
    # Priority 2: If LICENSE not accessible, try README.md
    readme_url = f"{base_url}/blob/main/README.md"
    if check_url_accessible(readme_url):
        return {
            'license_info_text': 'info',
            'license_info_url': readme_url,
            'license_name': '',
            'license_url': ''
        }
    
    # Priority 3: If README.md not accessible, try base repo page
    if check_url_accessible(base_url):
        return {
            'license_info_text': 'info',
            'license_info_url': base_url,
            'license_name': '',
            'license_url': ''
        }
    
    # Fallback: Return unknown if license URL not accessible
    return {
        'license_info_text': 'Unknown',
        'license_info_url': '',
        'license_name': 'Unknown',
        'license_url': ''
    }


def is_huggingface_model(hf_id: str) -> bool:
    """Check if model has HuggingFace ID"""
    return bool(hf_id and hf_id.strip())