#!/usr/bin/env python3
"""
Google Models Modality Enrichment Script
Links B-filtered-models.json with C-scrapped-modalities.json
to produce D-enriched-modalities.json with input/output modalities
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple

class ModalityEnrichment:
    def __init__(self):
        self.filtered_models = []
        self.scraped_modalities = {}
        self.embedding_config = {}
        self.modality_standardization = {}
        self.unique_models_config = {}
        self.enriched_models = []
        self.matching_stats = {
            'total_models': 0,
            'priority_1_matches': 0,
            'priority_2_matches': 0,
            'embedding_matches': 0,
            'gemma_matches': 0,
            'unique_matches': 0,
            'no_matches': 0,
            'match_details': []
        }
        
    def load_data_files(self) -> bool:
        """Load both input JSON files"""
        # Load filtered models
        try:
            with open('B-filtered-models.json', 'r') as f:
                self.filtered_models = json.load(f)
                print(f"✅ Loaded {len(self.filtered_models)} filtered models")
        except FileNotFoundError:
            print("❌ B-filtered-models.json not found")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing B-filtered-models.json: {e}")
            return False
            
        # Load scraped modalities
        try:
            with open('C-scrapped-modalities.json', 'r') as f:
                self.scraped_modalities = json.load(f)
                print(f"✅ Loaded {len(self.scraped_modalities)} scraped modality entries")
        except FileNotFoundError:
            print("❌ C-scrapped-modalities.json not found")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing C-scrapped-modalities.json: {e}")
            return False
            
        # Load embedding models configuration
        try:
            with open('04_embedding_models.json', 'r') as f:
                self.embedding_config = json.load(f)
                print(f"✅ Loaded embedding models configuration")
        except FileNotFoundError:
            print("⚠️ 04_embedding_models.json not found - embedding models will be skipped")
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing 04_embedding_models.json: {e}")
            
        # Load modality standardization configuration
        try:
            with open('02_modality_standardization.json', 'r') as f:
                self.modality_standardization = json.load(f)
                print(f"✅ Loaded modality standardization configuration")
        except FileNotFoundError:
            print("⚠️ 02_modality_standardization.json not found - modalities will not be standardized")
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing 02_modality_standardization.json: {e}")
            
        # Load unique models configuration
        try:
            with open('06_unique_models_modalities.json', 'r') as f:
                self.unique_models_config = json.load(f)
                print(f"✅ Loaded unique models configuration")
        except FileNotFoundError:
            print("⚠️ 06_unique_models_modalities.json not found - unique models will not be processed")
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing 06_unique_models_modalities.json: {e}")
            
        return True

    def extract_api_id_from_stage3_key(self, key: str) -> str:
        """Extract API identifier from stage-3 modality key"""
        # Handle compound keys with newline separator
        if '\n' in key:
            # Split by newline and take the API ID part
            parts = key.split('\n')
            api_part = parts[1].strip()
            
            # Handle multiple API IDs separated by &
            if ' &' in api_part:
                api_part = api_part.split(' &')[0].strip()
                
            return api_part
        else:
            # Direct API ID or simple key
            return key.strip()

    def extract_api_id_from_stage2_name(self, name: str) -> str:
        """Extract API identifier from stage-2 model name"""
        # Remove 'models/' prefix
        if name.startswith('models/'):
            return name[7:]  # Remove 'models/' prefix
        return name

    def normalize_api_id(self, api_id: str) -> str:
        """Normalize API ID by removing version suffixes and service indicators for Priority 2 matching"""
        normalized = api_id.lower()
        
        # Remove version suffixes
        normalized = re.sub(r'-\d{3}$', '', normalized)  # Remove -001, -002, etc.
        normalized = normalized.replace('-latest', '')
        
        # Remove service indicators
        normalized = normalized.replace('-generate', '')
        normalized = normalized.replace('.0', '')
        normalized = re.sub(r'-(ultra|fast)(?=-|$)', '', normalized)  # Remove -ultra, -fast when followed by - or end
        
        return normalized

    def find_modality_match(self, stage2_api_id: str) -> Tuple[Optional[Dict], int, str]:
        """
        Find modality match using two-priority strategy
        Returns (modality_data, priority, matched_api_id) where priority is 1 or 2, or (None, 0, '') for no match
        """
        # Priority 1: Exact match with full identifiers
        for stage3_key, modality_data in self.scraped_modalities.items():
            stage3_api_id = self.extract_api_id_from_stage3_key(stage3_key)
            
            if stage2_api_id.lower() == stage3_api_id.lower():
                return modality_data, 1, stage3_api_id
                
        # Priority 2: Normalized match (strip versions and service indicators)
        stage2_normalized = self.normalize_api_id(stage2_api_id)
        
        for stage3_key, modality_data in self.scraped_modalities.items():
            stage3_api_id = self.extract_api_id_from_stage3_key(stage3_key)
            stage3_normalized = self.normalize_api_id(stage3_api_id)
            
            if stage2_normalized == stage3_normalized:
                return modality_data, 2, stage3_api_id
                
        return None, 0, ''

    def extract_gemma_pattern(self, api_id: str) -> Optional[str]:
        """Extract gemma-x pattern from API ID like 'gemma-3-1b-it' -> 'gemma-3'"""
        import re
        match = re.search(r'gemma-(\d+n?)', api_id.lower())
        if match:
            return f"gemma-{match.group(1)}"
        return None

    def find_gemma_modality_match(self, stage2_api_id: str) -> Tuple[Optional[Dict], int, str]:
        """Find modality match for Gemma models using pattern extraction"""
        gemma_pattern = self.extract_gemma_pattern(stage2_api_id)
        if not gemma_pattern:
            return None, 0, ''
        
        # Look for exact match with the gemma pattern in stage-3 keys
        for stage3_key, modality_data in self.scraped_modalities.items():
            if stage3_key.lower() == gemma_pattern.lower():
                return modality_data, 4, gemma_pattern  # Priority 4 for Gemma pattern matching
                
        return None, 0, ''

    def find_unique_model_match(self, stage2_api_id: str) -> Tuple[Optional[Dict], int, str]:
        """Find modality match for unique models using hardcoded configuration"""
        if not self.unique_models_config:
            return None, 0, ''
        
        unique_models = self.unique_models_config.get('unique_models', {}).get('models', {})
        
        # Check direct match with API ID
        if stage2_api_id.lower() in unique_models:
            model_config = unique_models[stage2_api_id.lower()]
            modality_data = {
                'input_modalities': model_config.get('input_modalities', 'Text'),
                'output_modalities': model_config.get('output_modalities', 'Text')
            }
            return modality_data, 5, stage2_api_id  # Priority 5 for unique models
        
        return None, 0, ''

    def is_embedding_model(self, api_id: str) -> bool:
        """Check if model is an embedding model based on search patterns"""
        if not self.embedding_config:
            return False
            
        search_patterns = self.embedding_config.get('embedding_models', {}).get('search_patterns', [])
        api_id_lower = api_id.lower()
        
        for pattern in search_patterns:
            if pattern.lower() in api_id_lower:
                return True
                
        return False

    def standardize_modalities(self, modalities_str: str) -> str:
        """
        Standardize modality ordering using 02_modality_standardization.json
        """
        if not modalities_str or modalities_str.strip() == '':
            return ''
            
        if not self.modality_standardization:
            return modalities_str  # Return as-is if no config available
        
        modality_mappings = self.modality_standardization.get('modality_mappings', {})
        ordering_priority = self.modality_standardization.get('ordering_priority', {})
        
        # Split and clean modalities
        modalities = [m.strip() for m in modalities_str.split(',') if m.strip()]
        
        # Normalize variations using configuration
        normalized = []
        for modality in modalities:
            modality_lower = modality.lower()
            
            # Handle "Text Embeddings" as special case first
            if 'embedding' in modality_lower and 'text' in modality_lower:
                normalized.append('Text Embeddings')
            else:
                # Check against modality mappings
                mapped = False
                for key, value in modality_mappings.items():
                    if key.lower() in modality_lower:
                        normalized.append(value)
                        mapped = True
                        break
                
                if not mapped:
                    normalized.append(modality)  # Keep original if unknown
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for modality in normalized:
            if modality not in seen:
                result.append(modality)
                seen.add(modality)
        
        # Sort by priority from 02_modality_standardization.json configuration
        # Text Embeddings gets same priority as Text
        result.sort(key=lambda x: ordering_priority.get(x, ordering_priority.get('Text', 1)) if 'Embeddings' in x else ordering_priority.get(x, 99))
        
        return ', '.join(result) if result else ''

    def get_embedding_modalities(self) -> Dict[str, str]:
        """Get default embedding modalities from configuration"""
        if not self.embedding_config:
            default_modalities = {'input_modalities': 'Text', 'output_modalities': 'Text Embeddings'}
        else:
            default_modalities = self.embedding_config.get('embedding_models', {}).get('default_modalities', {
                'input_modalities': 'Text', 
                'output_modalities': 'Text Embeddings'
            })
        
        # Standardize the modalities
        standardized_modalities = {}
        for key, value in default_modalities.items():
            standardized_modalities[key] = self.standardize_modalities(value)
            
        return standardized_modalities

    def enrich_models(self) -> None:
        """Enrich filtered models with modality data"""
        print(f"\n=== Enriching {len(self.filtered_models)} models with modality data ===")
        
        self.matching_stats['total_models'] = len(self.filtered_models)
        
        for model in self.filtered_models:
            model_name = model.get('name', 'Unknown')
            display_name = model.get('displayName', 'Unknown')
            
            # Extract API ID from stage-2 model
            stage2_api_id = self.extract_api_id_from_stage2_name(model_name)
            
            # Check if this is a unique model first (highest priority)
            unique_data, unique_priority, unique_matched_id = self.find_unique_model_match(stage2_api_id)
            if unique_data:
                enriched_model = model.copy()
                input_modalities = unique_data.get('input_modalities', 'Text')
                output_modalities = unique_data.get('output_modalities', 'Text')
                enriched_model['input_modalities'] = self.standardize_modalities(input_modalities)
                enriched_model['output_modalities'] = self.standardize_modalities(output_modalities)
                enriched_model['modality_source'] = 'unique_config'
                enriched_model['match_priority'] = unique_priority
                
                self.matching_stats['unique_matches'] += 1
                print(f"🔧 Unique Model: {display_name} ({stage2_api_id})")
                
                match_detail = {
                    'model_name': model_name,
                    'display_name': display_name,
                    'api_id': stage2_api_id,
                    'match_found': True,
                    'match_priority': unique_priority,
                    'input_modalities': enriched_model['input_modalities'],
                    'output_modalities': enriched_model['output_modalities']
                }
                self.matching_stats['match_details'].append(match_detail)
                self.enriched_models.append(enriched_model)
                continue
            
            # Check if this is an embedding model
            if self.is_embedding_model(stage2_api_id):
                # Handle embedding model
                embedding_modalities = self.get_embedding_modalities()
                enriched_model = model.copy()
                enriched_model['input_modalities'] = embedding_modalities['input_modalities']
                enriched_model['output_modalities'] = embedding_modalities['output_modalities']
                enriched_model['modality_source'] = 'embedding_config'
                enriched_model['match_priority'] = 3
                
                self.matching_stats['embedding_matches'] += 1
                print(f"🔍 Embedding: {display_name} ({stage2_api_id})")
                
                match_detail = {
                    'model_name': model_name,
                    'display_name': display_name,
                    'api_id': stage2_api_id,
                    'match_found': True,
                    'match_priority': 3,
                    'input_modalities': enriched_model['input_modalities'],
                    'output_modalities': enriched_model['output_modalities']
                }
                self.matching_stats['match_details'].append(match_detail)
                self.enriched_models.append(enriched_model)
                continue
            
            # Check if this is a Gemma model with pattern matching
            gemma_data, gemma_priority, gemma_pattern = self.find_gemma_modality_match(stage2_api_id)
            if gemma_data:
                enriched_model = model.copy()
                input_modalities = gemma_data.get('input_modalities', 'Unknown')
                output_modalities = gemma_data.get('output_modalities', 'Unknown')
                enriched_model['input_modalities'] = self.standardize_modalities(input_modalities)
                enriched_model['output_modalities'] = self.standardize_modalities(output_modalities)
                enriched_model['modality_source'] = 'gemma_pattern'
                enriched_model['match_priority'] = gemma_priority
                
                self.matching_stats['gemma_matches'] += 1
                print(f"🧬 Gemma Pattern: {display_name} ({stage2_api_id}) → {gemma_pattern}")
                
                match_detail = {
                    'model_name': model_name,
                    'display_name': display_name,
                    'api_id': stage2_api_id,
                    'match_found': True,
                    'match_priority': gemma_priority,
                    'matched_api_id': gemma_pattern,
                    'input_modalities': enriched_model['input_modalities'],
                    'output_modalities': enriched_model['output_modalities']
                }
                self.matching_stats['match_details'].append(match_detail)
                self.enriched_models.append(enriched_model)
                continue
            
            # Find matching modality data
            modality_data, priority, matched_api_id = self.find_modality_match(stage2_api_id)
            
            # Create enriched model (copy original + add modality data)
            enriched_model = model.copy()
            
            if modality_data:
                # Add modality information and standardize
                input_modalities = modality_data.get('input_modalities', 'Unknown')
                output_modalities = modality_data.get('output_modalities', 'Unknown')
                enriched_model['input_modalities'] = self.standardize_modalities(input_modalities)
                enriched_model['output_modalities'] = self.standardize_modalities(output_modalities)
                enriched_model['modality_source'] = 'scraped'
                enriched_model['match_priority'] = priority
                
                # Update statistics
                if priority == 1:
                    self.matching_stats['priority_1_matches'] += 1
                    match_type = "Priority 1 (Exact)"
                else:
                    self.matching_stats['priority_2_matches'] += 1
                    match_type = "Priority 2 (Normalized)"
                    
                print(f"✅ {match_type}: {display_name} ({stage2_api_id})")
                
            else:
                # No match found
                enriched_model['input_modalities'] = 'Unknown'
                enriched_model['output_modalities'] = 'Unknown'
                enriched_model['modality_source'] = 'unknown'
                enriched_model['match_priority'] = 0
                
                self.matching_stats['no_matches'] += 1
                print(f"❌ No match: {display_name} ({stage2_api_id})")
                
            # Store match details for reporting
            match_detail = {
                'model_name': model_name,
                'display_name': display_name,
                'api_id': stage2_api_id,
                'match_found': modality_data is not None,
                'match_priority': priority,
                'input_modalities': enriched_model['input_modalities'],
                'output_modalities': enriched_model['output_modalities']
            }
            
            # Add matched API ID for priority 2 matches
            if modality_data and priority == 2:
                match_detail['matched_api_id'] = matched_api_id
            
            self.matching_stats['match_details'].append(match_detail)
            
            self.enriched_models.append(enriched_model)

    def save_enriched_models(self) -> None:
        """Save enriched models to JSON file"""
        try:
            with open('D-enriched-modalities.json', 'w') as f:
                json.dump(self.enriched_models, f, indent=2)
            print(f"\n✅ Saved {len(self.enriched_models)} enriched models to D-enriched-modalities.json")
        except Exception as e:
            print(f"❌ Error saving enriched models: {e}")

    def generate_enrichment_report(self) -> None:
        """Generate detailed enrichment report"""
        report_content = []
        
        # Header
        report_content.append("=== GOOGLE MODELS MODALITY ENRICHMENT REPORT ===\n")
        report_content.append(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_content.append("")
        
        # Summary statistics
        total = self.matching_stats['total_models']
        priority_1 = self.matching_stats['priority_1_matches']
        priority_2 = self.matching_stats['priority_2_matches']
        embedding_matches = self.matching_stats['embedding_matches']
        gemma_matches = self.matching_stats['gemma_matches']
        unique_matches = self.matching_stats['unique_matches']
        no_matches = self.matching_stats['no_matches']
        
        report_content.append("=== SUMMARY ===")
        report_content.append(f"Total Models: {total}")
        report_content.append(f"Priority 1 Matches (Exact): {priority_1}")
        report_content.append(f"Priority 2 Matches (Normalized): {priority_2}")
        report_content.append(f"Embedding Matches: {embedding_matches}")
        report_content.append(f"Gemma Pattern Matches: {gemma_matches}")
        report_content.append(f"Unique Model Matches: {unique_matches}")
        report_content.append(f"No Matches: {no_matches}")
        report_content.append(f"Overall Match Rate: {(priority_1 + priority_2 + embedding_matches + gemma_matches + unique_matches)/total*100:.1f}%")
        report_content.append("")
        
        # Priority 1 matches
        if priority_1 > 0:
            report_content.append("=== PRIORITY 1 MATCHES (EXACT) ===\n")
            for i, detail in enumerate([d for d in self.matching_stats['match_details'] if d['match_priority'] == 1], 1):
                report_content.append(f"{i:2d}. {detail['api_id']}")
                report_content.append(f"    Input: {detail['input_modalities']}")
                report_content.append(f"    Output: {detail['output_modalities']}")
                report_content.append("")
        
        # Priority 2 matches
        if priority_2 > 0:
            report_content.append("=== PRIORITY 2 MATCHES (NORMALIZED) ===\n")
            for i, detail in enumerate([d for d in self.matching_stats['match_details'] if d['match_priority'] == 2], 1):
                report_content.append(f"{i:2d}. {detail['api_id']}")
                # Show normalized transformation
                normalized_stage2 = self.normalize_api_id(detail['api_id'])
                normalized_stage3 = self.normalize_api_id(detail.get('matched_api_id', ''))
                report_content.append(f"    Filtered model's API ID normalized: '{normalized_stage2}'")
                report_content.append(f"    Scraped model's API ID normalized: '{normalized_stage3}'")
                report_content.append(f"    Input: {detail['input_modalities']}")
                report_content.append(f"    Output: {detail['output_modalities']}")
                report_content.append("")
        
        # Embedding matches
        if embedding_matches > 0:
            report_content.append("=== EMBEDDING MATCHES ===\n")
            for i, detail in enumerate([d for d in self.matching_stats['match_details'] if d['match_priority'] == 3], 1):
                report_content.append(f"{i:2d}. {detail['api_id']}")
                report_content.append(f"    Input: {detail['input_modalities']}")
                report_content.append(f"    Output: {detail['output_modalities']}")
                report_content.append("")
        
        # Gemma pattern matches
        if gemma_matches > 0:
            report_content.append("=== GEMMA PATTERN MATCHES ===\n")
            for i, detail in enumerate([d for d in self.matching_stats['match_details'] if d['match_priority'] == 4], 1):
                report_content.append(f"{i:2d}. {detail['api_id']}")
                report_content.append(f"    Pattern: {detail.get('matched_api_id', 'N/A')}")
                report_content.append(f"    Input: {detail['input_modalities']}")
                report_content.append(f"    Output: {detail['output_modalities']}")
                report_content.append("")
        
        # Unique model matches
        if unique_matches > 0:
            report_content.append("=== UNIQUE MODEL MATCHES ===\n")
            for i, detail in enumerate([d for d in self.matching_stats['match_details'] if d['match_priority'] == 5], 1):
                report_content.append(f"{i:2d}. {detail['api_id']}")
                report_content.append(f"    Input: {detail['input_modalities']}")
                report_content.append(f"    Output: {detail['output_modalities']}")
                report_content.append("")
                
        # No matches
        if no_matches > 0:
            report_content.append("=== NO MATCHES ===\n")
            for i, detail in enumerate([d for d in self.matching_stats['match_details'] if d['match_priority'] == 0], 1):
                report_content.append(f"{i:2d}. {detail['api_id']}")
        
        # Save report
        try:
            with open('D-enriched-modalities-report.txt', 'w') as f:
                f.write('\n'.join(report_content))
            print(f"✅ Enrichment report saved to D-enriched-modalities-report.txt")
        except Exception as e:
            print(f"❌ Error saving enrichment report: {e}")

    def run_enrichment_pipeline(self) -> None:
        """Run the complete modality enrichment pipeline"""
        print("=== Google Models Modality Enrichment Pipeline ===")
        
        # Load data files
        if not self.load_data_files():
            print("❌ Cannot proceed without input data files")
            return
            
        # Enrich models with modality data
        self.enrich_models()
        
        # Save results
        self.save_enriched_models()
        self.generate_enrichment_report()
        
        # Print summary
        print(f"\n=== Enrichment Summary ===")
        print(f"Priority 1 Matches: {self.matching_stats['priority_1_matches']}")
        print(f"Priority 2 Matches: {self.matching_stats['priority_2_matches']}")
        print(f"Embedding Matches: {self.matching_stats['embedding_matches']}")
        print(f"Gemma Pattern Matches: {self.matching_stats['gemma_matches']}")
        print(f"Unique Model Matches: {self.matching_stats['unique_matches']}")
        print(f"No Matches: {self.matching_stats['no_matches']}")
        total_success = self.matching_stats['priority_1_matches'] + self.matching_stats['priority_2_matches'] + self.matching_stats['embedding_matches'] + self.matching_stats['gemma_matches'] + self.matching_stats['unique_matches']
        print(f"Total Success Rate: {total_success/self.matching_stats['total_models']*100:.1f}%")

if __name__ == "__main__":
    enricher = ModalityEnrichment()
    enricher.run_enrichment_pipeline()