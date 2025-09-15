#!/usr/bin/env python3
"""
Google Models Pipeline Orchestrator
===================================

Master script that executes the Google models discovery pipeline
in the correct logical order from Stage 1 through Stage 6 (complete pipeline with comparison).

Pipeline Flow:
1. Stage 1: API Data Extraction (A_fetch_api_models.py)
2. Stage 2: Model Filtering (B_filter_models.py)
3. Stage 3: Modality Scraping (C_scrape_modalities.py)
4. Stage 4: Modality Enrichment (D_enrich_modalities.py)
5. Stage 5: Data Normalization (E_create_db_data.py)

Final Output: E-normalization-report.csv (ready for database upload)

Features:
- Sequential execution with dependency validation
- Error handling and pipeline interruption on failures
- Progress tracking and detailed logging
- File existence validation between stages
- Execution time measurement per stage
- Comprehensive summary reporting
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class GooglePipelineOrchestrator:
    def __init__(self):
        self.pipeline_start_time = None
        self.stage_results = []
        self.failed_stage = None
        
        # Pipeline configuration
        self.pipeline_stages = [
            {
                'stage': 'Stage 1',
                'name': 'API Data Extraction',
                'script': 'A_fetch_api_models.py',
                'description': 'Extract comprehensive model list from Google API',
                'outputs': [
                    'pipeline-outputs/A-api-models.json'
                ]
            },
            {
                'stage': 'Stage 2',
                'name': 'Model Filtering',
                'script': 'B_filter_models.py', 
                'description': 'Filter models based on production criteria',
                'inputs': ['pipeline-outputs/A-api-models.json'],
                'outputs': [
                    'pipeline-outputs/B-filtered-models.json',
                    'pipeline-outputs/B-filtered-models-report.txt'
                ]
            },
            {
                'stage': 'Stage 3',
                'name': 'Modality Scraping',
                'script': 'C_scrape_modalities.py',
                'description': 'Scrape modalities from Google documentation',
                'outputs': ['pipeline-outputs/C-scrapped-modalities.json']
            },
            {
                'stage': 'Stage 4', 
                'name': 'Modality Enrichment',
                'script': 'D_enrich_modalities.py',
                'description': 'Enrich models with modality data and patterns',
                'inputs': [
                    'pipeline-outputs/B-filtered-models.json',
                    'pipeline-outputs/C-scrapped-modalities.json'
                ],
                'outputs': [
                    'pipeline-outputs/D-enriched-modalities.json',
                    'pipeline-outputs/D-enriched-modalities-report.txt'
                ]
            },
            {
                'stage': 'Stage 5',
                'name': 'Data Normalization',
                'script': 'E_create_db_data.py',
                'description': 'Normalize data for database schema compliance',
                'inputs': [
                    'pipeline-outputs/D-enriched-modalities.json'
                ],
                'outputs': [
                    'pipeline-outputs/E-created-db-data.json',
                    'pipeline-outputs/E-created-db-data-report.txt'
                ]
            },
            {
                'stage': 'Stage 6',
                'name': 'Pipeline Comparison',
                'script': 'F_compare_pipeline_with_supabase.py',
                'description': 'Compare pipeline output with Supabase data',
                'inputs': [
                    'pipeline-outputs/E-created-db-data.json'
                ],
                'outputs': [
                    'pipeline-outputs/F-comparison-report.txt'
                ]
            }
        ]

    def validate_dependencies(self) -> bool:
        """Validate that all required configuration files exist"""
        required_configs = [
            '01_google_models_licenses.json',
            '02_modality_standardization.json', 
            '03_models_filtering_rules.json',
            '05_timestamp_patterns.json',
            '04_embedding_models.json',
            '06_unique_models_modalities.json',
            '07_name_standardization_rules.json'
        ]
        
        missing_configs = []
        for config in required_configs:
            if not Path(config).exists():
                missing_configs.append(config)
        
        if missing_configs:
            print("❌ Missing required configuration files:")
            for config in missing_configs:
                print(f"   - {config}")
            return False
        
        print("✅ All configuration files present")
        return True

    def validate_stage_inputs(self, stage_config: Dict) -> bool:
        """Validate that required input files exist for a stage"""
        if 'inputs' not in stage_config:
            return True
            
        missing_inputs = []
        for input_file in stage_config['inputs']:
            if not Path(input_file).exists():
                missing_inputs.append(input_file)
        
        if missing_inputs:
            print(f"❌ {stage_config['stage']} - Missing required input files:")
            for input_file in missing_inputs:
                print(f"   - {input_file}")
            return False
            
        return True

    def validate_stage_outputs(self, stage_config: Dict) -> bool:
        """Validate that expected output files were created"""
        if not stage_config['outputs']:
            return True  # No file outputs to validate (e.g., database operations)
            
        missing_outputs = []
        for output_file in stage_config['outputs']:
            if not Path(output_file).exists():
                missing_outputs.append(output_file)
        
        if missing_outputs:
            print(f"⚠️  {stage_config['stage']} - Missing expected output files:")
            for output_file in missing_outputs:
                print(f"   - {output_file}")
            return False
            
        return True

    def execute_script(self, script_name: str, stage_config: Dict) -> Tuple[bool, float, str]:
        """Execute a Python script and return success status, duration, and output"""
        print(f"\n🔄 Executing {stage_config['stage']}: {stage_config['name']}")
        print(f"   Script: {script_name}")
        print(f"   Description: {stage_config['description']}")
        
        if not Path(script_name).exists():
            error_msg = f"Script {script_name} not found"
            print(f"❌ {error_msg}")
            return False, 0.0, error_msg
        
        # Validate inputs before execution
        if not self.validate_stage_inputs(stage_config):
            error_msg = f"Input validation failed for {stage_config['stage']}"
            return False, 0.0, error_msg
        
        start_time = time.time()
        try:
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {stage_config['stage']} completed successfully ({duration:.1f}s)")
                
                # Validate outputs after successful execution
                if self.validate_stage_outputs(stage_config):
                    print(f"✅ All expected outputs created for {stage_config['stage']}")
                else:
                    print(f"⚠️  Some outputs missing for {stage_config['stage']} (execution succeeded)")
                
                return True, duration, result.stdout
            else:
                error_msg = f"Script failed with return code {result.returncode}"
                print(f"❌ {stage_config['stage']} failed: {error_msg}")
                if result.stderr:
                    print("Error output:")
                    print(result.stderr)
                return False, duration, error_msg
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = f"Script timed out after {duration:.1f} seconds"
            print(f"❌ {stage_config['stage']} failed: {error_msg}")
            return False, duration, error_msg
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Execution error: {str(e)}"
            print(f"❌ {stage_config['stage']} failed: {error_msg}")
            return False, duration, error_msg

    def run_pipeline(self, start_from_stage: Optional[str] = None) -> bool:
        """Execute the complete pipeline or start from a specific stage"""
        print("=== Google Models Discovery Pipeline Orchestrator ===")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Validate dependencies
        if not self.validate_dependencies():
            print("\n❌ Pipeline aborted due to missing dependencies")
            return False
        
        self.pipeline_start_time = time.time()
        start_index = 0
        
        # Determine starting stage
        if start_from_stage:
            for i, stage_config in enumerate(self.pipeline_stages):
                if stage_config['stage'].lower() == start_from_stage.lower():
                    start_index = i
                    print(f"\n🎯 Starting from {stage_config['stage']}: {stage_config['name']}")
                    break
            else:
                print(f"\n❌ Stage '{start_from_stage}' not found")
                return False
        
        # Execute pipeline stages
        for i in range(start_index, len(self.pipeline_stages)):
            stage_config = self.pipeline_stages[i]
            
            success, duration, output = self.execute_script(
                stage_config['script'], 
                stage_config
            )
            
            # Record stage result
            stage_result = {
                'stage': stage_config['stage'],
                'name': stage_config['name'],
                'script': stage_config['script'],
                'success': success,
                'duration': duration,
                'output': output[:500] + "..." if len(output) > 500 else output
            }
            self.stage_results.append(stage_result)
            
            if not success:
                self.failed_stage = stage_config['stage']
                print(f"\n💥 Pipeline failed at {stage_config['stage']}")
                break
        
        # Generate final report
        self.generate_pipeline_report()
        
        total_duration = time.time() - self.pipeline_start_time
        if self.failed_stage:
            print(f"\n❌ Pipeline FAILED at {self.failed_stage} (Total time: {total_duration:.1f}s)")
            return False
        else:
            print(f"\n🎉 Pipeline completed successfully! All stages complete. (Total time: {total_duration:.1f}s)")

            # Create timestamp tracking file
            self.create_completion_timestamp()

            print(f"\n📄 Final outputs:")
            print(f"   • pipeline-outputs/E-created-db-data.json (database-ready)")
            print(f"   • pipeline-outputs/E-created-db-data-report.txt (human-readable)")
            print(f"   • pipeline-outputs/F-comparison-report.txt (pipeline vs supabase comparison)")
            print(f"📊 Ready for database upload using G_refresh_supabase_working_version.py")
            return True

    def generate_pipeline_report(self) -> None:
        """Generate comprehensive pipeline execution report"""
        report_content = []
        
        # Header
        report_content.append("=== GOOGLE MODELS PIPELINE EXECUTION REPORT ===")
        report_content.append(f"Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.pipeline_start_time:
            total_duration = time.time() - self.pipeline_start_time
            report_content.append(f"Total Pipeline Duration: {total_duration:.1f} seconds")
        
        report_content.append("")
        
        # Summary
        successful_stages = sum(1 for result in self.stage_results if result['success'])
        total_stages = len(self.stage_results)
        
        report_content.append("=== EXECUTION SUMMARY ===")
        report_content.append(f"Stages Executed: {total_stages}")
        report_content.append(f"Successful: {successful_stages}")
        report_content.append(f"Failed: {total_stages - successful_stages}")
        
        if self.failed_stage:
            report_content.append(f"Failed At: {self.failed_stage}")
        
        report_content.append("")
        
        # Stage Details
        report_content.append("=== STAGE EXECUTION DETAILS ===")
        for result in self.stage_results:
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            report_content.append(f"{result['stage']}: {result['name']}")
            report_content.append(f"  Script: {result['script']}")
            report_content.append(f"  Status: {status}")
            report_content.append(f"  Duration: {result['duration']:.1f}s")
            if not result['success']:
                report_content.append(f"  Error: {result['output']}")
            report_content.append("")
        
        # Save report
        report_filename = "Z-pipeline-report.txt"
        try:
            with open(report_filename, 'w') as f:
                f.write('\n'.join(report_content))
            print(f"📄 Pipeline report saved to: {report_filename}")
        except Exception as e:
            print(f"⚠️  Could not save pipeline report: {e}")

    def create_completion_timestamp(self) -> None:
        """Create timestamp file to track pipeline completion"""
        timestamp_file = "pipeline-outputs/last-run.txt"
        try:
            # Ensure pipeline-outputs directory exists
            Path("pipeline-outputs").mkdir(exist_ok=True)

            with open(timestamp_file, 'w') as f:
                f.write(f"Google Pipeline completed: {datetime.now().strftime('%a %b %d %H:%M:%S UTC %Y')}\n")
                f.write(f"Local execution: {datetime.now().isoformat()}\n")
                f.write(f"Pipeline duration: {time.time() - self.pipeline_start_time:.1f} seconds\n")

            print(f"✅ Completion timestamp saved to: {timestamp_file}")
        except Exception as e:
            print(f"⚠️  Could not save completion timestamp: {e}")

    def list_stages(self) -> None:
        """List all available pipeline stages"""
        print("=== Available Pipeline Stages ===")
        for stage_config in self.pipeline_stages:
            print(f"{stage_config['stage']}: {stage_config['name']}")
            print(f"  Script: {stage_config['script']}")
            print(f"  Description: {stage_config['description']}")
            print()

def main():
    """Main execution function with command line argument support"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Google Models Pipeline Orchestrator (Stages 1-6: Complete Pipeline with Comparison)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python Z_run_A_to_F.py                    # Run complete pipeline (Stages 1-6)
  python Z_run_A_to_F.py --start "Stage 3"  # Start from Stage 3
  python Z_run_A_to_F.py --list             # List all stages
        """
    )
    
    parser.add_argument(
        '--start',
        type=str,
        help='Start pipeline from specific stage (e.g., "Stage 2", "Stage 4")'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available pipeline stages and exit'
    )
    
    args = parser.parse_args()
    
    orchestrator = GooglePipelineOrchestrator()
    
    if args.list:
        orchestrator.list_stages()
        return
    
    success = orchestrator.run_pipeline(start_from_stage=args.start)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()