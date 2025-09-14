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
from typing import Dict, List, Tuple, Optional
from urllib.parse import urljoin

class GoogleModalityScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.modality_mapping = {}
        
    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse HTML page with retry logic"""
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
        """Load modality configuration from 02_modality_standardization.json"""
        try:
            with open('02_modality_standardization.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ 02_modality_standardization.json not found, returning Unknown")
            return "Unknown"

    def standardize_modalities(self, modalities: List[str]) -> str:
        """Convert modalities to standardized format using 02_modality_standardization.json"""
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
        """Scrape Gemini model capabilities from model variations section"""
        url = "https://ai.google.dev/gemini-api/docs/models#model-variations"
        print(f"Scraping Gemini models from {url}")
        
        soup = self.fetch_page(url)
        gemini_models = {}
        
        if soup:
            # Look specifically for model variations table
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])] if rows else []
                
                # Find columns for model, input, output
                model_col = input_col = output_col = -1
                for i, header in enumerate(headers):
                    if 'model' in header or 'name' in header:
                        model_col = i
                    elif 'input' in header:
                        input_col = i
                    elif 'output' in header:
                        output_col = i
                
                # Process data rows
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) > max(model_col, input_col, output_col) and model_col >= 0:
                        model_name = cells[model_col].get_text().strip()
                        
                        if 'gemini' in model_name.lower() and model_name:
                            # Extract input/output from table or use fallback
                            input_modalities = cells[input_col].get_text().strip() if input_col >= 0 and input_col < len(cells) else ""
                            output_modalities = cells[output_col].get_text().strip() if output_col >= 0 and output_col < len(cells) else ""
                            
                            # If no table data, use model-specific mapping
                            if not input_modalities or not output_modalities:
                                model_caps = self.get_model_specific_capabilities(model_name)
                                if model_caps:
                                    input_modalities = ', '.join(model_caps['input'])
                                    output_modalities = ', '.join(model_caps['output'])
                            
                            if input_modalities and output_modalities:
                                gemini_models[model_name] = {
                                    'input_modalities': input_modalities,
                                    'output_modalities': output_modalities
                                }
                                print(f"  Found: {model_name} -> {input_modalities} → {output_modalities}")
            
            # Fallback: Look for model sections in the page if table parsing failed
            if not gemini_models:
                gemini_models = self.extract_gemini_from_sections(soup)
        
        return gemini_models

    def extract_model_capabilities(self, row, soup) -> Optional[Dict[str, str]]:
        """Extract input/output capabilities for a specific model"""
        row_text = row.get_text().strip()
        model_name = self.normalize_model_name(row_text)
        
        # Model-specific capability mapping
        capabilities = self.get_model_specific_capabilities(model_name)
        
        if capabilities:
            return {
                # 'input_modalities': self.standardize_modalities(capabilities['input']),
                # 'output_modalities': self.standardize_modalities(capabilities['output'])
                'input_modalities': ', '.join(capabilities['input']),
                'output_modalities': ', '.join(capabilities['output'])
            }
        return None

    def extract_gemini_from_sections(self, soup) -> Dict[str, Dict[str, str]]:
        """Extract Gemini models from page sections"""
        gemini_models = {}
        
        # Look for headings and content that mention Gemini models
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        for heading in headings:
            heading_text = heading.get_text().strip()
            if 'gemini' in heading_text.lower():
                # Extract model name
                model_match = re.search(r'gemini[^\s]*(?:\s+\d+[.\d]*)?(?:\s+\w+)*', heading_text.lower())
                if model_match:
                    model_name = self.normalize_model_name(model_match.group(0))
                    capabilities = self.get_model_specific_capabilities(model_name)
                    
                    if capabilities:
                        gemini_models[model_name] = {
                            # 'input_modalities': self.standardize_modalities(capabilities['input']),
                            # 'output_modalities': self.standardize_modalities(capabilities['output'])
                            'input_modalities': ', '.join(capabilities['input']),
                            'output_modalities': ', '.join(capabilities['output'])
                        }
                        
        return gemini_models

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
        """Scrape Imagen model capabilities from specific sections"""
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
        """Scrape Video generation model capabilities from specific sections"""
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
        """Scrape Gemma model capabilities from official model cards"""
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
        """Generate consolidated modality mapping from all sources"""
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

    def save_modality_mapping(self, output_file: str = "C-scrapped-modalities.json"):
        """Save modality mapping to JSON file with normalized Gemma names"""
        modality_mapping = self.generate_modality_mapping()
        
        # Normalize Gemma display names
        normalized_mapping = {}
        for key, value in modality_mapping.items():
            normalized_key = self.normalize_gemma_display_name(key)
            normalized_mapping[normalized_key] = value
        
        with open(output_file, 'w') as f:
            json.dump(normalized_mapping, f, indent=2)
            
        # Generate human-readable text version
        txt_filename = output_file.replace('.json', '-report.txt')
        with open(txt_filename, 'w') as f:
            f.write(f"Total Models: {len(normalized_mapping)}\n\n")
            
            for model, capabilities in normalized_mapping.items():
                input_mod = capabilities['input_modalities']
                output_mod = capabilities['output_modalities']
                f.write(f"{model}: {input_mod} → {output_mod}\n")
        
        print(f"\nModality mapping saved to: {output_file}")
        print(f"Human-readable version saved to: {txt_filename}")
        return normalized_mapping

if __name__ == "__main__":
    scraper = GoogleModalityScraper()
    mapping = scraper.save_modality_mapping()