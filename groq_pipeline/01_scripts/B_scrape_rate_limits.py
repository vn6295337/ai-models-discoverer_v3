#!/usr/bin/env python3
"""
B_scrape_rate_limits.py
======================

Standalone rate limits scraper for Groq pipeline.
Extracts rate limits with dynamic loading support.

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
    print("GROQ RATE LIMITS SCRAPER")
    print("=" * 80)

    scraper = GroqWebScraper()

    # Scrape rate limits
    rate_limits = scraper.scrape_rate_limits()

    if not rate_limits:
        print("⚠️ No rate limits extracted")
        # Continue - rate limits are not critical

    # Save the results
    filename = '../02_outputs/stage-2-scrape-rate-limits.json'

    data = {
        'metadata': {
            'extraction_timestamp': datetime.now().isoformat(),
            'source_url': 'https://console.groq.com/docs/rate-limits',
            'total_models': len(rate_limits)
        },
        'rate_limits': rate_limits
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved {len(rate_limits)} rate limit records to: {filename}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)