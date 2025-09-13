#!/usr/bin/env python3
"""
Final Database Schema Creation
Merges provider, modality, and license data into final database schema

Input Files:
- P-provider-enriched.json (primary data source)
- O-standardized-modalities.json (modality data)
- M-final-license-list.json (license data)
- 01_api_configuration.json (API metadata)
- 10_timestamp_patterns.json (timestamp formatting)

Output: Q-created-db-schema.json + CSV + human readable report
"""

import json
import os
import sys
import csv
from datetime import datetime
from typing import Any, Dict, List

def load_provider_data() -> List[Dict[str, Any]]:
    """Load provider enriched data from Stage-P"""
    input_file = 'P-provider-enriched.json'
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            models = json.load(f)
        print(f"✓ Loaded {len(models)} models from: {input_file}")
        return models
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load provider data from {input_file}: {error}")
        return []

def load_modality_data() -> Dict[str, Dict[str, Any]]:
    """Load standardized modality data from Stage-O"""
    input_file = 'O-standardized-modalities.json'
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            models = json.load(f)
        
        # Create lookup index by model ID
        modality_index = {}
        for model in models:
            model_id = model.get('id', '')
            if model_id:
                modality_index[model_id] = model
        
        print(f"✓ Loaded {len(modality_index)} models with modalities from: {input_file}")
        return modality_index
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load modality data from {input_file}: {error}")
        return {}

def load_license_data() -> Dict[str, Dict[str, Any]]:
    """Load license data from Stage-M"""
    input_file = 'M-final-license-list.json'
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            models = json.load(f)
        
        # Create lookup index by model ID
        license_index = {}
        for model in models:
            model_id = model.get('id', '')
            if model_id:
                license_index[model_id] = model
        
        print(f"✓ Loaded {len(license_index)} models with licenses from: {input_file}")
        return license_index
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load license data from {input_file}: {error}")
        return {}

def load_api_configuration() -> Dict[str, Any]:
    """Load API configuration"""
    config_file = '01_api_configuration.json'
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Loaded API configuration from: {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load API configuration from {config_file}: {error}")
        return {}

def load_database_schema() -> Dict[str, Any]:
    """Load database schema definition"""
    schema_file = '09_database_schema.json'
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        print(f"✓ Loaded database schema from: {schema_file}")
        return schema
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load database schema from {schema_file}: {error}")
        return {}

def load_field_mapping() -> Dict[str, Any]:
    """Load field mapping configuration"""
    mapping_file = '10_field_mapping.json'

    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        print(f"✓ Loaded field mapping from: {mapping_file}")
        return mapping
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: Failed to load field mapping from {mapping_file}: {error}")
        return {}

def generate_iso_timestamp() -> str:
    """Generate ISO timestamp in the format specified by 10_timestamp_patterns.json"""
    return datetime.now().isoformat() + '+00:00'

def create_database_record(provider_model: Dict[str, Any],
                          modality_data: Dict[str, Any],
                          license_data: Dict[str, Any],
                          api_config: Dict[str, Any],
                          field_mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Create a single database record from merged data sources"""
    
    # Get timestamp
    current_timestamp = generate_iso_timestamp()
    
    # Create database record according to schema
    db_record = {
        # Database managed field
        'id': '',  # Database will auto-generate
        
        # Provider information (from Stage P)
        'inference_provider': provider_model.get('inference_provider', ''),
        'model_provider': provider_model.get('model_provider', ''),
        'human_readable_name': provider_model.get('clean_model_name', ''),
        'model_provider_country': provider_model.get('model_provider_country', ''),
        'official_url': provider_model.get('official_url', ''),
        
        # Modality information (from Stage O)
        'input_modalities': modality_data.get('standardized_input_modalities', ''),
        'output_modalities': modality_data.get('standardized_output_modalities', ''),
        
        # License information (from Stage M)
        'license_info_text': license_data.get('license_info_text', ''),
        'license_info_url': license_data.get('license_info_url', ''),
        'license_name': license_data.get('license_name', ''),
        'license_url': license_data.get('license_url', ''),
        
        # API configuration (from 01_api_configuration.json)
        'rate_limits': api_config.get('rate_limits', {}).get('openrouter_default', ''),
        'provider_api_access': api_config.get('api_access_urls', {}).get('openrouter', ''),
        
        # Timestamps
        'created_at': current_timestamp,
        'updated_at': current_timestamp
    }
    
    return db_record

def create_final_database_data(provider_models: List[Dict[str, Any]], 
                               modality_index: Dict[str, Dict[str, Any]],
                               license_index: Dict[str, Dict[str, Any]],
                               api_config: Dict[str, Any],
                               field_mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create final database data by merging all data sources using field mapping"""
    
    database_records = []
    
    print(f"Creating database records for {len(provider_models)} models...")
    
    # Statistics tracking
    modality_matched = 0
    license_matched = 0
    modality_missing = []
    license_missing = []
    
    for provider_model in provider_models:
        model_id = provider_model.get('id', '')
        
        # Get modality data
        modality_data = modality_index.get(model_id, {})
        if modality_data:
            modality_matched += 1
        else:
            modality_missing.append(model_id)
        
        # Get license data
        license_data = license_index.get(model_id, {})
        if license_data:
            license_matched += 1
        else:
            license_missing.append(model_id)
        
        # Create database record using field mapping
        db_record = create_database_record(provider_model, modality_data, license_data, api_config, field_mapping)
        database_records.append(db_record)
    
    print(f"✓ Database record creation complete")
    print(f"  Total records: {len(database_records)}")
    print(f"  Modality matches: {modality_matched}/{len(provider_models)}")
    print(f"  License matches: {license_matched}/{len(provider_models)}")
    
    if modality_missing:
        print(f"  Modality misses: {len(modality_missing)} models")
        print(f"  Sample missing: {modality_missing[:5]}")
    
    if license_missing:
        print(f"  License misses: {len(license_missing)} models")
        print(f"  Sample missing: {license_missing[:5]}")
    
    return database_records

def save_database_json(database_records: List[Dict[str, Any]]) -> str:
    """Save database records to JSON file"""
    output_file = 'Q-created-db-data.json'
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(database_records, f, indent=2)
        print(f"✓ Saved database records to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save to {output_file}: {error}")
        return ""

def save_database_csv(database_records: List[Dict[str, Any]], db_schema: Dict[str, Any]) -> str:
    """Save database records to CSV file using schema field order"""
    output_file = 'Q-created-db-data.csv'
    
    try:
        schema_fields = db_schema.get('schema_fields', [])
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=schema_fields)
            writer.writeheader()
            
            for record in database_records:
                # Ensure all schema fields are present in the correct order
                ordered_record = {}
                for field in schema_fields:
                    ordered_record[field] = record.get(field, '')
                writer.writerow(ordered_record)
        
        print(f"✓ Saved database CSV to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save CSV to {output_file}: {error}")
        return ""

def save_database_txt(database_records: List[Dict[str, Any]]) -> str:
    """Save database records to human-readable TXT file with data quality analysis"""
    output_file = 'Q-db-data-quality-report.txt'
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("CREATED DATABASE SCHEMA - DATA QUALITY REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Data Quality Analysis
            missing_data = {
                'model_provider': [],
                'human_readable_name': [],
                'model_provider_country': [],
                'official_url': [],
                'input_modalities': [],
                'output_modalities': [],
                'license_info_text': [],
                'license_info_url': [],
                'license_name': [],
                'license_url': [],
                'rate_limits': [],
                'provider_api_access': []
            }
            
            unknown_values = {
                'model_provider': [],
                'license_name': []
            }
            
            # Analyze data quality
            for record in database_records:
                model_name = record.get('human_readable_name', 'Unknown')
                
                # Check for missing/empty values
                for field in missing_data.keys():
                    value = record.get(field, '').strip()
                    if not value:
                        missing_data[field].append(model_name)
                
                # Check for "Unknown" values
                if record.get('model_provider', '').strip().lower() in ['unknown', 'not found']:
                    unknown_values['model_provider'].append(model_name)
                
                if record.get('license_name', '').strip().lower() in ['unknown', 'not found']:
                    unknown_values['license_name'].append(model_name)
            
            # DATA QUALITY ISSUES SECTION
            f.write("DATA QUALITY ISSUES:\n")
            f.write("=" * 50 + "\n\n")
            
            # Missing/Empty Values Report
            f.write("MISSING OR EMPTY VALUES:\n")
            f.write("-" * 30 + "\n")
            has_missing = False
            for field, models in missing_data.items():
                if models:
                    has_missing = True
                    f.write(f"\n{field.upper().replace('_', ' ')} ({len(models)} models):\n")
                    for model in sorted(models):
                        f.write(f"  - {model}\n")
            
            if not has_missing:
                f.write("✓ No missing or empty values found\n")
            f.write("\n")
            
            # Unknown Values Report
            f.write("UNKNOWN OR 'NOT FOUND' VALUES:\n")
            f.write("-" * 30 + "\n")
            has_unknown = False
            for field, models in unknown_values.items():
                if models:
                    has_unknown = True
                    f.write(f"\n{field.upper().replace('_', ' ')} ({len(models)} models):\n")
                    for model in sorted(models):
                        f.write(f"  - {model}\n")
            
            if not has_unknown:
                f.write("✓ No unknown values found\n")
            f.write("\n")
            
            # Summary Statistics
            total_models = len(database_records)
            f.write("DATA QUALITY SUMMARY:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total models: {total_models}\n")
            
            for field, models in missing_data.items():
                if models:
                    percentage = (len(models) / total_models) * 100
                    f.write(f"Missing {field.replace('_', ' ')}: {len(models)} ({percentage:.1f}%)\n")
            
            for field, models in unknown_values.items():
                if models:
                    percentage = (len(models) / total_models) * 100
                    f.write(f"Unknown {field.replace('_', ' ')}: {len(models)} ({percentage:.1f}%)\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
            
            # COMPLETE MODEL RECORDS SECTION
            f.write("COMPLETE MODEL RECORDS:\n")
            f.write("=" * 50 + "\n\n")
            
            # Sort models by provider, then name for organized output
            sorted_models = sorted(
                database_records,
                key=lambda x: (x.get('model_provider', ''),
                              x.get('human_readable_name', ''))
            )
            
            for i, record in enumerate(sorted_models, 1):
                f.write(f"{i:3d}. {record.get('human_readable_name', 'Unknown')}\n")
                f.write(f"     Provider           : {record.get('model_provider', '')} ({record.get('model_provider_country', '')})\n")
                f.write(f"     Modalities         : {record.get('input_modalities', '')} → {record.get('output_modalities', '')}\n")
                f.write(f"     License            : {record.get('license_name', '')}\n")
                f.write(f"     License Info       : {record.get('license_info_text', '')}\n")
                f.write(f"     License URL        : {record.get('license_url', '')}\n")
                f.write(f"     Official URL       : {record.get('official_url', '')}\n")
                f.write(f"     Rate Limits        : {record.get('rate_limits', '')}\n")
                f.write(f"     Provider API Access: {record.get('provider_api_access', '')}\n")
                
                if i < len(sorted_models):
                    f.write("\n")
        
        print(f"✓ Saved data quality report to: {output_file}")
        return output_file
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save TXT to {output_file}: {error}")
        return ""

def generate_database_report(database_records: List[Dict[str, Any]]) -> str:
    """Generate human readable report for database records"""
    report_file = 'Q-created-db-schema-report.txt'
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("CREATED DATABASE SCHEMA REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"  Total database records: {len(database_records)}\n")
            f.write(f"  Input sources:\n")
            f.write(f"    - P-provider-enriched.json (primary data)\n")
            f.write(f"    - O-standardized-modalities.json (modalities)\n")
            f.write(f"    - M-final-license-list.json (licenses)\n")
            f.write(f"    - 01_api_configuration.json (API metadata)\n")
            f.write(f"  Processor: Q_create_db_schema.py\n")
            f.write(f"  Output: Q-created-db-schema.json + CSV\n\n")
            
            # Field distribution analysis
            provider_counts = {}
            country_counts = {}
            license_counts = {}
            modality_input_counts = {}
            modality_output_counts = {}
            
            for record in database_records:
                # Provider distribution
                provider = record.get('model_provider', '')
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
                
                # Country distribution
                country = record.get('model_provider_country', '')
                country_counts[country] = country_counts.get(country, 0) + 1
                
                # License distribution
                license_name = record.get('license_name', '')
                license_counts[license_name] = license_counts.get(license_name, 0) + 1
                
                # Input modalities
                input_mod = record.get('input_modalities', '')
                modality_input_counts[input_mod] = modality_input_counts.get(input_mod, 0) + 1
                
                # Output modalities
                output_mod = record.get('output_modalities', '')
                modality_output_counts[output_mod] = modality_output_counts.get(output_mod, 0) + 1
            
            # Provider distribution
            f.write(f"MODEL PROVIDER DISTRIBUTION:\n")
            sorted_providers = sorted(provider_counts.items(), key=lambda x: (-x[1], x[0]))
            for provider, count in sorted_providers:
                display_provider = provider if provider else "(empty)"
                f.write(f"  {count:2d} models: {display_provider}\n")
            f.write(f"\nTotal unique providers: {len(provider_counts)}\n\n")
            
            # Country distribution
            f.write(f"COUNTRY DISTRIBUTION:\n")
            sorted_countries = sorted(country_counts.items(), key=lambda x: (-x[1], x[0]))
            for country, count in sorted_countries:
                display_country = country if country else "(empty)"
                f.write(f"  {count:2d} models: {display_country}\n")
            f.write(f"\nTotal unique countries: {len(country_counts)}\n\n")
            
            # License distribution
            f.write(f"LICENSE DISTRIBUTION:\n")
            sorted_licenses = sorted(license_counts.items(), key=lambda x: (-x[1], x[0]))
            for license_name, count in sorted_licenses:
                display_license = license_name if license_name else "(empty)"
                f.write(f"  {count:2d} models: {display_license}\n")
            f.write(f"\nTotal unique licenses: {len(license_counts)}\n\n")
            
            # Input modalities distribution
            f.write(f"INPUT MODALITIES DISTRIBUTION:\n")
            sorted_input_mods = sorted(modality_input_counts.items(), key=lambda x: (-x[1], x[0]))
            for modality, count in sorted_input_mods:
                display_modality = modality if modality else "(empty)"
                f.write(f"  {count:2d} models: {display_modality}\n")
            f.write(f"\nTotal unique input modality types: {len(modality_input_counts)}\n\n")
            
            # Output modalities distribution
            f.write(f"OUTPUT MODALITIES DISTRIBUTION:\n")
            sorted_output_mods = sorted(modality_output_counts.items(), key=lambda x: (-x[1], x[0]))
            for modality, count in sorted_output_mods:
                display_modality = modality if modality else "(empty)"
                f.write(f"  {count:2d} models: {display_modality}\n")
            f.write(f"\nTotal unique output modality types: {len(modality_output_counts)}\n\n")
            
            # Detailed model listings
            f.write("DETAILED CREATED DATABASE SCHEMA:\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort models by provider, then name
            sorted_models = sorted(
                database_records,
                key=lambda x: (x.get('model_provider', ''),
                              x.get('human_readable_name', ''))
            )
            
            for i, record in enumerate(sorted_models, 1):
                f.write(f"RECORD {i}: {record.get('human_readable_name', 'Unknown')}\n")
                f.write("-" * 50 + "\n")
                
                # Database schema field order
                f.write(f"  ID: {record.get('id', '')}\n")
                f.write(f"  Inference Provider: {record.get('inference_provider', '')}\n")
                f.write(f"  Model Provider: {record.get('model_provider', '')}\n")
                f.write(f"  Human Readable Name: {record.get('human_readable_name', '')}\n")
                f.write(f"  Model Provider Country: {record.get('model_provider_country', '')}\n")
                f.write(f"  Official URL: {record.get('official_url', '')}\n")
                f.write(f"  Input Modalities: {record.get('input_modalities', '')}\n")
                f.write(f"  Output Modalities: {record.get('output_modalities', '')}\n")
                f.write(f"  License Info Text: {record.get('license_info_text', '')}\n")
                f.write(f"  License Info URL: {record.get('license_info_url', '')}\n")
                f.write(f"  License Name: {record.get('license_name', '')}\n")
                f.write(f"  License URL: {record.get('license_url', '')}\n")
                f.write(f"  Rate Limits: {record.get('rate_limits', '')}\n")
                f.write(f"  Provider API Access: {record.get('provider_api_access', '')}\n")
                f.write(f"  Created At: {record.get('created_at', '')}\n")
                f.write(f"  Updated At: {record.get('updated_at', '')}\n")
                
                # Add separator between models
                if i < len(sorted_models):
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    f.write("\n")
        
        print(f"✓ Database report saved to: {report_file}")
        return report_file
        
    except (IOError, TypeError) as error:
        print(f"ERROR: Failed to save report to {report_file}: {error}")
        return ""

def main():
    """Main execution function"""
    print("Final Database Schema Creation")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Load all data sources
    provider_models = load_provider_data()
    if not provider_models:
        print("No provider data loaded")
        return False
    
    modality_index = load_modality_data()
    license_index = load_license_data()
    api_config = load_api_configuration()
    db_schema = load_database_schema()
    field_mapping = load_field_mapping()
    
    if not db_schema:
        print("No database schema loaded")
        return False
    
    if not field_mapping:
        print("No field mapping loaded")
        return False
    
    # Create database records using field mapping
    database_records = create_final_database_data(
        provider_models, modality_index, license_index, api_config, field_mapping
    )
    
    if not database_records:
        print("No database records created")
        return False
    
    # Save outputs
    json_success = save_database_json(database_records)
    txt_success = save_database_txt(database_records)
    report_success = generate_database_report(database_records)

    if json_success and txt_success and report_success:
        print("="*60)
        print("FINAL DATABASE SCHEMA CREATION COMPLETE")
        print(f"Total records created: {len(database_records)}")
        print(f"JSON output: {json_success}")
        print(f"TXT output: {txt_success}")
        print(f"Report output: {report_success}")
        print(f"Completed at: {datetime.now().isoformat()}")
        return True
    else:
        print("FINAL DATABASE SCHEMA CREATION FAILED")
        return False

if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)