#!/usr/bin/env python3
"""
C_scrape_modalities.py
=====================

Standalone modalities scraper for Groq pipeline.
Extracts input/output modalities for each model.

Author: AI Models Discovery Pipeline
Version: 1.0
"""

import sys
import os
import json
from datetime import datetime

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '04_utils'))
from groq_web_scraper import GroqWebScraper

def main():
    """Main execution function"""
    print("=" * 80)
    print("GROQ MODALITIES SCRAPER")
    print("=" * 80)

    # Load production models from stage 1
    try:
        with open('../02_outputs/stage-1-scrape-production-models.json', 'r', encoding='utf-8') as f:
            stage1_data = json.load(f)
            production_models = stage1_data['production_models']
    except FileNotFoundError:
        print("❌ Error: stage-1-scrape-production-models.json not found")
        print("   Please run A_scrape_production_models.py first")
        return False
    except Exception as e:
        print(f"❌ Error loading production models: {e}")
        return False

    scraper = GroqWebScraper()

    # Scrape modalities
    modalities_data = scraper.scrape_model_modalities(production_models)

    if not modalities_data:
        print("⚠️ No modalities extracted")
        # Continue - modalities are not critical

    # Transform data to include model_id field for each model
    transformed_modalities = {}
    for model_key, modality_info in modalities_data.items():
        transformed_modalities[model_key] = {
            'model_id': model_key,
            'input_modalities': modality_info['input_modalities'],
            'output_modalities': modality_info['output_modalities']
        }

    # Save the results
    filename = '../02_outputs/stage-3-scrape-modalities.json'

    data = {
        'metadata': {
            'extraction_timestamp': datetime.now().isoformat(),
            'source_base_url': 'https://console.groq.com/docs/model/',
            'total_models': len(transformed_modalities)
        },
        'modalities': transformed_modalities
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved modalities for {len(modalities_data)} models to: {filename}")

    # Show summary
    for model_id, modalities in modalities_data.items():
        input_mod = ', '.join(modalities['input_modalities'])
        output_mod = ', '.join(modalities['output_modalities'])
        print(f"   📋 {model_id}: {input_mod} → {output_mod}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)