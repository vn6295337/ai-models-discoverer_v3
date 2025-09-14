#!/usr/bin/env python3
"""
Google Models Filter Script
Filters A-api-models-fetch.json through criteria in 03_model_filtering.json
and outputs to pipeline-outputs/B-filtered-models.json
"""

import json
import re
from typing import List, Dict, Any, Set

class GoogleModelsFilter:
    def __init__(self):
        self.filtering_config = {}
        self.filtered_models = []
        self.excluded_models = []
        
    def load_filtering_config(self) -> Dict[str, Any]:
        """Load filtering configuration from 03_models_filtering_rules.json"""
        try:
            with open('03_models_filtering_rules.json', 'r') as f:
                self.filtering_config = json.load(f)
                print(f"✅ Loaded filtering configuration from 03_models_filtering_rules.json")
                return self.filtering_config
        except FileNotFoundError:
            print("❌ 03_models_filtering_rules.json not found")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing 03_models_filtering_rules.json: {e}")
            return {}

    def load_input_models(self) -> List[Dict[str, Any]]:
        """Load models from A-api-models-fetch.json"""
        try:
            with open('pipeline-outputs/A-api-models.json', 'r') as f:
                models = json.load(f)
                print(f"✅ Loaded {len(models)} models from pipeline-outputs/A-api-models.json")
                return models
        except FileNotFoundError:
            print("❌ pipeline-outputs/A-api-models.json not found")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing pipeline-outputs/A-api-models.json: {e}")
            return []

    def should_exclude_model(self, model: Dict[str, Any]) -> tuple[bool, str]:
        """Check if model should be excluded based on filtering criteria"""
        if not self.filtering_config:
            return False, ""
            
        exclude_keywords = self.filtering_config.get('exclude_keywords', [])
        exclude_descriptions = self.filtering_config.get('exclude_descriptions', [])
        exclude_reasons = self.filtering_config.get('exclude_reasons', {})
        
        # Check model name, displayName, and description for exclusion keywords
        model_name = model.get('name', '').lower()
        display_name = model.get('displayName', '').lower()
        description = model.get('description', '').lower()
        
        # Check for keyword exclusions in name, display name, and description
        for keyword in exclude_keywords:
            keyword_lower = keyword.lower()
            # Use word boundaries and exclude "non-keyword" patterns
            import re
            
            # Check if keyword appears but not as "non-keyword"
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            non_pattern = r'\bnon-' + re.escape(keyword_lower) + r'\b'
            
            for text in [model_name, display_name, description]:
                if re.search(pattern, text) and not re.search(non_pattern, text):
                    reason = exclude_reasons.get(keyword, f"Contains excluded keyword: {keyword}")
                    return True, reason
        
        # Check for description-based exclusions
        for exclude_desc in exclude_descriptions:
            if exclude_desc in description:
                reason = exclude_reasons.get('billing_required', 'Model requires billing/payment - free models only')
                return True, reason
                
        return False, ""

    def should_include_model(self, model: Dict[str, Any]) -> tuple[bool, str]:
        """Check if model matches include patterns"""
        if not self.filtering_config:
            return True, "No filtering config - include all"
            
        include_patterns = self.filtering_config.get('include_patterns', {})
        include_descriptions = self.filtering_config.get('include_descriptions', {})
        
        model_name = model.get('name', '').lower()
        display_name = model.get('displayName', '').lower()
        description = model.get('description', '').lower()
        
        # Check all include pattern categories
        for category, patterns in include_patterns.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if (pattern_lower in model_name or 
                    pattern_lower in display_name or 
                    pattern_lower in description):
                    reason = include_descriptions.get(category, f"Matches pattern: {pattern}")
                    return True, reason
                    
        # If model doesn't match any specific patterns, include it (general models)
        return True, "General model - no exclusions apply"

    def filter_models(self, models: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Filter models based on configuration criteria"""
        filtered_models = []
        excluded_models = []
        
        print(f"\n=== Filtering {len(models)} models ===")
        
        for model in models:
            model_name = model.get('name', 'Unknown')
            display_name = model.get('displayName', 'Unknown')
            
            # First check exclusions
            should_exclude, exclude_reason = self.should_exclude_model(model)
            if should_exclude:
                excluded_info = {
                    'model': model,
                    'reason': exclude_reason,
                    'excluded_by': 'exclude_keywords'
                }
                excluded_models.append(excluded_info)
                print(f"❌ Excluded: {display_name} ({model_name}) - {exclude_reason}")
                continue
            
            # Then check inclusions
            should_include, include_reason = self.should_include_model(model)
            if should_include:
                filtered_info = {
                    'model': model,
                    'reason': include_reason,
                    'included_by': 'include_patterns'
                }
                filtered_models.append(filtered_info)
                print(f"✅ Included: {display_name} ({model_name}) - {include_reason}")
            else:
                excluded_info = {
                    'model': model,
                    'reason': "Does not match any include patterns",
                    'excluded_by': 'include_patterns'
                }
                excluded_models.append(excluded_info)
                print(f"❌ Excluded: {display_name} ({model_name}) - Does not match include patterns")
        
        return filtered_models, excluded_models

    def save_filtered_models(self, filtered_models: List[Dict[str, Any]]) -> None:
        """Save filtered models to pipeline-outputs/B-filtered-models.json"""
        # Extract just the model data without filtering metadata
        models_data = [item['model'] for item in filtered_models]
        
        try:
            with open('pipeline-outputs/B-filtered-models.json', 'w') as f:
                json.dump(models_data, f, indent=2)
            print(f"\n✅ Saved {len(models_data)} filtered models to pipeline-outputs/B-filtered-models.json")
        except Exception as e:
            print(f"❌ Error saving filtered models: {e}")

    def generate_filtering_report(self, filtered_models: List[Dict[str, Any]], excluded_models: List[Dict[str, Any]]) -> None:
        """Generate summary report of filtering results"""
        print(f"\n=== Filtering Summary ===")
        print(f"Total Input Models: {len(filtered_models) + len(excluded_models)}")
        print(f"Models Included: {len(filtered_models)}")
        print(f"Models Excluded: {len(excluded_models)}")
        print(f"Filtering Success Rate: {len(filtered_models)/(len(filtered_models) + len(excluded_models))*100:.1f}%")
        
        if excluded_models:
            print(f"\n=== Exclusion Breakdown ===")
            exclusion_reasons = {}
            for excluded in excluded_models:
                reason = excluded['reason']
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            
            for reason, count in sorted(exclusion_reasons.items()):
                print(f"  {count} models: {reason}")

    def save_txt_report(self, filtered_models: List[Dict[str, Any]], excluded_models: List[Dict[str, Any]]) -> None:
        """Save detailed filtering report to txt file"""
        report_content = []
        
        # Header
        report_content.append("=== GOOGLE MODELS FILTERING REPORT ===")
        report_content.append(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_content.append("")
        
        # Summary
        total_models = len(filtered_models) + len(excluded_models)
        report_content.append("=== SUMMARY ===")
        report_content.append(f"Total Input Models: {total_models}")
        report_content.append(f"Models Included: {len(filtered_models)}")
        report_content.append(f"Models Excluded: {len(excluded_models)}")
        report_content.append(f"Filtering Success Rate: {len(filtered_models)/total_models*100:.1f}%")
        report_content.append("")
        
        # Excluded Models (First)
        report_content.append("=== EXCLUDED MODELS ===")
        if excluded_models:
            for i, item in enumerate(excluded_models, 1):
                model = item['model']
                model_name = model.get('name', 'Unknown')
                # Extract just the model ID part after "models/"
                if model_name.startswith('models/'):
                    model_name = model_name[7:]  # Remove "models/" prefix
                report_content.append(f"{i:2d}. {model_name}")
        else:
            report_content.append("No models excluded.")
        report_content.append("")
        
        # Filtered Models (Included) - Second
        report_content.append("=== INCLUDED MODELS ===")
        if filtered_models:
            for i, item in enumerate(filtered_models, 1):
                model = item['model']
                model_name = model.get('name', 'Unknown')
                # Extract just the model ID part after "models/"
                if model_name.startswith('models/'):
                    model_name = model_name[7:]  # Remove "models/" prefix
                report_content.append(f"{i:2d}. {model_name}")
        else:
            report_content.append("No models included.")
        report_content.append("")
        
        # Exclusion Breakdown
        if excluded_models:
            report_content.append("=== EXCLUSION BREAKDOWN ===")
            exclusion_reasons = {}
            for excluded in excluded_models:
                reason = excluded['reason']
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            
            for reason, count in sorted(exclusion_reasons.items()):
                report_content.append(f"{count:2d} models: {reason}")
        
        # Write to file
        try:
            with open('pipeline-outputs/B-filtered-models-report.txt', 'w') as f:
                f.write('\n'.join(report_content))
            print(f"\n✅ Detailed filtering report saved to: pipeline-outputs/B-filtered-models-report.txt")
        except Exception as e:
            print(f"❌ Error saving filtering report: {e}")

    def run_filtering_pipeline(self) -> None:
        """Run the complete filtering pipeline"""
        print("=== Google Models Filtering Pipeline ===")
        
        # Load configuration
        config = self.load_filtering_config()
        if not config:
            print("❌ Cannot proceed without filtering configuration")
            return
        
        # Load input models
        models = self.load_input_models()
        if not models:
            print("❌ Cannot proceed without input models")
            return
        
        # Apply filters
        filtered_models, excluded_models = self.filter_models(models)
        
        # Save results
        self.save_filtered_models(filtered_models)
        
        # Generate reports
        self.generate_filtering_report(filtered_models, excluded_models)
        self.save_txt_report(filtered_models, excluded_models)
        
        # Store results for potential further processing
        self.filtered_models = filtered_models
        self.excluded_models = excluded_models

if __name__ == "__main__":
    filter_processor = GoogleModelsFilter()
    filter_processor.run_filtering_pipeline()