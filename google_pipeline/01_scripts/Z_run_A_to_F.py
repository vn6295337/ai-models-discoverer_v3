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
                    '../02_outputs/A-api-models.json'
                ]
            },
            {
                'stage': 'Stage 2',
                'name': 'Model Filtering',
                'script': 'B_filter_models.py', 
                'description': 'Filter models based on production criteria',
                'inputs': ['../02_outputs/A-api-models.json'],
                'outputs': [
                    '../02_outputs/B-filtered-models.json',
                    '../02_outputs/B-filtered-models-report.txt'
                ]
            },
            {
                'stage': 'Stage 3',
                'name': 'Modality Scraping',
                'script': 'C_scrape_modalities.py',
                'description': 'Scrape modalities from Google documentation',
                'outputs': ['../02_outputs/C-scrapped-modalities.json']
            },
            {
                'stage': 'Stage 4', 
                'name': 'Modality Enrichment',
                'script': 'D_enrich_modalities.py',
                'description': 'Enrich models with modality data and patterns',
                'inputs': [
                    '../02_outputs/B-filtered-models.json',
                    '../02_outputs/C-scrapped-modalities.json'
                ],
                'outputs': [
                    '../02_outputs/D-enriched-modalities.json',
                    '../02_outputs/D-enriched-modalities-report.txt'
                ]
            },
            {
                'stage': 'Stage 5',
                'name': 'Data Normalization',
                'script': 'E_create_db_data.py',
                'description': 'Normalize data for database schema compliance',
                'inputs': [
                    '../02_outputs/D-enriched-modalities.json'
                ],
                'outputs': [
                    '../02_outputs/E-created-db-data.json',
                    '../02_outputs/E-created-db-data-report.txt'
                ]
            },
            {
                'stage': 'Stage 6',
                'name': 'Pipeline Comparison',
                'script': 'F_compare_pipeline_with_supabase.py',
                'description': 'Compare pipeline output with Supabase data',
                'inputs': [
                    '../02_outputs/E-created-db-data.json'
                ],
                'outputs': [
                    '../02_outputs/F-comparison-report.txt'
                ]
            }
        ]

    def validate_dependencies(self) -> bool:
        """Validate that all required configuration files exist"""
        # Use absolute path relative to script location for reliable resolution
        script_dir = Path(__file__).parent  # Always points to 01_scripts/
        config_dir = script_dir.parent / "03_configs"  # Always points to google_pipeline/03_configs/

        print(f"DEBUG: Script dir: {script_dir}")
        print(f"DEBUG: Config dir: {config_dir}")
        print(f"DEBUG: Config dir exists: {config_dir.exists()}")

        required_configs = [
            config_dir / "01_google_models_licenses.json",
            config_dir / "02_modality_standardization.json",
            config_dir / "03_models_filtering_rules.json",
            config_dir / "05_timestamp_patterns.json",
            config_dir / "04_embedding_models.json",
            config_dir / "06_unique_models_modalities.json",
            config_dir / "07_name_standardization_rules.json"
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
        """Validate that expected output files were created and are valid"""
        if not stage_config['outputs']:
            return True  # No file outputs to validate (e.g., database operations)

        missing_outputs = []
        invalid_outputs = []

        for output_file in stage_config['outputs']:
            file_path = Path(output_file)

            # Check if file exists
            if not file_path.exists():
                missing_outputs.append(output_file)
                continue

            # Check file size (empty files are suspicious)
            if file_path.stat().st_size == 0:
                invalid_outputs.append(f"{output_file} (empty file)")
                continue

            # For JSON files, try to validate JSON structure
            if output_file.endswith('.json'):
                try:
                    with open(file_path, 'r') as f:
                        json.load(f)
                except (json.JSONDecodeError, Exception) as e:
                    invalid_outputs.append(f"{output_file} (invalid JSON: {str(e)})")

        issues_found = False
        if missing_outputs:
            print(f"⚠️  {stage_config['stage']} - Missing expected output files:")
            for output_file in missing_outputs:
                print(f"   - {output_file}")
            issues_found = True

        if invalid_outputs:
            print(f"⚠️  {stage_config['stage']} - Invalid output files:")
            for issue in invalid_outputs:
                print(f"   - {issue}")
            issues_found = True

        return not issues_found

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
                    return True, duration, result.stdout
                else:
                    error_msg = f"Script completed but failed to generate expected output files"
                    print(f"❌ {stage_config['stage']} failed: {error_msg}")
                    if result.stderr:
                        print("Script stderr:")
                        print(result.stderr)
                    return False, duration, error_msg
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

    def setup_environment(self) -> bool:
        """Setup local development environment"""
        print("\n" + "=" * 60)
        print("🔧 ENVIRONMENT SETUP")
        print("=" * 60)

        try:
            # Check if we're in the right directory
            if not os.path.exists("../03_configs"):
                print("⚠️ Config directory not found, but continuing...")
            else:
                print("✅ Configuration directory found")

            # Check if output directory exists
            output_dir = "../02_outputs"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"📁 Created output directory: {output_dir}")
            else:
                print(f"✅ Output directory exists: {output_dir}")

            # Check requirements.txt (optional for Google pipeline)
            script_dir = Path(__file__).parent
            requirements_file = script_dir.parent / "03_configs" / "requirements.txt"
            if requirements_file.exists():
                print(f"✅ Requirements file found: {requirements_file}")
            else:
                print(f"⚠️ No requirements.txt found at {requirements_file}, skipping dependency installation")

            print("\n🎉 Environment setup completed successfully!")
            return True

        except Exception as e:
            print(f"💥 Environment setup failed: {str(e)}")
            return False

    def get_user_script_selection(self) -> List[Dict]:
        """Get user selection for which scripts to run"""
        script_map = {chr(65 + i): stage for i, stage in enumerate(self.pipeline_stages)}

        print("\n" + "=" * 60)
        print("📋 SCRIPT SELECTION MENU")
        print("=" * 60)
        print("Available scripts:")
        for i, stage in enumerate(self.pipeline_stages):
            letter = chr(65 + i)  # A, B, C, etc.
            print(f"  {letter}: {stage['script']}")

        print("\nExecution options:")
        print("  1. Run all scripts (A to F)")
        print("  2. Run script range (e.g., C to E)")
        print("  3. Run specific scripts (e.g., A, C, F)")

        while True:
            choice = input("\nEnter your choice (1/2/3): ").strip()

            if choice == "1":
                return self.pipeline_stages

            elif choice == "2":
                while True:
                    range_input = input("Enter range (e.g., 'C E' for C to E): ").strip().upper()
                    try:
                        start_letter, end_letter = range_input.split()
                        start_idx = ord(start_letter) - 65
                        end_idx = ord(end_letter) - 65

                        if 0 <= start_idx <= end_idx < len(self.pipeline_stages):
                            selected = self.pipeline_stages[start_idx:end_idx + 1]
                            print(f"Selected scripts: {[chr(65 + start_idx + i) for i in range(len(selected))]}")
                            return selected
                        else:
                            print("Invalid range. Please try again.")
                    except ValueError:
                        print("Invalid format. Use format like 'C E' for range.")

            elif choice == "3":
                while True:
                    scripts_input = input("Enter script letters (e.g., 'A C F' or 'B D'): ").strip().upper()
                    try:
                        letters = scripts_input.split()
                        selected = []
                        indices = []

                        for letter in letters:
                            if letter in script_map:
                                idx = ord(letter) - 65
                                indices.append(idx)
                                selected.append(script_map[letter])
                            else:
                                print(f"Invalid script letter: {letter}")
                                break
                        else:
                            # Sort by original pipeline order
                            sorted_pairs = sorted(zip(indices, selected))
                            selected = [script for _, script in sorted_pairs]
                            print(f"Selected scripts: {[chr(65 + idx) for idx, _ in sorted_pairs]}")
                            return selected
                    except ValueError:
                        print("Invalid format. Use format like 'A C F' for specific scripts.")
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    def run_pipeline(self, start_from_stage: Optional[str] = None, interactive: bool = True) -> bool:
        """Execute the complete pipeline or start from a specific stage"""
        print("=" * 60)
        print("🚀 GOOGLE PIPELINE ORCHESTRATOR")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # ===============================================
        # ENVIRONMENT SETUP SECTION
        # ===============================================
        print("\n🔧 Setting up local development environment...")
        if not self.setup_environment():
            print("💥 Pipeline aborted due to environment setup failure")
            return False

        # ===============================================
        # PIPELINE EXECUTION SECTION
        # ===============================================
        print("\n📍 SEQUENTIAL PIPELINE EXECUTION")
        print("Flow: A → B → C → D → E → F")
        print("Note: G & H deployment scripts available via manual workflow trigger")

        # Validate dependencies
        if not self.validate_dependencies():
            print("\n❌ Pipeline aborted due to missing dependencies")
            return False

        # Get user selection for which scripts to run
        selected_stages = self.get_user_script_selection()

        # Display selected scripts and ask for confirmation
        print(f"\n📋 SELECTED SCRIPTS ({len(selected_stages)} total):")
        for i, stage in enumerate(selected_stages, 1):
            original_idx = self.pipeline_stages.index(stage) + 1
            letter = chr(64 + original_idx)  # A, B, C, etc.
            print(f"  {i:2d}. {letter}: {stage['script']}")

        # Ask for confirmation
        while True:
            confirm = input(f"\nProceed with executing {len(selected_stages)} script(s)? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                break
            elif confirm in ['n', 'no']:
                print("Pipeline execution cancelled.")
                return False
            else:
                print("Please enter 'y' or 'n'.")

        # Clean output directory if starting from Stage 1
        if selected_stages and selected_stages[0]['stage'] == 'Stage 1':
            self.clean_output_directory()

        self.pipeline_start_time = time.time()

        # Execute selected scripts
        total_stages = len(selected_stages)
        for i, stage_config in enumerate(selected_stages, 1):
            original_idx = self.pipeline_stages.index(stage_config) + 1
            letter = chr(64 + original_idx)  # A, B, C, etc.
            print(f"\n📍 STAGE {i:2d}/{total_stages}: {letter} - {stage_config['script']}")

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
                print(f"\n💥 Pipeline stopped due to failure in {stage_config['script']}")
                break

        # Generate final report
        self.generate_pipeline_report()

        total_duration = time.time() - self.pipeline_start_time
        if self.failed_stage:
            print(f"\n❌ Pipeline FAILED at {self.failed_stage} (Total time: {total_duration:.1f}s)")
            return False
        else:
            print("\n" + "=" * 60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"Total execution time: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
            print(f"All {len(self.stage_results)} selected scripts executed successfully")
            if len(selected_stages) == len(self.pipeline_stages):
                print("Full pipeline (A to F) completed")
            else:
                executed_letters = [chr(64 + self.pipeline_stages.index(stage) + 1) for stage in selected_stages]
                print(f"Executed scripts: {', '.join(executed_letters)}")
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            # Create timestamp tracking file
            self.create_completion_timestamp()

            print(f"\n📄 Final outputs:")
            print(f"   • ../02_outputs/E-created-db-data.json (database-ready)")
            print(f"   • ../02_outputs/E-created-db-data-report.txt (human-readable)")
            print(f"   • ../02_outputs/F-comparison-report.txt (pipeline vs supabase comparison)")
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
        timestamp_file = "../02_outputs/last-run.txt"
        try:
            # Ensure ../02_outputs directory exists
            Path("../02_outputs").mkdir(exist_ok=True)

            with open(timestamp_file, 'w') as f:
                f.write(f"Google Pipeline completed: {datetime.now().strftime('%a %b %d %H:%M:%S UTC %Y')}\n")
                f.write(f"Local execution: {datetime.now().isoformat()}\n")
                f.write(f"Pipeline duration: {time.time() - self.pipeline_start_time:.1f} seconds\n")

            print(f"✅ Completion timestamp saved to: {timestamp_file}")
        except Exception as e:
            print(f"⚠️  Could not save completion timestamp: {e}")

    def clean_output_directory(self) -> None:
        """Clean ../02_outputs directory of old output files"""
        output_dir = Path("../02_outputs")

        try:
            if not output_dir.exists():
                print("📁 Creating ../02_outputs directory")
                output_dir.mkdir(exist_ok=True)
                return

            # Files to clean (keep .gitkeep)
            files_to_remove = []
            patterns_to_clean = [
                "A-api-models.json", "A-api-models-report.txt",
                "B-filtered-models.json", "B-filtered-models-report.txt",
                "C-scrapped-modalities.json", "C-scrapped-modalities-report.txt",
                "D-enriched-modalities.json", "D-enriched-modalities-report.txt",
                "E-created-db-data.json", "E-created-db-data-report.txt",
                "F-comparison-report.txt",
                "last-run.txt", "Z-pipeline-report.txt"
            ]

            for pattern in patterns_to_clean:
                file_path = output_dir / pattern
                if file_path.exists():
                    files_to_remove.append(file_path)

            if files_to_remove:
                print(f"🧹 Cleaning {len(files_to_remove)} old output files from ../02_outputs/")
                for file_path in files_to_remove:
                    file_path.unlink()
                    print(f"   Removed: {file_path.name}")
            else:
                print("✅ ../02_outputs directory is clean")

        except Exception as e:
            print(f"⚠️  Could not clean output directory: {e}")
            print("Continuing with pipeline execution...")

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
  python Z_run_A_to_F.py --interactive      # Interactive stage selection
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
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode for stage selection'
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

    # Detect if running in non-interactive environment (like GitHub Actions)
    import sys
    is_interactive_env = sys.stdin.isatty()

    if args.interactive and is_interactive_env:
        # Explicit interactive mode and we're in a terminal
        success = orchestrator.run_pipeline(interactive=True)
    elif args.start:
        # Start from specific stage
        success = orchestrator.run_pipeline(
            start_from_stage=args.start,
            interactive=False
        )
    elif not is_interactive_env:
        # Non-interactive environment (GitHub Actions, etc.) - run all stages
        print("🤖 Non-interactive environment detected, running complete pipeline...")
        success = orchestrator.run_pipeline(interactive=False)
    else:
        # Interactive terminal environment, default to interactive mode
        success = orchestrator.run_pipeline(interactive=True
        )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()