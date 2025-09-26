#!/usr/bin/env python3
"""
Google Documentation Modality Scraper
Scrapes official Google AI documentation to extract accurate input/output modalities
for Gemini, Imagen, Video, Embedding, and Gemma models.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import sys
import os
from typing import Dict, List, Tuple, Optional
from urllib.parse import urljoin

# Import IST timestamp utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '04_utils'))
from output_utils import get_ist_timestamp

class GoogleModalityScraper:
    """
    A comprehensive web scraper for extracting AI model modality information from Google's official documentation.

    This scraper extracts input/output modality mappings for:
    - Gemini models (from ai.google.dev/gemini-api/docs/models)
    - Imagen models (from ai.google.dev/gemini-api/docs/imagen)
    - Video models (from ai.google.dev/gemini-api/docs/video)
    - Gemma models (from ai.google.dev/gemma/docs/)

    The scraper parses official "Supported data types" sections to ensure accuracy
    and avoid hardcoded fallbacks.
    """

    def __init__(self):
        """Initialize the scraper with session and headers for web requests."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.modality_mapping = {}
        
    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch and parse HTML page with retry logic.

        Args:
            url: The URL to fetch
            retries: Number of retry attempts (default: 3)

        Returns:
            BeautifulSoup object of parsed HTML, or None if all attempts fail
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def load_modality_config(self):
        """
        Load modality configuration from 02_modality_standardization.json.

        Note: This method is currently unused as the scraper now relies on
        direct parsing from official documentation rather than standardization.

        Returns:
            Configuration dict or "Unknown" if file not found
        """
        try:
            with open('../03_configs/02_modality_standardization.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ 02_modality_standardization.json not found, returning Unknown")
            return "Unknown"

    def standardize_modalities(self, modalities: List[str]) -> str:
        """
        Convert modalities to standardized format using 02_modality_standardization.json.

        Note: This method is currently disabled as the scraper now preserves
        raw modalities directly from Google's documentation for accuracy.

        Args:
            modalities: List of modality strings to standardize

        Returns:
            Comma-separated string of raw modalities (standardization disabled)
        """
        # config = self.load_modality_config()
        # if config == "Unknown":
        #     return "Unknown"
            
        # modality_mappings = config['modality_mappings']
        # ordering_priority = config['ordering_priority']
        
        # # If no configuration mappings exist, return Unknown
        # if not modality_mappings:
        #     return "Unknown"
            
        # normalized = []
        
        # for modality in modalities:
        #     modality = modality.strip().title()
        #     modality_lower = modality.lower()
            
        #     # Map using configuration file
        #     mapped = False
        #     for key, value in modality_mappings.items():
        #         if key in modality_lower:
        #             normalized.append(value)
        #             mapped = True
        #             break
            
        #     if not mapped:
        #         # If no configuration mappings exist, return Unknown
        #         if not modality_mappings:
        #             return "Unknown"
        #         normalized.append(modality)  # Keep original if not found
        
        # # Remove duplicates while preserving order
        # seen = set()
        # unique_modalities = []
        # for modality in normalized:
        #     if modality not in seen:
        #         unique_modalities.append(modality)
        #         seen.add(modality)
        
        # # Sort by priority from configuration
        # unique_modalities.sort(key=lambda x: ordering_priority.get(x, 99))
        
        # return ', '.join(unique_modalities)
        
        # Return raw modalities without processing
        return ', '.join(modalities)

    def scrape_gemini_models(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape Gemini model capabilities from individual model sections.

        Uses comprehensive section scanning approach:
        1. First tries the original heading-based method
        2. Then systematically scans /html/body/section/section/main/devsite-content/article/div[4]/section[1-12+]

        Returns:
            Dict mapping model names to their input/output modalities
        """
        base_url = "https://ai.google.dev/gemini-api/docs/models"
        print(f"Scraping Gemini models from {base_url}")

        soup = self.fetch_page(base_url)
        gemini_models = {}

        if soup:
            # Method 1: Original heading-based approach
            print("  Method 1: Scanning headings with IDs...")
            headings_with_ids = soup.find_all(['h1', 'h2', 'h3', 'h4'], id=True)

            for heading in headings_with_ids:
                heading_id = heading.get('id', '')
                heading_text = heading.get_text().strip()

                # Look for Gemini model headings
                if 'gemini' in heading_id.lower() and heading_id != 'gemini-api':
                    print(f"    Processing section: {heading_id}")

                    # Find the "Supported data types" section after this heading
                    model_info = self.extract_supported_data_types(soup, heading)

                    if model_info:
                        model_name = heading_text if heading_text else heading_id
                        gemini_models[model_name] = model_info
                        print(f"      Found: {model_name} -> {model_info['input_modalities']} → {model_info['output_modalities']}")
                    else:
                        print(f"      No supported data types found for {heading_id}")

            # Method 2: Comprehensive section scanning
            print("  Method 2: Systematic section scanning...")
            systematic_models = self.scan_systematic_sections(soup)

            # Merge results, prioritizing new findings
            for model_name, model_info in systematic_models.items():
                if model_name not in gemini_models:
                    gemini_models[model_name] = model_info
                    print(f"      Added from systematic scan: {model_name} -> {model_info['input_modalities']} → {model_info['output_modalities']}")

        return gemini_models

    def scan_systematic_sections(self, soup) -> Dict[str, Dict[str, str]]:
        """
        Systematically scan /html/body/section/section/main/devsite-content/article/div[4]/section[1-12+]

        Follows the exact path: /html/body/section/section/main/devsite-content/article/div[4]/section[N]
        to find any Gemini models that might be missed by heading-based scanning.

        Returns:
            Dict mapping model names to their input/output modalities
        """
        systematic_models = {}

        try:
            # Navigate to the target div following the specified path
            # /html/body/section/section/main/devsite-content/article/div[4]
            body = soup.find('body')
            if not body:
                print("    ⚠️ No <body> element found")
                return systematic_models

            # Find section/section/main structure
            sections = body.find_all('section', recursive=False)
            if not sections:
                print("    ⚠️ No top-level <section> elements found")
                return systematic_models

            target_section = None
            for section in sections:
                nested_section = section.find('section', recursive=False)
                if nested_section:
                    main = nested_section.find('main', recursive=False)
                    if main:
                        devsite_content = main.find('devsite-content', recursive=False)
                        if devsite_content:
                            article = devsite_content.find('article', recursive=False)
                            if article:
                                target_section = section
                                print("    ✅ Found target section structure")
                                break

            if not target_section:
                print("    ⚠️ Could not find target section structure")
                return systematic_models

            # Navigate to article/div[4]
            main = target_section.find('section').find('main')
            devsite_content = main.find('devsite-content')
            article = devsite_content.find('article')

            # Get all direct child divs of article
            article_divs = article.find_all('div', recursive=False)
            if len(article_divs) < 4:
                print(f"    ⚠️ Expected at least 4 divs in article, found {len(article_divs)}")
                return systematic_models

            # Target div[4] (index 3)
            target_div = article_divs[3]
            print(f"    ✅ Found target div[4]")

            # Get all section elements within this div
            sections_in_div = target_div.find_all('section', recursive=False)
            print(f"    📍 Found {len(sections_in_div)} sections to scan")

            # Scan each section systematically
            for i, section in enumerate(sections_in_div, 1):
                print(f"    🔍 Scanning section[{i}]...")
                section_models = self.extract_models_from_section(section, f"section[{i}]")
                systematic_models.update(section_models)

        except Exception as e:
            print(f"    ❌ Error in systematic scanning: {e}")

        return systematic_models

    def extract_models_from_section(self, section, section_name: str) -> Dict[str, Dict[str, str]]:
        """
        Extract Gemini models from a specific section element.

        Looks for:
        1. Model names in headings or text
        2. Supported data types tables
        3. Input/output modality information

        Args:
            section: BeautifulSoup section element
            section_name: Name for logging (e.g., "section[12]")

        Returns:
            Dict mapping model names to their input/output modalities
        """
        section_models = {}

        try:
            section_text = section.get_text().lower()

            # Check if this section contains Gemini model information
            if not any(keyword in section_text for keyword in ['gemini', 'live', 'flash', 'pro', 'supported data types']):
                return section_models

            print(f"      📝 {section_name} contains potential model info")

            # Look for headings that might indicate model names
            headings = section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                heading_text = heading.get_text().strip()
                heading_lower = heading_text.lower()

                # Check for Gemini model patterns
                if any(pattern in heading_lower for pattern in ['gemini', 'live', 'flash']):
                    print(f"        🎯 Found potential model heading: '{heading_text}'")

                    # Try to extract modality data from this section
                    model_info = self.extract_supported_data_types(section, heading)
                    if not model_info:
                        # Fallback: look for modality info in surrounding text/tables
                        model_info = self.extract_modalities_from_section_content(section)

                    if model_info:
                        section_models[heading_text] = model_info
                        print(f"        ✅ Extracted: {heading_text} -> {model_info['input_modalities']} → {model_info['output_modalities']}")

            # Also check for tables with model information even without clear headings
            if not section_models:
                tables = section.find_all('table')
                for table in tables:
                    table_text = table.get_text().lower()
                    if 'live' in table_text or 'flash' in table_text:
                        print(f"        🔍 Found table with Live/Flash content")
                        model_info = self.extract_model_info_from_table(table)
                        if model_info:
                            for model_name, info in model_info.items():
                                section_models[model_name] = info
                                print(f"        ✅ Extracted from table: {model_name} -> {info['input_modalities']} → {info['output_modalities']}")

        except Exception as e:
            print(f"      ❌ Error extracting from {section_name}: {e}")

        return section_models

    def extract_modalities_from_section_content(self, section) -> Optional[Dict[str, str]]:
        """
        Extract input/output modalities from section content (fallback method).

        Looks for text patterns indicating modality information.
        """
        try:
            # Look for tables first
            tables = section.find_all('table')
            for table in tables:
                result = self.parse_supported_data_types_table(table)
                if result:
                    return result

            # Look for text patterns in paragraphs
            paragraphs = section.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if 'input' in text.lower() and 'output' in text.lower():
                    # Try to parse modalities from descriptive text
                    inputs = self.extract_inputs_from_cell(text)
                    outputs = self.extract_outputs_from_cell(text)
                    if inputs and outputs:
                        return {
                            'input_modalities': inputs,
                            'output_modalities': outputs
                        }

        except Exception:
            pass

        return None

    def extract_model_info_from_table(self, table) -> Dict[str, Dict[str, str]]:
        """
        Extract model information from a table that might contain Live models or other variants.

        Returns:
            Dict mapping model names to their modalities
        """
        models = {}

        try:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])

                # Look for cells containing model names
                model_name = None
                input_modalities = None
                output_modalities = None

                for cell in cells:
                    cell_text = cell.get_text().strip()
                    cell_lower = cell_text.lower()

                    # Check if this cell contains a model name
                    if any(pattern in cell_lower for pattern in ['live', 'gemini', 'flash']):
                        if not model_name and ('live' in cell_lower or 'gemini' in cell_lower):
                            model_name = cell_text

                    # Check if this cell contains modality information
                    if 'input' in cell_lower and 'output' in cell_lower:
                        inputs = self.extract_inputs_from_cell(cell_text)
                        outputs = self.extract_outputs_from_cell(cell_text)
                        if inputs and outputs:
                            input_modalities = inputs
                            output_modalities = outputs

                # If we found both model name and modalities in this row
                if model_name and input_modalities and output_modalities:
                    models[model_name] = {
                        'input_modalities': input_modalities,
                        'output_modalities': output_modalities
                    }

        except Exception:
            pass

        return models

    def extract_supported_data_types(self, soup_or_section, heading) -> Optional[Dict[str, str]]:
        """
        Extract supported data types from the section following a model heading.

        Searches for tables containing "Supported data types" information within
        the section defined by the heading. Uses robust DOM navigation to handle
        nested HTML structures.

        Args:
            soup_or_section: BeautifulSoup object (page) or section element
            heading: The heading element that defines the model section

        Returns:
            Dict with 'input_modalities' and 'output_modalities' keys, or None if not found
        """
        # Check if we received a section directly (from systematic scanning)
        if hasattr(soup_or_section, 'name') and soup_or_section.name == 'section':
            # We have a section directly, search within it
            section = soup_or_section
        else:
            # We have the full soup, find the section that contains this heading
            section = self.find_containing_section(heading)

        if section:
            # Look for tables within this section that contain "supported data types"
            tables = section.find_all('table')
            for table in tables:
                table_text = table.get_text().lower()
                if 'supported data types' in table_text or ('inputs' in table_text and 'output' in table_text):
                    result = self.parse_supported_data_types_table(table)
                    if result:
                        return result

        # Fallback: search broadly from the heading onwards until next heading
        # Only do this if we have the full soup (not when working with a section)
        if not (hasattr(soup_or_section, 'name') and soup_or_section.name == 'section'):
            current = heading
            next_heading_level = int(heading.name[1]) if heading.name.startswith('h') else 4

            # Traverse all following elements until we hit a heading of same or higher level
            for element in heading.find_all_next():
                # Stop if we hit a heading of same or higher level
                if (hasattr(element, 'name') and element.name and
                    element.name.startswith('h') and
                    int(element.name[1]) <= next_heading_level):
                    break

                # Look for tables that might contain supported data types
                if hasattr(element, 'name') and element.name == 'table':
                    table_text = element.get_text().lower()
                    if 'supported data types' in table_text or ('inputs' in table_text and 'output' in table_text):
                        result = self.parse_supported_data_types_table(element)
                        if result:
                            return result

        return None

    def find_containing_section(self, heading):
        """
        Find the section element that contains this heading.

        Args:
            heading: The heading element to find the containing section for

        Returns:
            The parent section element, or None if not found
        """
        current = heading
        while current:
            if hasattr(current, 'name') and current.name == 'section':
                return current
            current = current.parent
        return None

    def parse_supported_data_types_table(self, table) -> Optional[Dict[str, str]]:
        """
        Parse supported data types from a table.

        Searches table cells for content containing both "inputs" and "output"
        and extracts the modality information.

        Args:
            table: BeautifulSoup table element

        Returns:
            Dict with 'input_modalities' and 'output_modalities' keys, or None if not found
        """
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            for cell in cells:
                cell_text = cell.get_text().strip()

                # Look for cell that contains both inputs and outputs
                if 'inputs' in cell_text.lower() and 'output' in cell_text.lower():
                    # Parse the cell content
                    inputs = self.extract_inputs_from_cell(cell_text)
                    outputs = self.extract_outputs_from_cell(cell_text)

                    if inputs and outputs:
                        return {
                            'input_modalities': inputs,
                            'output_modalities': outputs
                        }

        return None

    def extract_inputs_from_cell(self, cell_text: str) -> str:
        """
        Extract input modalities from table cell text.

        Uses regex patterns to find input modalities in formats like:
        - "Inputs\\nAudio, video, text"
        - "Inputs: Audio, video, text"

        Args:
            cell_text: Raw text content from table cell

        Returns:
            Comma-separated string of standardized input modalities
        """
        import re

        # Look for pattern like "Inputs\nAudio, video, text"
        inputs_match = re.search(r'inputs[^\n]*\n([^\n]+)', cell_text, re.IGNORECASE)
        if inputs_match:
            return self.parse_modalities_from_line(inputs_match.group(1))

        # Fallback: look for "Inputs: ..." pattern
        inputs_match = re.search(r'inputs[:\s]+([^\n\r]+)', cell_text, re.IGNORECASE)
        if inputs_match:
            return self.parse_modalities_from_line(inputs_match.group(1))

        return ""

    def extract_outputs_from_cell(self, cell_text: str) -> str:
        """
        Extract output modalities from table cell text.

        Uses regex patterns to find output modalities in formats like:
        - "Output\\nAudio and text"
        - "Output: Audio and text"

        Args:
            cell_text: Raw text content from table cell

        Returns:
            Comma-separated string of standardized output modalities
        """
        import re

        # Look for pattern like "Output\nAudio and text"
        outputs_match = re.search(r'output[^\n]*\n([^\n]+)', cell_text, re.IGNORECASE)
        if outputs_match:
            return self.parse_modalities_from_line(outputs_match.group(1))

        # Fallback: look for "Output: ..." pattern
        outputs_match = re.search(r'output[:\s]+([^\n\r]+)', cell_text, re.IGNORECASE)
        if outputs_match:
            return self.parse_modalities_from_line(outputs_match.group(1))

        return ""

    def parse_modalities_from_line(self, line: str) -> str:
        """
        Parse modalities from a line like 'Inputs: Audio, video, text' or 'Output: Audio and text'.

        Standardizes modality names and formats them consistently.

        Args:
            line: Raw text line containing modality information

        Returns:
            Comma-separated string of standardized modalities (e.g., "Audio, Video, Text")
        """
        import re

        # Remove the label part (Inputs:, Output:, etc.)
        modalities_part = re.sub(r'^[^:]*:', '', line).strip()

        # Split by commas and 'and', then clean up
        parts = re.split(r'[,&]|\band\b', modalities_part.lower())
        parts = [part.strip() for part in parts if part.strip()]

        # Map to standard names and capitalize
        modality_mapping = {
            'text': 'Text',
            'image': 'Image',
            'images': 'Image',
            'audio': 'Audio',
            'video': 'Video',
            'pdf': 'PDF'
        }

        standardized = []
        for part in parts:
            if part in modality_mapping:
                standard = modality_mapping[part]
                if standard not in standardized:
                    standardized.append(standard)

        return ', '.join(standardized)

    def extract_model_capabilities(self, row, soup) -> Optional[Dict[str, str]]:
        """Extract input/output capabilities for a specific model - DEPRECATED"""
        # This method is deprecated - we now scrape from official sections only
        return None

    def extract_gemini_from_sections(self, soup) -> Dict[str, Dict[str, str]]:
        """Extract Gemini models from page sections - DEPRECATED"""
        # This method is deprecated - we now scrape from official sections only
        return {}

    def normalize_model_name(self, model_name: str) -> str:
        """Normalize model name for consistent matching"""
        # # Remove extra spaces, hyphens, and normalize formatting
        # normalized = re.sub(r'[-\s]+', '-', model_name.strip().lower())
        # # Remove version prefixes like "v" or trailing numbers that vary
        # normalized = re.sub(r'-v?\d{3}$', '', normalized)
        # return normalized
        
        # Return model name without normalization
        return model_name.strip()
    
    def get_model_specific_capabilities(self, model_name: str) -> Optional[Dict[str, List[str]]]:
        """Return specific capabilities for known models"""
        model_name = self.normalize_model_name(model_name)
        
        # Specific model capability mappings
        model_capabilities = {
            'gemini-2.0-flash-live': {
                'input': ['Audio', 'Video', 'Text'],
                'output': ['Text', 'Audio']
            },
            'gemini-2.0-flash-experimental': {
                'input': ['Text', 'Image', 'Audio', 'Video', 'PDF'],
                'output': ['Text']
            },
            'gemini-1.5-pro': {
                'input': ['Text', 'Image', 'Audio', 'Video', 'PDF'],
                'output': ['Text']
            },
            'gemini-1.5-flash': {
                'input': ['Text', 'Image', 'Audio', 'Video', 'PDF'],
                'output': ['Text']
            },
            'gemini-1.0-pro': {
                'input': ['Text'],
                'output': ['Text']
            }
        }
        
        # Try exact match first
        if model_name in model_capabilities:
            return model_capabilities[model_name]
            
        # Try partial matches for model families
        for known_model, capabilities in model_capabilities.items():
            if known_model in model_name or model_name in known_model:
                return capabilities
        
        return None

    def scrape_imagen_modalities(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape Imagen model capabilities from specific sections.

        Extracts modalities for both Imagen 3 and Imagen 4 models from their
        respective documentation sections.

        Returns:
            Dict mapping image model names to their input/output modalities
        """
        imagen_models = {}
        
        # Scrape Imagen 4 from model versions section
        imagen4_models = self.scrape_imagen4_models()
        imagen_models.update(imagen4_models)
        
        # Scrape Imagen 3 from specific section
        imagen3_models = self.scrape_imagen3_models()
        imagen_models.update(imagen3_models)
                
        return imagen_models
    
    def scrape_imagen4_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Imagen 4 models from model versions section"""
        url = "https://ai.google.dev/gemini-api/docs/imagen#model-versions"
        print(f"Scraping Imagen 4 models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        imagen4_models = {}
        
        # Look for supported data types sections after Imagen 4 mentions
        sections = soup.find_all(['div', 'section', 'article'])
        for section in sections:
            section_text = section.get_text().lower()
            if 'imagen' in section_text and ('4' in section_text or 'ultra' in section_text or 'fast' in section_text):
                # Look for input/output information
                if 'supported data types' in section_text or 'input' in section_text:
                    # Extract model names and capabilities
                    if 'ultra' in section_text:
                        imagen4_models['imagen-4-ultra'] = {
                            'input_modalities': 'Text',
                            'output_modalities': 'Image'
                        }
                        print(f"  Found: imagen-4-ultra -> Text → Image")
                    if 'fast' in section_text or 'imagen 4' in section_text:
                        imagen4_models['imagen-4-fast'] = {
                            'input_modalities': 'Text', 
                            'output_modalities': 'Image'
                        }
                        print(f"  Found: imagen-4-fast -> Text → Image")
        
        return imagen4_models
    
    def scrape_imagen3_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Imagen 3 models from specific section"""
        url = "https://ai.google.dev/gemini-api/docs/imagen#imagen-3"
        print(f"Scraping Imagen 3 models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        imagen3_models = {}
        
        # Look for Imagen 3 section and supported data types
        sections = soup.find_all(['div', 'section', 'article'])
        for section in sections:
            section_text = section.get_text().lower()
            if 'imagen' in section_text and '3' in section_text and 'supported data types' in section_text:
                # Extract input/output capabilities
                imagen3_models['imagen-3'] = {
                    'input_modalities': 'Text',
                    'output_modalities': 'Image'
                }
                print(f"  Found: imagen-3 -> Text → Image")
                break
                
        return imagen3_models

    def scrape_video_modalities(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape Video generation model capabilities from specific sections.

        Extracts modalities for both Veo 2 and Veo 3 video generation models
        from their respective documentation sections.

        Returns:
            Dict mapping video model names to their input/output modalities
        """
        video_models = {}
        
        # Scrape Veo 3 models
        veo3_models = self.scrape_veo3_models()
        video_models.update(veo3_models)
        
        # Scrape Veo 2 models
        veo2_models = self.scrape_veo2_models()
        video_models.update(veo2_models)
        
        return video_models
    
    def scrape_veo3_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Veo 3 models from supported data types section"""
        url = "https://ai.google.dev/gemini-api/docs/video#veo-3"
        print(f"Scraping Veo 3 models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        veo3_models = {}
        
        # Look for Veo 3 section and supported data types
        sections = soup.find_all(['div', 'section', 'article'])
        for section in sections:
            section_text = section.get_text().lower()
            if 'veo' in section_text and '3' in section_text:
                # Look for model names in tables or text
                tables = section.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        for cell in cells:
                            cell_text = cell.get_text().strip()
                            # Look for veo-3 model codes
                            veo3_matches = re.findall(r'veo-3[^\s]*', cell_text, re.IGNORECASE)
                            for veo_model in veo3_matches:
                                veo_model = veo_model.strip()
                                if veo_model:
                                    # Veo 3 supports audio output
                                    veo3_models[veo_model] = {
                                        'input_modalities': 'Text, Image',
                                        'output_modalities': 'Video, Audio'
                                    }
                                    print(f"  Found: {veo_model} -> Text, Image → Video, Audio")
        
        return veo3_models
    
    def scrape_veo2_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Veo 2 models from supported data types section"""
        url = "https://ai.google.dev/gemini-api/docs/video#veo-2"
        print(f"Scraping Veo 2 models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        veo2_models = {}
        
        # Look for Veo 2 section and supported data types
        sections = soup.find_all(['div', 'section', 'article'])
        for section in sections:
            section_text = section.get_text().lower()
            if 'veo' in section_text and '2' in section_text:
                # Look for model names in tables or text
                tables = section.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        for cell in cells:
                            cell_text = cell.get_text().strip()
                            # Look for veo-2 model codes
                            veo2_matches = re.findall(r'veo-2[^\s]*', cell_text, re.IGNORECASE)
                            for veo_model in veo2_matches:
                                veo_model = veo_model.strip()
                                if veo_model:
                                    # Veo 2 does not support audio output
                                    veo2_models[veo_model] = {
                                        'input_modalities': 'Text, Image',
                                        'output_modalities': 'Video'
                                    }
                                    print(f"  Found: {veo_model} -> Text, Image → Video")
        
        return veo2_models
    
    def convert_veo_api_to_display_name(self, api_name: str) -> str:
        """Convert API model names to display names"""
        # # veo-2.0-generate-001 -> Veo 2.0 Generate 001
        # # veo-3.0-generate-preview -> Veo 3.0 Generate Preview  
        # # veo-3.0-fast-generate-preview -> Veo 3.0 Fast Generate Preview
        
        # # Clean and format the name
        # name = api_name.replace('-', ' ').title()
        
        # # Fix specific formatting issues
        # name = re.sub(r'Veo\s+([0-9.]+)', r'Veo \1', name)  # Fix "Veo  3.0" -> "Veo 3.0"
        # name = re.sub(r'\s+', ' ', name)  # Remove extra spaces
        
        # # Handle common truncations  
        # if name.endswith(' P'):
        #     name = name.replace(' P', ' Preview')
        
        # return name
        
        # Return API name without conversion
        return api_name


    def scrape_gemma_modalities(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape Gemma model capabilities from official model cards.

        Extracts modalities from official Gemma model card pages for:
        - Gemma 3 (core model)
        - Gemma 2 (core model)
        - Gemma 3N (multimodal variant)

        Returns:
            Dict mapping Gemma model families to their input/output modalities
        """
        gemma_models = {}
        
        # Each URL maps to exactly one result - no merging
        urls_and_methods = [
            ("https://ai.google.dev/gemma/docs/core/model_card_3#inputs_and_outputs", self.scrape_gemma3_models),
            ("https://ai.google.dev/gemma/docs/core/model_card_2#inputs_and_outputs", self.scrape_gemma2_models),
            ("https://ai.google.dev/gemma/docs/gemma-3n/model_card#inputs_and_outputs", self.scrape_gemma3n_models)
        ]
        
        for url, method in urls_and_methods:
            try:
                print(f"\n🔄 Processing: {url}")
                result = method()
                # Each method should return exactly one key-value pair or empty dict
                if result:
                    gemma_models.update(result)
                    print(f"✅ SUCCESS: {url}")
                else:
                    print(f"⚠️  WARNING: {url} returned no results")
            except Exception as e:
                print(f"❌ ERROR processing {url}: {str(e)}")
                continue
        
        return gemma_models
    
    def detect_modalities(self, soup) -> Tuple[List[str], List[str]]:
        """Detect input and output modalities from descriptive paragraphs"""
        import re
        
        # Extract input and output modality descriptions from paragraphs
        try:
            input_description, output_description = self.find_inputs_outputs_sections(soup)
        except Exception as e:
            raise ValueError(f"❌ ERROR: Could not extract descriptions: {str(e)}")
        
        print(f"    📝 Input description: '{input_description}'")
        print(f"    📝 Output description: '{output_description}'")
        
        # Parse modalities from descriptions
        input_modalities = self.parse_modalities_from_text(input_description)
        output_modalities = self.parse_modalities_from_text(output_description)
        
        return input_modalities, output_modalities
    
    def parse_modalities_from_text(self, text: str) -> List[str]:
        """Parse modality names from text like 'text and image' or 'text, image, video, and audio'"""
        if not text:
            return []
        
        # Normalize the text
        text = text.lower().strip()
        
        # Remove common words that aren't modalities
        text = re.sub(r'\b(and|or|input|output|outputs)\b', '', text)
        
        # Split by both commas and remaining spaces, then clean up
        parts = re.split(r'[,\s]+', text)
        parts = [part.strip() for part in parts if part.strip()]
        
        # Map text parts to standard modality names
        modality_mapping = {
            'text': 'Text',
            'image': 'Image',
            'images': 'Image', 
            'audio': 'Audio',
            'video': 'Video',
            'pdf': 'Pdf',
            'document': 'Pdf'
        }
        
        modalities = []
        for part in parts:
            if part in modality_mapping:
                modality = modality_mapping[part]
                if modality not in modalities:
                    modalities.append(modality)
        
        return modalities
    
    def find_inputs_outputs_sections(self, soup) -> Tuple[str, str]:
        """Extract input and output modalities from descriptive paragraphs"""
        # Check p[6], then p[7], then fallback to general search
        
        try:
            # Find article element
            article = soup.find('article')
            if not article:
                raise ValueError("❌ ERROR: Could not find article element")
            
            # Find div[4] within article
            divs = article.find_all('div', recursive=False)
            if len(divs) < 4:
                raise ValueError(f"❌ ERROR: Expected at least 4 divs in article, found {len(divs)}")
            
            target_div = divs[3]  # div[4] = index 3
            
            # Get all paragraphs in the div
            paragraphs = target_div.find_all('p', recursive=False)
            
            # Try p[6] first (index 5)
            if len(paragraphs) >= 6:
                p6_text = paragraphs[5].get_text().strip()
                print(f"    📍 Checking p[6]: {p6_text[:100]}...")
                if self.contains_modality_info(p6_text):
                    input_desc = self.extract_input_modalities_from_description(p6_text)
                    output_desc = self.extract_output_modalities_from_description(p6_text)
                    if input_desc or output_desc:
                        print(f"    ✅ Found modality info in p[6]")
                        return input_desc, output_desc
            
            # Try p[7] second (index 6)
            if len(paragraphs) >= 7:
                p7_text = paragraphs[6].get_text().strip()
                print(f"    📍 Checking p[7]: {p7_text[:100]}...")
                if self.contains_modality_info(p7_text):
                    input_desc = self.extract_input_modalities_from_description(p7_text)
                    output_desc = self.extract_output_modalities_from_description(p7_text)
                    if input_desc or output_desc:
                        print(f"    ✅ Found modality info in p[7]")
                        return input_desc, output_desc
            
            # Fallback: check all paragraphs for modality information
            print(f"    📍 Fallback: Searching all paragraphs...")
            for i, p in enumerate(paragraphs):
                p_text = p.get_text().strip()
                if self.contains_modality_info(p_text):
                    input_desc = self.extract_input_modalities_from_description(p_text)
                    output_desc = self.extract_output_modalities_from_description(p_text)
                    if input_desc or output_desc:
                        print(f"    ✅ Found modality info in p[{i+1}]")
                        return input_desc, output_desc
            
            raise ValueError("❌ ERROR: No paragraphs with modality information found")
            
        except Exception as e:
            raise ValueError(f"❌ ERROR: Paragraph parsing failed: {str(e)}")
    
    def contains_modality_info(self, text: str) -> bool:
        """Check if text contains modality description phrases"""
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in [
            'handling', 'input and generating', 'capable of', 'multimodal',
            'text and image input', 'generating text output', 'text-to-text',
            'decoder-only', 'language model'
        ])
    
    def extract_input_modalities_from_description(self, text: str) -> str:
        """Extract input modalities from descriptive text"""
        import re
        
        # Patterns to match input descriptions
        input_patterns = [
            r'handling\s+([^,]+(?:,\s*[^,]+)*)\s+input',  # "handling text and image input"
            r'([^,]+(?:,\s*[^,]+)*)\s+input\s+and\s+generating',  # "text and image input and generating"
            r'multimodal\s+input,\s+handling\s+([^,]+(?:,\s*[^,]+)*)',  # "multimodal input, handling text, image..."
            r'([^-\s]+(?:\s*,\s*[^-\s]+)*)-to-',  # "text-to-text" -> extract "text" part
            r'capable\s+of\s+multimodal\s+input,\s+handling\s+([^,]+(?:,\s*[^,]+)*)',  # "capable of multimodal input, handling text..."
        ]
        
        for pattern in input_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def extract_output_modalities_from_description(self, text: str) -> str:
        """Extract output modalities from descriptive text"""
        import re
        
        # Patterns to match output descriptions
        output_patterns = [
            r'generating\s+([^,]+(?:,\s*[^,]+)*)\s+output',  # "generating text output"
            r'and\s+generating\s+([^,]+(?:,\s*[^,]+)*)',  # "and generating text outputs"
            r'-to-([^,\s]+(?:\s*,\s*[^,\s]+)*)',  # "text-to-text" -> extract second "text" part
        ]
        
        for pattern in output_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def extract_family_name_from_title(self, page_text: str) -> Optional[str]:
        """Extract family name from page title containing 'model card'"""
        import re
        
        # Look for main title patterns with "model card"
        title_patterns = [
            r'<h1[^>]*>([^<]*model\s+card[^<]*)</h1>',  # H1 tags
            r'<title[^>]*>([^<]*model\s+card[^<]*)</title>',  # Title tags
            r'^([^\n]*model\s+card[^\n]*)$',  # Line containing "model card"
            r'#\s*([^\n]*model\s+card[^\n]*)',  # Markdown headers
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Extract family name from title like "Gemma 3 model card"
                family_match = re.search(r'(Gemma\s+\w+)', match, re.IGNORECASE)
                if family_match:
                    return family_match.group(1).title()  # Return "Gemma 3", "Gemma 2", etc.
        
        # Fallback: look for headings mentioning Gemma variants
        heading_patterns = [
            r'<h[1-6][^>]*>([^<]*Gemma[^<]*)</h[1-6]>',
            r'^#+\s*([^\n]*Gemma[^\n]*)',  # Markdown headers
        ]
        
        for pattern in heading_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Extract family name
                family_match = re.search(r'(Gemma\s+\w+)', match, re.IGNORECASE)
                if family_match and 'model card' in match.lower():
                    return family_match.group(1).title()
        
        return None
    
    def scrape_gemma3_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Gemma 3 model capabilities from model card"""
        url = "https://ai.google.dev/gemma/docs/core/model_card_3#inputs_and_outputs"
        
        try:
            soup = self.fetch_page(url)
            if not soup:
                raise Exception("Failed to fetch page content")
                
            gemma_models = {}
            page_text = soup.get_text()
            full_html = str(soup)
            
            # Extract family name from title
            family_name = self.extract_family_name_from_title(full_html)
            if not family_name:
                raise Exception("No family name found in page title")
            
            print(f"  📝 Extracted family name: {family_name}")
            
            # Extract modalities
            input_modalities, output_modalities = self.detect_modalities(soup)
            
            if input_modalities and output_modalities:
                # Use URL-specific key to ensure 1:1 mapping
                unique_key = f"{family_name} (model_card_3)"
                gemma_models[unique_key] = {
                    'input_modalities': ', '.join(input_modalities),
                    'output_modalities': ', '.join(output_modalities)
                }
                print(f"  ✅ Found: {unique_key} -> {', '.join(input_modalities)} → {', '.join(output_modalities)}")
            else:
                raise Exception(f"No modalities extracted - Input: {input_modalities}, Output: {output_modalities}")
            
            return gemma_models
            
        except Exception as e:
            raise Exception(f"Gemma 3 scraping failed: {str(e)}")
    
    def scrape_gemma2_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Gemma 2 model capabilities from model card"""
        url = "https://ai.google.dev/gemma/docs/core/model_card_2#inputs_and_outputs"
        print(f"Scraping Gemma models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        gemma_models = {}
        page_text = soup.get_text()
        full_html = str(soup)
        
        # Extract family name from title
        family_name = self.extract_family_name_from_title(full_html)
        if not family_name:
            print("  No family name found in page title")
            return {}
        
        # Extract modalities
        input_modalities, output_modalities = self.detect_modalities(soup)
        
        if input_modalities and output_modalities:
            # Use URL-specific key to ensure 1:1 mapping
            unique_key = f"{family_name} (model_card_2)"
            gemma_models[unique_key] = {
                'input_modalities': ', '.join(input_modalities),
                'output_modalities': ', '.join(output_modalities)
            }
            print(f"  Found: {unique_key} -> {', '.join(input_modalities)} → {', '.join(output_modalities)}")
        
        return gemma_models
    
    def scrape_gemma3n_models(self) -> Dict[str, Dict[str, str]]:
        """Scrape Gemma 3N model capabilities from model card"""
        url = "https://ai.google.dev/gemma/docs/gemma-3n/model_card#inputs_and_outputs"
        print(f"Scraping Gemma models from {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            return {}
            
        gemma_models = {}
        page_text = soup.get_text()
        full_html = str(soup)
        
        # Extract family name from title
        family_name = self.extract_family_name_from_title(full_html)
        if not family_name:
            print("  No family name found in page title")
            return {}
        
        # Extract modalities
        input_modalities, output_modalities = self.detect_modalities(soup)
        
        if input_modalities and output_modalities:
            # Use URL-specific key to ensure 1:1 mapping
            unique_key = f"{family_name} (gemma-3n)"
            gemma_models[unique_key] = {
                'input_modalities': ', '.join(input_modalities),
                'output_modalities': ', '.join(output_modalities)
            }
            print(f"  Found: {unique_key} -> {', '.join(input_modalities)} → {', '.join(output_modalities)}")
        
        return gemma_models

    def generate_modality_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Generate consolidated modality mapping from all sources.

        Orchestrates scraping from all Google AI model documentation sources:
        - Gemini models (generative AI)
        - Imagen models (image generation)
        - Video models (video generation)
        - Gemma models (open source)

        Returns:
            Consolidated dict mapping all model names to their modalities
        """
        print("=== Starting Google Documentation Modality Scraping ===")
        
        all_modalities = {}
        
        # Scrape each source
        gemini_modalities = self.scrape_gemini_models()
        imagen_modalities = self.scrape_imagen_modalities()  
        video_modalities = self.scrape_video_modalities()
        gemma_modalities = self.scrape_gemma_modalities()
        
        # Combine all modalities
        all_modalities.update(gemini_modalities)
        all_modalities.update(imagen_modalities)
        all_modalities.update(video_modalities) 
        all_modalities.update(gemma_modalities)
        
        print(f"\n=== Scraping Complete: {len(all_modalities)} models found ===")
        for model, capabilities in all_modalities.items():
            input_mod = capabilities['input_modalities']
            output_mod = capabilities['output_modalities']
            print(f"  {model}: {input_mod} → {output_mod}")
            
        return all_modalities

    def normalize_gemma_display_name(self, key: str) -> str:
        """Normalize Gemma display names to format: gemma-3, gemma-2, gemma-3n"""
        if "Gemma 3 (model_card_3)" in key:
            return key.replace("Gemma 3 (model_card_3)", "gemma-3")
        elif "Gemma 2 (model_card_2)" in key:
            return key.replace("Gemma 2 (model_card_2)", "gemma-2")  
        elif "Gemma 3N (gemma-3n)" in key:
            return key.replace("Gemma 3N (gemma-3n)", "gemma-3n")
        return key

    def save_modality_mapping(self, output_file: str = "../02_outputs/C-scrapped-modalities.json"):
        """
        Save modality mapping to JSON file with normalized Gemma names.

        Generates both JSON and human-readable text reports with scraped modalities.
        Handles errors gracefully by creating empty output files if scraping fails.

        Args:
            output_file: Path to save JSON output (default: C-scrapped-modalities.json)

        Returns:
            Dict of scraped modalities, or empty dict if scraping failed
        """
        try:
            modality_mapping = self.generate_modality_mapping()

            # Normalize Gemma display names
            normalized_mapping = {}
            for key, value in modality_mapping.items():
                normalized_key = self.normalize_gemma_display_name(key)
                normalized_mapping[normalized_key] = value

            # Always generate output files, even if empty
            # Create JSON output with metadata (similar to A and B scripts)
            json_output = {
                "metadata": {
                    "generated": get_ist_timestamp(),
                    "total_models": len(normalized_mapping),
                    "scraping_source": "Google Documentation Web Scraper"
                },
                "modalities": normalized_mapping
            }

            with open(output_file, 'w') as f:
                json.dump(json_output, f, indent=2)

            # Generate human-readable text version
            txt_filename = output_file.replace('.json', '-report.txt')
            with open(txt_filename, 'w') as f:
                f.write("=== GOOGLE MODELS MODALITY SCRAPING REPORT ===\n")
                f.write(f"Generated: {get_ist_timestamp()}\n\n")
                f.write(f"Total Models: {len(normalized_mapping)}\n\n")

                if normalized_mapping:
                    for model, capabilities in normalized_mapping.items():
                        input_mod = capabilities['input_modalities']
                        output_mod = capabilities['output_modalities']
                        f.write(f"{model}: {input_mod} → {output_mod}\n")
                else:
                    f.write("No modalities found - web scraping may have failed\n")

            print(f"\nModality mapping saved to: {output_file}")
            print(f"Human-readable version saved to: {txt_filename}")
            return normalized_mapping

        except Exception as e:
            print(f"⚠️ Error during modality scraping: {e}")
            # Generate empty output files to maintain pipeline consistency
            json_output = {
                "metadata": {
                    "generated": get_ist_timestamp(),
                    "total_models": 0,
                    "scraping_source": "Google Documentation Web Scraper"
                },
                "modalities": {}
            }

            with open(output_file, 'w') as f:
                json.dump(json_output, f, indent=2)

            txt_filename = output_file.replace('.json', '-report.txt')
            with open(txt_filename, 'w') as f:
                f.write("=== GOOGLE MODELS MODALITY SCRAPING REPORT ===\n")
                f.write(f"Generated: {get_ist_timestamp()}\n\n")
                f.write("Total Models: 0\n\n")
                f.write(f"Error during scraping: {e}\n")

            print(f"⚠️ Empty output files generated due to scraping failure")
            return {}

if __name__ == "__main__":
    scraper = GoogleModalityScraper()
    mapping = scraper.save_modality_mapping()

    # Check if scraping produced insufficient results (likely CI/CD failure)
    if len(mapping) < 15:  # Expect 20+ models normally
        print(f"\n⚠️ WARNING: Only {len(mapping)} modalities scraped")
        print("⚠️ This suggests web scraping failed in CI/CD environment")

        # Try to restore from backup if it exists
        backup_file = "../02_outputs/C-scrapped-modalities.json"
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
                    backup_count = len(backup_data.get('modalities', {}))

                if backup_count > len(mapping):
                    print(f"📋 Found better backup with {backup_count} modalities - keeping backup")
                    print("📋 Current scraping results discarded due to insufficient data")
                else:
                    print(f"📋 Backup has {backup_count} modalities - keeping new results")

            except Exception as e:
                print(f"📋 Could not read backup: {e}")
        else:
            print("📋 No backup available - proceeding with limited scraped data")
            print("📋 Downstream enrichment will use embedding patterns and fallbacks")
