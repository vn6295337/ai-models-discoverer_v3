# Google AI Models Discovery Pipeline Documentation

## What This Pipeline Does (Simple Explanation)

**For Everyone**: This pipeline is like an automated research assistant that:
1. **Discovers** all available AI models from Google
2. **Filters** them to find only the stable, production-ready ones
3. **Researches** what each model can do (text, images, audio, etc.)
4. **Organizes** all the information into a clean database format
5. **Creates** reports that humans can easily read and understand

**Why This Matters**: Instead of manually checking Google's documentation and keeping track of dozens of AI models, this pipeline does it automatically and keeps everything organized and up-to-date.

---

## Technical Overview

### Pipeline Architecture
This is a **5-stage data pipeline** that transforms raw Google AI API data into normalized, database-ready format:

```
Raw Google API → Filtered Models → Modality Data → Enriched Models → Database-Ready CSV
    Stage 1    →    Stage 2     →   Stage 3    →    Stage 4   →      Stage 5
```

### Pipeline Stages

#### Stage 1: API Data Extraction (`A_api_models_fetch.py`)
- **What it does**: Fetches all available models from Google's AI API
- **Input**: Google AI API (requires API key)
- **Output**: `pipeline-outputs/A-api-models-fetch.json` (raw model data)
- **Report**: `pipeline-outputs/A-api-models-fetch-report.txt` (human-readable summary)

#### Stage 2: Model Filtering (`B_models_filter.py`)
- **What it does**: Filters out experimental/preview models, keeps only production-ready ones
- **Input**: `pipeline-outputs/A-api-models-fetch.json`
- **Output**: `pipeline-outputs/B-models-filter.json` (filtered models)
- **Report**: `pipeline-outputs/B-models-filter-report.txt` (shows what was included/excluded)
- **Configuration**: Uses `03_models_filtering_rules.json` for filtering criteria

#### Stage 3: Modality Scraping (`C_modality_scraper.py`)
- **What it does**: Scrapes Google's documentation to discover what each model can do (text, images, audio, etc.)
- **Input**: Google's official AI documentation websites
- **Output**: `stage-3-scrapped-modalities.json` (modality mappings)
- **Report**: `stage-3-scrapped-modalities-report.txt` (readable modality list)

#### Stage 4: Modality Enrichment (`D_modality_enrichment.py`)
- **What it does**: Combines filtered models with scraped modality data using intelligent matching
- **Input**: `stage-2-filtered-models.json` + `stage-3-scrapped-modalities.json`
- **Output**: `stage-4-enriched-modalities.json` (models with complete modality info)
- **Report**: `stage-4-enriched-modalities-report.txt` (matching statistics and details)

#### Stage 5: Data Normalization (`E_normalization_per_db_schema.py`)
- **What it does**: Transforms data into final database schema with proper formatting
- **Input**: `stage-4-enriched-modalities.json`
- **Output**: 
  - `stage-5-normalization-report.csv` (database-ready CSV file)
  - `stage-5-normalization-report.txt` (human-readable final report)

---

## Configuration Files Explained

### 🔧 Core Configuration Files

#### `01_google_models_licenses.json`
- **Purpose**: Defines license information for different model families
- **Contains**: License names, URLs, and terms for Google AI models

#### `02_modality_standardization.json`
- **Purpose**: Standardizes how we describe what models can do
- **Example**: "Text Embeddings", "Image Generation", "Audio Processing"

#### `03_models_filtering_rules.json`
- **Purpose**: Rules for deciding which models to include/exclude
- **Contains**: 
  - Keywords to exclude (experimental, preview, beta)
  - Patterns to include (embedding, imagen, gemini)
  - Validation requirements

#### `04_embedding_models.json`
- **Purpose**: Special handling for text embedding models
- **Contains**: Search patterns and default modality assignments

#### `05_timestamp_patterns.json`
- **Purpose**: Handles date/time formatting across different Google model releases

#### `06_unique_models_modalities.json`
- **Purpose**: Hardcoded modality data for special models that don't fit standard patterns
- **Example**: AQA (Question Answering) model specifications

#### `07_name_standardization_rules.json`
- **Purpose**: Special rules for model name formatting
- **Example**: "Gemma 3N" → "Gemma 3n" (lowercase 'n')

---

## How to Run the Pipeline

### 🚀 Quick Start (Complete Pipeline)
```bash
# Run all 5 stages automatically
python3 Z_run_complete_pipeline.py
```

### 🎯 Partial Pipeline Execution
```bash
# Start from a specific stage (useful for debugging or re-running)
python3 Z_run_complete_pipeline.py --start "Stage 3"

# List all available stages
python3 Z_run_complete_pipeline.py --list
```

### 🔧 Individual Stage Execution
```bash
# Run individual stages manually
python3 A_api_models_fetch.py      # Stage 1
python3 B_models_filter.py         # Stage 2  
python3 C_modality_scraper.py      # Stage 3
python3 D_modality_enrichment.py   # Stage 4
python3 E_normalization_per_db_schema.py  # Stage 5
```

---

## Understanding the Output

### 📊 Final Database File
**File**: `stage-5-normalization-report.csv`
- This is the **final, database-ready file**
- Contains all Google AI models with complete information
- Ready to upload to any database system

### 📄 Human-Readable Reports
Each stage creates a `.txt` report file that explains:
- What happened during that stage
- How many models were processed
- Any issues encountered
- Statistics and summaries

### 🔍 What Information is Collected
For each AI model, the pipeline collects:
- **Basic Info**: Name, version, description
- **Capabilities**: What it can process (text, images, audio, video)
- **Licensing**: Terms of use and restrictions
- **Technical Details**: Token limits, supported features
- **Provider Info**: Google as provider, US as country

---

## Model Filtering Logic

### ✅ Models We Keep (Production-Ready)
- **Stable releases**: gemini-1.5-pro, gemini-2.0-flash
- **Embedding models**: text-embedding-004, embedding-001
- **Image generation**: imagen-3.0-generate, imagen-4.0-generate
- **Video generation**: veo-3.0-generate (non-preview versions)
- **Specialized AI**: AQA, LearnLM (stable versions)

### ❌ Models We Exclude (Not Production-Ready)
- **Experimental**: Any model with "exp", "experimental"
- **Preview**: Any model with "preview"
- **Beta/Test**: Any model with "beta", "test", "testing"
- **Billing Required**: Models requiring special payment plans

### 🧠 Smart Filtering Features
- **Word Boundary Matching**: Excludes "experimental" but keeps "non-experimental"
- **Pattern-Based Inclusion**: Automatically includes new models that match known patterns
- **Configurable Rules**: Easy to update filtering criteria without code changes

---

## Data Sources and Reliability

### 🌐 Primary Data Sources
1. **Google AI API**: Official model listings and specifications
2. **Google AI Documentation**: 
   - https://ai.google.dev/gemini-api/docs/models
   - https://ai.google.dev/gemini-api/docs/imagen
   - https://ai.google.dev/gemini-api/docs/video
   - https://ai.google.dev/gemini-api/docs/embeddings
   - https://ai.google.dev/gemma/docs (Gemma models)

### 🔄 Data Freshness
- API data: Real-time (fetched during each run)
- Documentation: Scraped during each run
- Configuration: Updated as needed for new model types

### 🛡️ Error Handling
- **API failures**: Graceful degradation with detailed error reporting
- **Missing modalities**: Fallback to "Unknown" with manual review flags
- **Network issues**: Retry logic with timeout handling
- **Data validation**: Comprehensive checks at each stage

---

## Troubleshooting Common Issues

### 🔑 API Key Problems
**Error**: "API key not found" or "Authentication failed"
**Solution**: 
1. Get API key from Google AI Studio
2. Set environment variable: `export GOOGLE_API_KEY="your-key-here"`
3. Or add to `.env` file in parent directory

### 🌐 Network/Documentation Issues
**Error**: "Failed to scrape modalities" or timeout errors
**Solution**:
1. Check internet connection
2. Verify Google documentation URLs are accessible
3. Re-run the specific failed stage

### 📁 Missing Configuration Files
**Error**: "Configuration file not found"
**Solution**: Ensure all required JSON configuration files are present in the pipeline directory

### 🔄 Partial Pipeline Failures
**Error**: Pipeline stops at specific stage
**Solution**: 
1. Check the generated report files for error details
2. Run individual stages to isolate the problem
3. Use `--start` parameter to resume from failed stage

---

## Advanced Usage

### 🔧 Customizing Filtering Rules
Edit `03_models_filtering_rules.json` to:
- Add new exclusion keywords
- Include new model patterns
- Modify validation requirements

### 📊 Custom Modality Mappings
Edit `06_unique_models_modalities.json` to:
- Add modality data for new unique models
- Override default modality detection
- Handle special cases

### 🎯 Database Integration
After pipeline completion:
1. Use `stage-5-normalization-report.csv` for database upload
2. Run `F_refresh_supabase_working_version.py` for Supabase integration
3. Or import CSV into any database system

---

## Pipeline Performance

### ⏱️ Expected Runtime
- **Complete Pipeline**: 5-15 minutes
- **Stage 1 (API)**: 1-2 minutes
- **Stage 2 (Filtering)**: <30 seconds
- **Stage 3 (Scraping)**: 2-5 minutes
- **Stage 4 (Enrichment)**: <30 seconds  
- **Stage 5 (Normalization)**: <30 seconds

### 📈 Typical Results
- **Input Models**: ~65 total models from Google API
- **Filtered Models**: ~32 production-ready models
- **Success Rate**: 95-100% modality matching
- **Final Output**: Complete database records for all filtered models

---

## Getting Help

### 📋 Log Files and Reports
Each stage generates detailed reports. Check these first:
- `Z-run-complete-pipeline-report.txt` - Overall pipeline status
- Individual stage reports (e.g., `stage-2-filtered-models-report.txt`)

### 🐛 Common Solutions
1. **Re-run the pipeline**: Often resolves temporary network issues
2. **Check configuration files**: Ensure all JSON files are valid
3. **Verify API access**: Test Google AI API key independently
4. **Review error messages**: Reports contain detailed error information

### 💡 Tips for Success
- Run during stable internet connection
- Ensure sufficient disk space for output files
- Keep configuration files up-to-date
- Monitor Google AI documentation for changes

---

*This documentation covers the complete Google AI Models Discovery Pipeline. For technical support or customization needs, refer to the individual script files and configuration documentation.*