#!/usr/bin/env python3
"""
Groq Complete Pipeline - End-to-End Data Extraction and Normalization
Combines: production models extraction → rate limits extraction → modalities extraction → data normalization
Output files: 01_production_models.json, 02_rate_limits.json, 03_input_output_modalities.json, stage-3-data-normalization.csv
"""

import json
import csv
import time
import datetime
import re
from pathlib import Path
from typing import List, Dict, Any

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required dependencies not available")
    print("Please install: selenium, webdriver-manager, beautifulsoup4")
    exit(1)

def setup_chrome_driver():
    """Set up Chrome driver with consistent options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# =============================================================================
# STAGE 1: EXTRACT PRODUCTION MODELS
# =============================================================================

def scrape_production_models() -> List[Dict[str, Any]]:
    """Scrape production models from Groq documentation including production systems"""
    print("=" * 80)
    print("🚀 STAGE 1: GROQ PRODUCTION MODELS EXTRACTION")
    print("=" * 80)
    print(f"🕒 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    driver = setup_chrome_driver()
    print("✅ ChromeDriver automatically managed")

    try:
        # Extract from production-models section
        url_production = 'https://console.groq.com/docs/models#production-models'
        print(f"🔍 Extracting production models from: {url_production}")

        driver.get(url_production)
        print("⏳ Waiting for dynamic content...")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )
        print("✅ Page content loaded")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tables = soup.find_all('table')
        print(f"📊 Found {len(tables)} tables in production-models section")

        production_models = []

        for i, table in enumerate(tables):
            print(f"✅ Processing production models table {i+1}")

            header_row = table.find('tr')
            if not header_row:
                continue

            headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
            print(f"📋 Production Models headers: {headers}")

            if not ('MODEL ID' in [h.upper() for h in headers]):
                continue

            # Find column indices
            model_col = next((i for i, h in enumerate(headers) if 'model' in h.lower()), 0)
            developer_col = next((i for i, h in enumerate(headers) if 'developer' in h.lower()), 1)
            context_col = next((i for i, h in enumerate(headers) if 'context' in h.lower()), 2)
            completion_col = next((i for i, h in enumerate(headers) if 'completion' in h.lower()), 3)

            # Parse data rows
            data_rows = table.find_all('tr')[1:]  # Skip header
            print(f"📊 Found {len(data_rows)} data rows in Production Models")

            for row_num, row in enumerate(data_rows, 1):
                cells = row.find_all(['td', 'th'])
                if len(cells) > model_col:
                    model_id = cells[model_col].get_text().strip()

                    if model_id and model_id.lower() not in ['model', 'model id', '']:
                        model_data = {
                            'model_id': model_id,
                            'object': 'model',
                            'created': int(time.time()),
                            'model_provider': cells[developer_col].get_text().strip() if len(cells) > developer_col else 'Groq',
                            'active': True,
                            'context_window': cells[context_col].get_text().strip().replace(',', '') if len(cells) > context_col else '',
                            'max_completion_tokens': cells[completion_col].get_text().strip().replace(',', '') if len(cells) > completion_col else '',
                            'public_apps': True,
                            'source_section': 'production-models'
                        }

                        production_models.append(model_data)
                        print(f"   ✅ Row {row_num}: {model_data['model_id']} ({model_data['model_provider']})")

            break  # Only process first valid table

        # Extract from production-systems section
        url_systems = 'https://console.groq.com/docs/models#production-systems'
        print(f"\n🔍 Extracting production systems from: {url_systems}")

        driver.get(url_systems)
        print("⏳ Waiting for dynamic content...")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )
        print("✅ Page content loaded")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tables = soup.find_all('table')
        print(f"📊 Found {len(tables)} tables in production-systems section")

        for i, table in enumerate(tables):
            print(f"✅ Processing production systems table {i+1}")

            header_row = table.find('tr')
            if not header_row:
                continue

            headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
            print(f"📋 Production Systems headers: {headers}")

            # Look for model-related columns (more flexible matching)
            has_model_column = any('model' in h.lower() for h in headers)
            if not has_model_column:
                continue

            # Find column indices with flexible matching
            model_col = next((i for i, h in enumerate(headers) if 'model' in h.lower()), 0)
            developer_col = next((i for i, h in enumerate(headers) if any(keyword in h.lower() for keyword in ['developer', 'provider', 'company'])), 1)
            context_col = next((i for i, h in enumerate(headers) if 'context' in h.lower()), 2)
            completion_col = next((i for i, h in enumerate(headers) if any(keyword in h.lower() for keyword in ['completion', 'max', 'output'])), 3)

            # Parse data rows
            data_rows = table.find_all('tr')[1:]  # Skip header
            print(f"📊 Found {len(data_rows)} data rows in Production Systems")

            for row_num, row in enumerate(data_rows, 1):
                cells = row.find_all(['td', 'th'])
                if len(cells) > model_col:
                    model_id = cells[model_col].get_text().strip()

                    if model_id and model_id.lower() not in ['model', 'model id', '']:
                        # Check if this model is already in our list
                        existing_model = next((m for m in production_models if m['model_id'] == model_id), None)

                        if not existing_model:
                            model_data = {
                                'model_id': model_id,
                                'object': 'model',
                                'created': int(time.time()),
                                'model_provider': cells[developer_col].get_text().strip() if len(cells) > developer_col else 'Groq',
                                'active': True,
                                'context_window': cells[context_col].get_text().strip().replace(',', '') if len(cells) > context_col else '',
                                'max_completion_tokens': cells[completion_col].get_text().strip().replace(',', '') if len(cells) > completion_col else '',
                                'public_apps': True,
                                'source_section': 'production-systems'
                            }

                            production_models.append(model_data)
                            print(f"   ✅ Row {row_num}: {model_data['model_id']} ({model_data['model_provider']}) [SYSTEMS]")
                        else:
                            print(f"   ⚠️  Row {row_num}: {model_id} already exists from production-models section")

            break  # Only process first valid table
        
        driver.quit()
        print("🔒 Browser closed successfully")
        print(f"✅ Total production models extracted: {len(production_models)}")
        
        return production_models
        
    except Exception as error:
        print(f"❌ Error scraping production models: {error}")
        try:
            driver.quit()
        except:
            pass
        return []

def save_production_models(production_models: List[Dict[str, Any]]) -> str:
    """Save production models to stage-1-scrape-production-models.json"""
    filename = 'stage-1-scrape-production-models.json'

    # Count models by source section
    production_models_count = sum(1 for m in production_models if m.get('source_section') == 'production-models')
    production_systems_count = sum(1 for m in production_models if m.get('source_section') == 'production-systems')

    data = {
        'extraction_timestamp': datetime.datetime.now().isoformat(),
        'source_urls': [
            'https://console.groq.com/docs/models#production-models',
            'https://console.groq.com/docs/models#production-systems'
        ],
        'total_models': len(production_models),
        'models_by_source': {
            'production-models': production_models_count,
            'production-systems': production_systems_count
        },
        'production_models': production_models
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Saved {len(production_models)} production models to: {filename}")
    return filename

# =============================================================================
# STAGE 2: EXTRACT RATE LIMITS
# =============================================================================

def scrape_rate_limits() -> Dict[str, Dict[str, str]]:
    """Scrape rate limits from Groq documentation"""
    print("\n" + "=" * 80)
    print("🚀 STAGE 2: GROQ RATE LIMITS EXTRACTION")
    print("=" * 80)
    print(f"🕒 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    driver = setup_chrome_driver()
    print("✅ ChromeDriver automatically managed")
    
    try:
        url = 'https://console.groq.com/docs/rate-limits'
        print(f"🔍 Extracting rate limits from: {url}")
        
        driver.get(url)
        print("⏳ Waiting for page and dynamic content to load...")
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )
        
        # Wait for data to populate - try multiple times
        max_attempts = 5
        data_found = False
        
        for attempt in range(max_attempts):
            print(f"⏳ Attempt {attempt + 1}/{max_attempts}: Waiting for data to populate...")
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                header_row = table.find('tr')
                if header_row:
                    headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                    if 'MODEL ID' in [h.upper() for h in headers]:
                        data_rows = table.find_all('tr')[1:]
                        if len(data_rows) > 0:
                            first_row_cells = [cell.get_text().strip() for cell in data_rows[0].find_all(['td', 'th'])]
                            if any(cell for cell in first_row_cells):
                                data_found = True
                                print(f"✅ Data loaded successfully on attempt {attempt + 1}")
                                break
            
            if data_found:
                break
        
        if not data_found:
            print("⚠️ Failed to load dynamic rate limits data after all attempts")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tables = soup.find_all('table')
        
        rate_limits = {}
        
        for i, table in enumerate(tables):
            print(f"✅ Processing rate limits table {i+1}")
            
            header_row = table.find('tr')
            if not header_row:
                continue
                
            headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
            print(f"📋 Rate Limits headers: {headers}")
            
            header_upper = [h.upper() for h in headers]
            is_rate_table = ('MODEL ID' in header_upper and 
                           any(col in header_upper for col in ['RPM', 'TPM', 'ASH']))
            
            if not is_rate_table:
                continue
                
            print(f"✅ Found rate limits table with headers: {headers}")
                
            # Find column indices
            model_col = next((i for i, h in enumerate(headers) if 'model' in h.lower()), 0)
            rpm_col = next((i for i, h in enumerate(headers) if h.upper() == 'RPM'), -1)
            rpd_col = next((i for i, h in enumerate(headers) if h.upper() == 'RPD'), -1)
            tpm_col = next((i for i, h in enumerate(headers) if h.upper() == 'TPM'), -1)
            tpd_col = next((i for i, h in enumerate(headers) if h.upper() == 'TPD'), -1)
            ash_col = next((i for i, h in enumerate(headers) if h.upper() == 'ASH'), -1)
            asd_col = next((i for i, h in enumerate(headers) if h.upper() == 'ASD'), -1)
            
            # Parse data rows
            data_rows = table.find_all('tr')[1:]  # Skip header
            print(f"📊 Found {len(data_rows)} data rows in Rate Limits")
            
            if len(data_rows) == 0:
                print("⚠️ Rate limits table is empty - data may not have loaded yet")
                continue
                
            # Verify data rows have content
            rows_with_content = []
            for row in data_rows:
                cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                if any(cell for cell in cells):  # Has non-empty cells
                    rows_with_content.append(row)
            
            if len(rows_with_content) == 0:
                print("⚠️ Rate limits table rows are empty - continuing")
                continue
                
            print(f"📊 Processing {len(rows_with_content)} rows with actual data")
            data_rows = rows_with_content
                
            for row_num, row in enumerate(data_rows, 1):
                cells = row.find_all(['td', 'th'])
                if len(cells) > model_col:
                    model_id = cells[model_col].get_text().strip()
                    
                    if model_id and model_id.lower() not in ['model', 'model id', '']:
                        rate_limit_data = {
                            'model_id': model_id,
                            'RPM': cells[rpm_col].get_text().strip() if rpm_col >= 0 and len(cells) > rpm_col else '-',
                            'RPD': cells[rpd_col].get_text().strip() if rpd_col >= 0 and len(cells) > rpd_col else '-',
                            'TPM': cells[tpm_col].get_text().strip() if tpm_col >= 0 and len(cells) > tpm_col else '-',
                            'TPD': cells[tpd_col].get_text().strip() if tpd_col >= 0 and len(cells) > tpd_col else '-',
                            'ASH': cells[ash_col].get_text().strip() if ash_col >= 0 and len(cells) > ash_col else '-',
                            'ASD': cells[asd_col].get_text().strip() if asd_col >= 0 and len(cells) > asd_col else '-'
                        }
                        
                        rate_limits[model_id] = rate_limit_data
                        print(f"   ✅ Row {row_num}: {model_id} - RPM:{rate_limit_data['RPM']}, TPM:{rate_limit_data['TPM']}")
            
            break  # Only process first valid table
        
        driver.quit()
        print("🔒 Browser closed successfully")
        print(f"✅ Total rate limits extracted: {len(rate_limits)}")
        
        return rate_limits
        
    except Exception as error:
        print(f"❌ Error scraping rate limits: {error}")
        try:
            driver.quit()
        except:
            pass
        return {}

def save_rate_limits(rate_limits: Dict[str, Dict[str, str]]) -> str:
    """Save rate limits to stage-2-scrape-rate-limits.json"""
    filename = 'stage-2-scrape-rate-limits.json'
    
    data = {
        'extraction_timestamp': datetime.datetime.now().isoformat(),
        'source_url': 'https://console.groq.com/docs/rate-limits',
        'total_models': len(rate_limits),
        'rate_limits': rate_limits
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Saved {len(rate_limits)} rate limit records to: {filename}")
    return filename

# =============================================================================
# STAGE 3: EXTRACT INPUT/OUTPUT MODALITIES
# =============================================================================

def load_production_models_for_modalities() -> List[Dict[str, Any]]:
    """Load production models from stage-1-scrape-production-models.json"""
    try:
        with open('stage-1-scrape-production-models.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('production_models', [])
    except FileNotFoundError:
        print("❌ ERROR: stage-1-scrape-production-models.json not found")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in stage-1-scrape-production-models.json: {e}")
        return []

def extract_modalities_for_model(driver, model_id: str) -> Dict[str, List[str]]:
    """Extract input and output modalities for a specific model"""
    url = f"https://console.groq.com/docs/model/{model_id}"
    print(f"   🔍 Extracting modalities from: {url}")
    
    try:
        driver.get(url)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        page_text = soup.get_text()
        
        input_modalities = []
        output_modalities = []
        
        # Look for INPUT/OUTPUT div elements
        input_divs = soup.find_all(['div', 'span'], string=lambda text: text and text.strip().upper() == 'INPUT')
        output_divs = soup.find_all(['div', 'span'], string=lambda text: text and text.strip().upper() == 'OUTPUT')
        
        print(f"      🔍 Found {len(input_divs)} INPUT divs, {len(output_divs)} OUTPUT divs")
        
        # Extract content after INPUT sections
        for input_div in input_divs:
            if input_div.parent:
                parent_text = input_div.parent.get_text().lower()
                
                if 'audio' in parent_text and 'Audio' not in input_modalities:
                    input_modalities.append('Audio')
                    print(f"         ➡️ Input: Audio")
                if 'text' in parent_text and 'Text' not in input_modalities:
                    input_modalities.append('Text')
                    print(f"         ➡️ Input: Text")
                if 'image' in parent_text and 'Image' not in input_modalities:
                    input_modalities.append('Image')
                    print(f"         ➡️ Input: Image")
                if 'video' in parent_text and 'Video' not in input_modalities:
                    input_modalities.append('Video')
                    print(f"         ➡️ Input: Video")
        
        # Extract content after OUTPUT sections  
        for output_div in output_divs:
            if output_div.parent:
                parent_text = output_div.parent.get_text().lower()
                
                if 'audio' in parent_text and 'Audio' not in output_modalities:
                    output_modalities.append('Audio')
                    print(f"         ⬅️ Output: Audio")
                if 'text' in parent_text and 'Text' not in output_modalities:
                    output_modalities.append('Text')
                    print(f"         ⬅️ Output: Text")
                if 'image' in parent_text and 'Image' not in output_modalities:
                    output_modalities.append('Image')
                    print(f"         ⬅️ Output: Image")
                if 'video' in parent_text and 'Video' not in output_modalities:
                    output_modalities.append('Video')
                    print(f"         ⬅️ Output: Video")
        
        # Fallback logic based on model type if no modalities found
        if not input_modalities and not output_modalities:
            print(f"      ⚠️ No modalities found in webpage content, using model type fallback")
            
            if 'whisper' in model_id.lower():
                input_modalities = ['Audio']
                output_modalities = ['Text']
            elif 'tts' in model_id.lower():
                input_modalities = ['Text']
                output_modalities = ['Audio']
            elif any(model_type in model_id.lower() for model_type in ['llama', 'gpt', 'guard', 'qwen', 'gemma']):
                input_modalities = ['Text']
                output_modalities = ['Text']
                
                if 'guard' in model_id.lower():
                    input_modalities = ['Image', 'Text']
            else:
                input_modalities = ['Text']
                output_modalities = ['Text']
            
            print(f"         ➡️ Fallback Input: {', '.join(input_modalities)}")
            print(f"         ⬅️ Fallback Output: {', '.join(output_modalities)}")
        
        return {
            'input_modalities': input_modalities,
            'output_modalities': output_modalities
        }
        
    except Exception as error:
        print(f"      ❌ Error extracting modalities for {model_id}: {error}")
        
        # Fallback based on model type
        if 'whisper' in model_id.lower():
            return {'input_modalities': ['Audio'], 'output_modalities': ['Text']}
        elif 'tts' in model_id.lower():
            return {'input_modalities': ['Text'], 'output_modalities': ['Audio']}
        elif 'guard' in model_id.lower():
            return {'input_modalities': ['Image', 'Text'], 'output_modalities': ['Text']}
        else:
            return {'input_modalities': ['Text'], 'output_modalities': ['Text']}

def scrape_all_modalities() -> Dict[str, Dict[str, List[str]]]:
    """Scrape input/output modalities for all production models"""
    print("\n" + "=" * 80)
    print("🚀 STAGE 3: GROQ INPUT/OUTPUT MODALITIES EXTRACTION")
    print("=" * 80)
    print(f"🕒 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    production_models = load_production_models_for_modalities()
    if not production_models:
        return {}
    
    print(f"📋 Found {len(production_models)} production models to process")
    
    driver = setup_chrome_driver()
    print("✅ ChromeDriver automatically managed")
    
    try:
        all_modalities = {}
        
        # Process each model
        for i, model in enumerate(production_models, 1):
            model_id = model.get('model_id')
            if not model_id:
                print(f"⚠️ Model {i} has no 'model_id' field, skipping")
                continue
            
            print(f"📊 Processing model {i}/{len(production_models)}: {model_id}")
            
            # Extract modalities for this model
            modalities = extract_modalities_for_model(driver, model_id)
            all_modalities[model_id] = modalities
            
            # Brief pause between requests to be respectful
            time.sleep(1)
        
        driver.quit()
        print("🔒 Browser closed successfully")
        print(f"✅ Total models processed: {len(all_modalities)}")
        
        return all_modalities
        
    except Exception as error:
        print(f"❌ Error in modalities extraction: {error}")
        try:
            driver.quit()
        except:
            pass
        return {}

def save_modalities(modalities_data: Dict[str, Dict[str, List[str]]]) -> str:
    """Save modalities to stage-3-scrape-modalities.json"""
    filename = 'stage-3-scrape-modalities.json'
    
    # Transform data to include model_id field for each model
    transformed_modalities = {}
    for model_key, modality_info in modalities_data.items():
        transformed_modalities[model_key] = {
            'model_id': model_key,  # Add model_id field with the key value
            'input_modalities': modality_info['input_modalities'],
            'output_modalities': modality_info['output_modalities']
        }
    
    data = {
        'extraction_timestamp': datetime.datetime.now().isoformat(),
        'source_base_url': 'https://console.groq.com/docs/model/',
        'total_models': len(transformed_modalities),
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
    
    return filename

# =============================================================================
# STAGE 4: CREATE UNIFIED LICENSE MAPPINGS
# =============================================================================

def create_fresh_license_mappings() -> Dict[str, Any]:
    """Create fresh license mappings structure"""
    return {
        "license_urls": {
            "MIT": "https://spdx.org/licenses/MIT.html",
            "Apache-2.0": "https://www.apache.org/licenses/LICENSE-2.0",
            "Apache-2": "https://www.apache.org/licenses/LICENSE-2.0"
        },
        "provider_license_mappings": {}
    }

def check_huggingface_license_pattern(model_id: str) -> bool:
    """Check if model follows HF license URL pattern"""
    # Models that follow https://huggingface.co/{model_id}/blob/main/LICENSE pattern
    hf_license_patterns = [
        'openai/gpt-oss-20b',
        'openai/gpt-oss-120b'
    ]
    return model_id in hf_license_patterns

def get_whisper_license_info() -> Dict[str, Dict[str, str]]:
    """Get whisper model license info (hardcoded since special rules file removed)"""
    return {
        "whisper-large-v3": {
            "license_info_text": "info",
            "license_info_url": "https://huggingface.co/openai/whisper-large-v3",
            "license_name": "Apache-2.0",
            "license_url": "https://www.apache.org/licenses/LICENSE-2.0"
        },
        "whisper-large-v3-turbo": {
            "license_info_text": "info",
            "license_info_url": "https://huggingface.co/openai/whisper-large-v3-turbo",
            "license_name": "Apache-2.0",
            "license_url": "https://www.apache.org/licenses/LICENSE-2.0"
        }
    }

def extract_llama_license_info(model_id: str) -> Dict[str, str]:
    """Extract Llama license information based on version patterns"""
    model_lower = model_id.lower()
    
    # Llama Guard patterns
    guard_match = re.search(r'llama[_-]?guard[_-]?(\d+)', model_lower)
    if guard_match:
        guard_version = guard_match.group(1)
        return {
            'license_info_text': '',
            'license_info_url': '',
            'license_name': f'Llama-{guard_version}',
            'license_url': f'https://www.llama.com/llama{guard_version}/license/'
        }
    
    # Regular Llama version patterns
    version_patterns = [
        r'llama[_-]?(\d+\.\d+)',  # Match llama-3.1, llama-3.3, etc.
        r'llama[_-]?(\d+)',       # Match llama-4, etc.
    ]
    
    for pattern in version_patterns:
        match = re.search(pattern, model_lower)
        if match:
            version = match.group(1)
            url_version = version.replace('.', '_')
            return {
                'license_info_text': '',
                'license_info_url': '',
                'license_name': f'Llama-{version}',
                'license_url': f'https://www.llama.com/llama{url_version}/license/'
            }
    
    return {}

def create_unified_license_mappings(production_models: List[Dict[str, Any]]) -> str:
    """Create unified license mappings from all sources"""
    print("=" * 80)
    print("🚀 STAGE 4: UNIFIED LICENSE MAPPINGS CREATOR")
    print("=" * 80)
    print(f"🕒 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load all data sources
    fresh_mappings = create_fresh_license_mappings()
    whisper_overrides = get_whisper_license_info()
    
    print(f"📋 Processing {len(production_models)} production models")
    print("🔄 Creating fresh license mappings (clearing existing)")
    
    # Start with base license URLs
    license_urls = fresh_mappings['license_urls']
    
    # Process each model to determine license source
    model_license_info = {}
    source_stats = {
        'llama': 0,
        'google': 0,
        'mistral': 0,
        'special_rules': 0,
        'kimi': 0,
        'zai': 0,
        'huggingface': 0,
        'unknown': 0
    }
    
    # Get whisper overrides
    special_overrides = whisper_overrides
    
    for model in production_models:
        model_id = model['model_id']
        provider = model['model_provider']
        
        print(f"🔍 Processing: {model_id} ({provider})")
        
        license_info = {}
        source = 'unknown'
        
        # ================================================================================
        # CATEGORY 1: LLAMA MODELS  
        # ================================================================================
        if 'llama' in model_id.lower():
            print(f"   ⎿ ================================================================================")
            print(f"     LLAMA MODELS")
            print(f"     ================================================================================")
            llama_info = extract_llama_license_info(model_id)
            if llama_info:
                license_info = llama_info
                source = 'llama'
                source_stats['llama'] += 1
                print(f"   ✅ Llama license: {license_info['license_name']}")
            else:
                print(f"   ❌ Llama pattern not recognized")
                license_info = {'license_info_text': 'Unknown', 'license_info_url': '', 'license_name': 'Unknown', 'license_url': ''}
                source = 'unknown'
                source_stats['unknown'] += 1
        
        # ================================================================================
        # CATEGORY 2: GOOGLE GEMINI & GEMMA MODELS  
        # ================================================================================
        elif provider.lower() == 'google' and ('gemini' in model_id.lower() or 'gemma' in model_id.lower()):
            if 'gemini' in model_id.lower():
                print(f"   ⎿ ================================================================================")
                print(f"     GOOGLE GEMINI MODELS")
                print(f"     ================================================================================")
                license_info = {
                    'license_info_text': 'Google',
                    'license_info_url': 'https://developers.google.com/terms',
                    'license_name': 'Gemini',
                    'license_url': 'https://ai.google.dev/gemini-api/terms'
                }
            else:  # gemma
                print(f"   ⎿ ================================================================================")
                print(f"     GOOGLE GEMMA MODELS")
                print(f"     ================================================================================")
                license_info = {
                    'license_info_text': '',
                    'license_info_url': '',
                    'license_name': 'Gemma',
                    'license_url': 'https://ai.google.dev/gemma/terms'
                }
            source = 'google'
            source_stats['google'] = source_stats.get('google', 0) + 1
            print(f"   ✅ Google license: {license_info['license_name']}")
        
        # ================================================================================
        # CATEGORY 3: MISTRAL MODELS
        # ================================================================================
        elif provider.lower() == 'mistral ai' or 'mistral' in model_id.lower():
            print(f"   ⎿ ================================================================================")
            print(f"     MISTRAL MODELS")
            print(f"     ================================================================================")
            license_info = {
                'license_info_text': '',
                'license_info_url': 'https://docs.mistral.ai/getting-started/models/models_overview/',
                'license_name': 'Apache-2.0',
                'license_url': 'https://www.apache.org/licenses/LICENSE-2.0'
            }
            source = 'mistral'
            source_stats['mistral'] = source_stats.get('mistral', 0) + 1
            print(f"   ✅ Mistral license: {license_info['license_name']}")
        
        # ================================================================================
        # CATEGORY 4: HUGGING FACE MODELS WITH VALID LICENSE FILES
        # ================================================================================
        elif check_huggingface_license_pattern(model_id):
            print(f"   ⎿ ================================================================================")
            print(f"     HUGGING FACE MODELS")
            print(f"     ================================================================================")
            license_info = {
                'license_info_text': 'info',
                'license_info_url': f'https://huggingface.co/{model_id}/blob/main/LICENSE',
                'license_name': 'Apache-2.0',
                'license_url': 'https://www.apache.org/licenses/LICENSE-2.0'
            }
            source = 'huggingface'
            source_stats['huggingface'] += 1
            print(f"   ✅ Hugging Face: {license_info['license_name']}")
        
        # ================================================================================
        # CATEGORY 5: OTHER MODELS (Kimi, Z.AI, Whisper)
        # ================================================================================
        elif model_id in special_overrides or any(x in model_id.lower() for x in ['whisper', 'kimi', 'z.ai']):
            if model_id in special_overrides:
                print(f"   ⎿ ================================================================================")
                print(f"     WHISPER MODELS")
                print(f"     ================================================================================")
            elif 'kimi' in model_id.lower():
                print(f"   ⎿ ================================================================================")
                print(f"     KIMI MODELS")
                print(f"     ================================================================================")
            elif 'z.ai' in model_id.lower():
                print(f"   ⎿ ================================================================================")
                print(f"     Z.AI MODELS")
                print(f"     ================================================================================")
            
            if model_id in special_overrides:
                license_info = special_overrides[model_id]
                source = 'special_rules'
                source_stats['special_rules'] += 1
                print(f"   ✅ Special rules: {license_info['license_name']}")
            elif 'kimi' in model_id.lower():
                license_info = {
                    'license_info_text': '',
                    'license_info_url': 'https://www.kimi.com/',
                    'license_name': 'Kimi',
                    'license_url': 'https://www.kimi.com/user/agreement/modelUse?version=v2'
                }
                source = 'kimi'
                source_stats['kimi'] = source_stats.get('kimi', 0) + 1
                print(f"   ✅ Kimi license: {license_info['license_name']}")
            elif 'z.ai' in model_id.lower():
                license_info = {
                    'license_info_text': '',
                    'license_info_url': 'https://chat.z.ai/',
                    'license_name': 'Z.AI',
                    'license_url': 'https://chat.z.ai/legal-agreement/terms-of-service'
                }
                source = 'zai'
                source_stats['zai'] = source_stats.get('zai', 0) + 1
                print(f"   ✅ Z.AI license: {license_info['license_name']}")
        
        # ================================================================================
        # CATEGORY 6: UNKNOWN MODELS
        # ================================================================================
        else:
            print(f"   ⎿ ================================================================================")
            print(f"     UNKNOWN MODELS")
            print(f"     ================================================================================")
            license_info = {
                'license_info_text': 'Unknown',
                'license_info_url': '',
                'license_name': 'Unknown',
                'license_url': ''
            }
            source = 'unknown'
            source_stats['unknown'] += 1
            print(f"   ❌ Unknown license")
        
        model_license_info[model_id] = {
            'license_info': license_info,
            'source': source,
            'provider': provider
        }
        
        # Add license name to license_urls if new
        if license_info.get('license_name') and license_info.get('license_url'):
            license_name = license_info['license_name']
            license_url = license_info['license_url']
            if license_name not in license_urls:
                license_urls[license_name] = license_url
    
    # Build final provider mappings structure
    final_provider_mappings = {}
    
    # Group models by provider and organize license info
    provider_models = {}
    for model_id, info in model_license_info.items():
        provider = info['provider']
        if provider not in provider_models:
            provider_models[provider] = []
        provider_models[provider].append((model_id, info['license_info']))
    
    # Create provider mappings - ALWAYS use model-specific mappings for individual models
    for provider, models in provider_models.items():
        provider_mapping = {}
        for model_id, license_info in models:
            # Use model name as key (without provider prefix)
            model_key = model_id.split('/')[-1] if '/' in model_id else model_id
            provider_mapping[model_key] = license_info
        final_provider_mappings[provider] = provider_mapping
    
    # Create final structure
    final_mappings = {
        "license_urls": license_urls,
        "provider_license_mappings": final_provider_mappings
    }
    
    # Save to file
    filename = 'stage-4-license-mappings.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(final_mappings, f, indent=2)
    
    print(f"\n" + "=" * 80)
    print("📄 STAGE 4 LICENSE MAPPINGS COMPLETED")
    print("=" * 80)
    print(f"✅ Updated: {filename}")
    
    # Print statistics
    print(f"\nSource Statistics:")
    for source, count in source_stats.items():
        percentage = (count / len(production_models) * 100) if len(production_models) > 0 else 0
        print(f"  {source.title()}: {count} models ({percentage:.1f}%)")
    
    print(f"\nLicense Coverage:")
    known_licenses = len(production_models) - source_stats['unknown']
    coverage = (known_licenses / len(production_models) * 100) if len(production_models) > 0 else 0
    print(f"  Known licenses: {known_licenses}/{len(production_models)} ({coverage:.1f}%)")
    print(f"  Unknown licenses: {source_stats['unknown']}/{len(production_models)} ({(100-coverage):.1f}%)")
    
    print(f"🕒 Completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return filename

# =============================================================================
# STAGE 5: POPULATE NORMALIZED DATA
# =============================================================================

def load_json_file(filename):
    """Load JSON file and return data."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_special_model_rules():
    """Load special model name conversion rules"""
    try:
        with open('04_special_model_rules.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('special_name_conversions', {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def clean_model_name(model_id, standardization_rules):
    """Clean and standardize model name with special rules support."""
    # Load special model rules
    special_rules = load_special_model_rules()
    
    # Extract base name (remove provider prefix if exists)
    base_name = model_id.split('/')[-1] if '/' in model_id else model_id
    
    # Check for special conversion rules first
    if base_name in special_rules:
        return special_rules[base_name]
    
    # Apply standard processing
    name = model_id
    
    # Remove patterns
    for pattern in standardization_rules.get('remove_patterns', []):
        name = name.replace(pattern, '')
    
    # Replace patterns
    for old, new in standardization_rules.get('replace_patterns', {}).items():
        name = name.replace(old, new)
    
    # Extract human readable name (remove provider prefix if exists)
    if '/' in name:
        name = name.split('/')[-1]
    
    # Capitalize first letter of each word
    name = ' '.join(word.capitalize() for word in name.replace('-', ' ').split())
    
    return name

def get_provider_info(model_provider, provider_mappings):
    """Get provider country and official URL."""
    provider_data = provider_mappings.get('provider_mappings', {}).get(model_provider.lower(), [model_provider, "Unknown"])
    country = provider_data[1] if len(provider_data) > 1 else "Unknown"
    
    official_urls = provider_mappings.get('official_urls', {})
    official_url = official_urls.get(model_provider, "")
    
    return country, official_url

def load_modality_standardization():
    """Load modality standardization mappings"""
    try:
        with open('08_modality_standardization.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('modality_mappings', {}), data.get('ordering_priority', {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}, {}


def load_timestamp_patterns():
    """Load timestamp formatting patterns"""
    try:
        with open('09_timestamp_patterns.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def standardize_modalities(modalities_list, modality_mappings):
    """Standardize modality names using mappings"""
    if not modalities_list:
        return []
    
    standardized = []
    for modality in modalities_list:
        standardized_mod = modality_mappings.get(modality.lower(), modality)
        if standardized_mod not in standardized:
            standardized.append(standardized_mod)
    
    return standardized


def sort_modalities(modalities_list, ordering_priority):
    """Sort modalities based on priority order"""
    if not modalities_list or not ordering_priority:
        return modalities_list
    
    return sorted(modalities_list, key=lambda x: ordering_priority.get(x, 999))


def format_timestamp(unix_timestamp, timestamp_patterns):
    """Format timestamp using standardized patterns"""
    if not timestamp_patterns:
        # Fallback to default formatting
        if unix_timestamp:
            return datetime.datetime.fromtimestamp(int(unix_timestamp)).isoformat() + '+00:00'
        else:
            return datetime.datetime.now().isoformat() + '+00:00'
    
    try:
        if unix_timestamp:
            # Use unix conversion template
            return datetime.datetime.fromtimestamp(int(unix_timestamp)).isoformat() + '+00:00'
        else:
            # Use default fallback template
            return datetime.datetime.now().isoformat() + '+00:00'
    except (ValueError, TypeError):
        # Error handling - use fallback
        return datetime.datetime.now().isoformat() + '+00:00'


def get_modalities(model_id, modalities_data):
    """Get input/output modalities for a model with standardization."""
    model_data = modalities_data.get('modalities', {}).get(model_id, {})
    
    # Load standardization mappings
    modality_mappings, ordering_priority = load_modality_standardization()
    
    # Get raw modalities
    input_modalities = model_data.get('input_modalities', [])
    output_modalities = model_data.get('output_modalities', [])
    
    # Standardize and sort modalities
    input_standardized = standardize_modalities(input_modalities, modality_mappings)
    output_standardized = standardize_modalities(output_modalities, modality_mappings)
    
    input_sorted = sort_modalities(input_standardized, ordering_priority)
    output_sorted = sort_modalities(output_standardized, ordering_priority)
    
    # Join with commas and spaces for proper formatting
    input_mods = ', '.join(input_sorted)
    output_mods = ', '.join(output_sorted)
    
    return input_mods, output_mods

def get_license_info(model_id, model_provider, license_mappings):
    """Get license information for a specific model."""
    # Get provider's license mappings
    provider_licenses = license_mappings.get('provider_license_mappings', {}).get(model_provider, {})
    
    # Extract model key (remove provider prefix if exists)
    model_key = model_id.split('/')[-1] if '/' in model_id else model_id
    
    # Get model-specific license info
    model_license_info = provider_licenses.get(model_key, {})
    
    license_info_text = model_license_info.get('license_info_text', '')
    license_info_url = model_license_info.get('license_info_url', '')
    license_name = model_license_info.get('license_name', '')
    license_url = model_license_info.get('license_url', '')
    
    # If no license_url in model info, try to get from global license_urls mapping
    if not license_url and license_name:
        license_url = license_mappings.get('license_urls', {}).get(license_name, '')
    
    return license_info_text, license_info_url, license_name, license_url

def format_rate_limits(model_id, rate_limits_data):
    """Format rate limits data."""
    model_limits = rate_limits_data.get('rate_limits', {}).get(model_id, {})
    if not model_limits:
        return ""
    
    # Format as "RPM: X, TPM: Y, RPD: Z, TPD: W"
    rpm = model_limits.get('RPM', '')
    tpm = model_limits.get('TPM', '')
    rpd = model_limits.get('RPD', '')
    tpd = model_limits.get('TPD', '')
    ash = model_limits.get('ASH', '')
    asd = model_limits.get('ASD', '')
    
    parts = []
    if rpm and rpm != '-': parts.append(f"RPM: {rpm}")
    if tpm and tpm != '-': parts.append(f"TPM: {tpm}")
    if rpd and rpd != '-': parts.append(f"RPD: {rpd}")
    if tpd and tpd != '-': parts.append(f"TPD: {tpd}")
    if ash and ash != '-': parts.append(f"ASH: {ash}")
    if asd and asd != '-': parts.append(f"ASD: {asd}")
    
    return ', '.join(parts)

def generate_normalization_report(production_models, normalized_data, report_filename=None):
    """Generate detailed normalization report like OpenRouter pipeline"""
    if not report_filename:
        report_filename = 'groq_normalization_report.txt'
    
    total_extracted = len(production_models['production_models'])
    total_normalized = len(normalized_data)
    success_rate = (total_normalized / total_extracted * 100) if total_extracted > 0 else 0
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("GROQ PIPELINE NORMALIZATION REPORT\n")
        f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Summary
        f.write("SUMMARY:\n")
        f.write(f"  Total models extracted: {total_extracted}\n")
        f.write(f"  Models filtered out: 0\n")  # Groq only extracts production models
        f.write(f"  Models normalized: {total_normalized}\n")
        f.write(f"  Models unchanged: 0\n")
        f.write(f"  Success rate: {success_rate:.1f}%\n\n")
        
        # Models normalized details
        f.write(f"MODELS NORMALIZED: {total_normalized}\n")
        f.write("-" * 40 + "\n")
        
        for idx, record in enumerate(normalized_data, 1):
            provider = record['model_provider'].upper()
            human_name = record['human_readable_name']
            
            # Find original model data by matching record ID with list index
            original_model = None
            original_model_id = ""
            if idx <= len(production_models['production_models']):
                original_model = production_models['production_models'][idx - 1]  # idx is 1-based, list is 0-based
                original_model_id = original_model['model_id']
            
            f.write(f"   {idx}. {provider} - {human_name}\n")
            if original_model_id and original_model_id != human_name:
                f.write(f"      Model Name: {original_model_id} -> {human_name}\n")
            
            # Input/Output modalities
            if record['input_modalities']:
                f.write(f"      Input Modalities: {record['input_modalities']}\n")
            if record['output_modalities']:
                f.write(f"      Output Modalities: {record['output_modalities']}\n")
            
            # License info
            if record['license_name']:
                f.write(f"      License: {record['license_info_text']} -> {record['license_name']}\n")
            
            # Rate limits summary
            if record['rate_limits']:
                f.write(f"      Rate Limits: {record['rate_limits'][:50]}{'...' if len(record['rate_limits']) > 50 else ''}\n")
            
            f.write("\n")
        
        # Provider summary
        f.write("PROVIDER SUMMARY:\n")
        f.write("-" * 40 + "\n")
        
        provider_counts = {}
        for record in normalized_data:
            provider = record['model_provider']
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        for provider, count in sorted(provider_counts.items()):
            f.write(f"  {provider}: {count} models\n")
        
        f.write(f"\nTotal providers: {len(provider_counts)}\n")
    
    print(f"📄 Normalization report generated: {report_filename}")
    return report_filename

def populate_normalized_data():
    """Populate normalized CSV from all extracted data"""
    print("\n" + "=" * 80)
    print("🚀 STAGE 5: DATA NORMALIZATION")
    print("=" * 80)
    print(f"🕒 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load all data files
    print("Loading data files...")
    production_models = load_json_file('stage-1-scrape-production-models.json')
    rate_limits = load_json_file('stage-2-scrape-rate-limits.json')
    modalities = load_json_file('stage-3-scrape-modalities.json')
    provider_mappings = load_json_file('01_provider_mappings.json')
    license_mappings = load_json_file('stage-4-license-mappings.json')
    database_schema = load_json_file('03_database_schema.json')
    
    # Get standardization rules
    standardization = provider_mappings.get('model_name_standardization', {})
    
    # Prepare CSV output
    fieldnames = [
        'id', 'inference_provider', 'model_provider', 'human_readable_name',
        'model_provider_country', 'official_url', 'input_modalities', 'output_modalities',
        'license_info_text', 'license_info_url', 'license_name', 'license_url',
        'rate_limits', 'provider_api_access', 'created_at', 'updated_at'
    ]
    
    # Load timestamp patterns
    timestamp_patterns = load_timestamp_patterns()
    
    normalized_data = []
    current_timestamp = datetime.datetime.now().isoformat() + '+00:00'
    
    print(f"Processing {len(production_models['production_models'])} models...")
    
    # Process each production model
    for idx, model in enumerate(production_models['production_models'], 1):
        model_id = model['model_id']
        model_provider = model['model_provider']
        
        print(f"Processing {model_id}...")
        
        # Get provider info
        country, official_url = get_provider_info(model_provider, provider_mappings)
        
        # Get modalities
        input_mods, output_mods = get_modalities(model_id, modalities)
        
        # Get license info
        license_text, license_url_info, license_name, license_url = get_license_info(model_id, model_provider, license_mappings)
        
        # Get rate limits
        rate_limits_str = format_rate_limits(model_id, rate_limits)
        
        # Create normalized record
        record = {
            'id': idx,
            'inference_provider': 'Groq',
            'model_provider': model_provider,
            'human_readable_name': clean_model_name(model_id, standardization),
            'model_provider_country': country,
            'official_url': official_url,
            'input_modalities': input_mods,
            'output_modalities': output_mods,
            'license_info_text': license_text,
            'license_info_url': license_url_info,
            'license_name': license_name,
            'license_url': license_url,
            'rate_limits': rate_limits_str,
            'provider_api_access': 'https://console.groq.com/keys',
            'created_at': format_timestamp(model.get('created'), timestamp_patterns),
            'updated_at': current_timestamp
        }
        
        normalized_data.append(record)
    
    # Write to CSV
    print("Writing to stage-5-data-normalization.csv...")
    with open('stage-5-data-normalization.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_data)
    
    print(f"✅ Successfully populated {len(normalized_data)} records to stage-5-data-normalization.csv")
    
    # Generate normalization report
    report_file = generate_normalization_report(production_models, normalized_data)
    
    # Print summary
    print("\nSummary:")
    providers = set(record['model_provider'] for record in normalized_data)
    print(f"- Total models: {len(normalized_data)}")
    print(f"- Providers: {', '.join(sorted(providers))}")
    print(f"- Models with modalities: {sum(1 for r in normalized_data if r['input_modalities'])}")
    print(f"- Models with rate limits: {sum(1 for r in normalized_data if r['rate_limits'])}")
    print(f"- Normalization report: {report_file}")
    
    return normalized_data

# =============================================================================
# LICENSE EXTRACTION SYSTEM INTEGRATION
# =============================================================================

def run_meta_license_extraction() -> bool:
    """Run Meta license extraction script"""
    try:
        import subprocess
        result = subprocess.run(['python3', 'A_extract_meta_licenses.py'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("   ✅ Meta license extraction completed")
            return True
        else:
            print(f"   ⚠️ Meta license extraction issues: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Meta license extraction failed: {e}")
        return False


def run_hf_scraped_license_extraction() -> bool:
    """Run HF-scraped & Google license extraction script"""
    try:
        import subprocess
        result = subprocess.run(['python3', 'B_extract_opensource_licenses.py'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("   ✅ HF-scraped & Google license extraction completed")
            return True
        else:
            print(f"   ⚠️ HF-scraped license extraction issues: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ HF-scraped license extraction failed: {e}")
        return False


def run_license_consolidation() -> bool:
    """Run license consolidation script"""
    try:
        import subprocess
        result = subprocess.run(['python3', 'F_consolidate_all_licenses.py'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("   ✅ License consolidation completed")
            return True
        else:
            print(f"   ❌ License consolidation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ License consolidation failed: {e}")
        return False


# =============================================================================
# MAIN PIPELINE EXECUTION
# =============================================================================

def main():
    """Main pipeline execution function"""
    print("=" * 80)
    print("🚀 GROQ COMPLETE PIPELINE - END-TO-END DATA EXTRACTION & NORMALIZATION")
    print("=" * 80)
    print(f"🕒 Pipeline started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📋 Stages: Production Models → Rate Limits → Modalities → License Mappings → Normalization")
    
    try:
        # Stage 1: Extract production models
        production_models = scrape_production_models()
        if not production_models:
            print("❌ Stage 1 failed: No production models extracted")
            return False
        save_production_models(production_models)
        
        # Stage 2: Extract rate limits
        rate_limits = scrape_rate_limits()
        if not rate_limits:
            print("❌ Stage 2 failed: No rate limits extracted")
            return False
        save_rate_limits(rate_limits)
        
        # Stage 3: Extract modalities
        modalities_data = scrape_all_modalities()
        if not modalities_data:
            print("❌ Stage 3 failed: No modalities data extracted")
            return False
        save_modalities(modalities_data)
        
        # Stage 4: Extract license information using new 3-step system
        print("\n🚀 STAGE 4: LICENSE EXTRACTION (3-STEP SYSTEM)")
        
        # Stage 4A: Extract Meta licenses
        print("🔄 Step 4A: Extracting Meta/Llama licenses...")
        meta_success = run_meta_license_extraction()
        if not meta_success:
            print("⚠️ Stage 4A warning: Meta license extraction had issues")
        
        # Stage 4B: Extract HF-scraped & Google licenses  
        print("🔄 Step 4B: Extracting HF-scraped & Google licenses...")
        hf_success = run_hf_scraped_license_extraction()
        if not hf_success:
            print("⚠️ Stage 4B warning: HF-scraped license extraction had issues")
        
        # Stage 4C: Consolidate all licenses
        print("🔄 Step 4C: Consolidating all license information...")
        consolidation_success = run_license_consolidation()
        if not consolidation_success:
            print("❌ Stage 4 failed: License consolidation failed")
            return False
        
        print("✅ Stage 4 completed: All license information consolidated")
        
        # Stage 5: Populate normalized data
        populate_normalized_data()
        
        print("\n" + "=" * 80)
        print("🎉 GROQ PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("📄 Output Files:")
        print("   • stage-1-scrape-production-models.json - Production models data")
        print("   • stage-2-scrape-rate-limits.json - Rate limits data") 
        print("   • stage-3-scrape-modalities.json - Modalities data")
        print("   • stage-4-license-mappings.json - License mappings data")
        print("   • stage-5-data-normalization.csv - Normalized database-ready data")
        print("   • groq_normalization_report.txt - Detailed normalization report")
        print(f"🕒 Pipeline completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as error:
        print(f"❌ Pipeline failed: {error}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)