#!/usr/bin/env python3
"""
G_normalize_data.py
==================

Standalone data normalization script for Groq pipeline.
Normalizes all extracted data into database-ready format.

Author: AI Models Discovery Pipeline
Version: 1.0
"""

import sys
import os
import json
from datetime import datetime

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '04_utils'))
from groq_data_processor import GroqDataProcessor

def main():
    """Main execution function"""
    print("=" * 80)
    print("GROQ DATA NORMALIZATION")
    print("=" * 80)

    processor = GroqDataProcessor()

    # Normalize all data
    normalized_data = processor.populate_normalized_data()

    if not normalized_data:
        print("❌ Data normalization failed")
        return False

    print(f"✅ Normalized {len(normalized_data)} records")

    # Show final statistics
    print("\n📊 NORMALIZATION STATISTICS:")
    providers = set(record['model_provider'] for record in normalized_data)
    print(f"   • Total models processed: {len(normalized_data)}")
    print(f"   • Unique providers: {len(providers)}")
    print(f"   • Providers: {', '.join(sorted(providers))}")
    print(f"   • Models with modalities: {sum(1 for r in normalized_data if r.get('input_modalities'))}")
    print(f"   • Models with rate limits: {sum(1 for r in normalized_data if r.get('rate_limits'))}")
    print(f"   • Models with license info: {sum(1 for r in normalized_data if r.get('license_name'))}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)