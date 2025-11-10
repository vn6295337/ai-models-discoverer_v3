# AI Models Discoverer v3

Automated multi-pipeline system for discovering, enriching, and managing AI model metadata from multiple providers (OpenRouter, Google, Groq). Orchestrates daily data pipelines to fetch model information, process licenses, standardize modalities, and deploy to Supabase database for production use.

## Overview

AI Models Discoverer v3 is a production-grade data pipeline system that:
- Fetches AI model metadata from multiple API providers
- Extracts and standardizes licensing information (including Google, Meta, and open-source licenses)
- Processes and enriches model capabilities (modalities, context windows, pricing)
- Validates data quality and consistency
- Deploys curated datasets to Supabase database
- Runs automatically via GitHub Actions on a daily schedule

## Features

- **Multi-Provider Support**: OpenRouter, Google AI, Groq
- **Automated Pipelines**: Scheduled daily runs via GitHub Actions
- **License Processing**: Comprehensive license extraction from multiple sources (HuggingFace, Google, Meta)
- **Modality Standardization**: Text, image, video, audio, code capabilities
- **Provider Enrichment**: Additional metadata and company information
- **Database Integration**: Direct deployment to Supabase PostgreSQL
- **Quality Assurance**: Field comparison and data validation between pipeline outputs and database
- **Detailed Reporting**: Comprehensive reports for each pipeline stage

## Architecture

### Pipeline Structure

Each pipeline follows a standardized alphabetical flow (A → Z):

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Models Discoverer v3                       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐           ┌────▼────┐          ┌────▼────┐
   │OpenRouter│          │ Google  │          │  Groq   │
   │Pipeline  │          │Pipeline │          │Pipeline │
   └────┬────┘           └────┬────┘          └────┬────┘
        │                     │                     │
        │  A: Fetch Models    │                     │
        │  B: Filter          │                     │
        │  C-M: Licenses      │                     │
        │  N-O: Modalities    │                     │
        │  P: Enrich Provider │                     │
        │  Q: Create DB Data  │                     │
        │  R: Filter DB Data  │                     │
        │  S: Compare Fields  │                     │
        │  T: Refresh Working │                     │
        │  U: Deploy to Main  │                     │
        └─────────┬───────────┴─────────────────────┘
                  │
            ┌─────▼─────┐
            │ Supabase  │
            │ Database  │
            └───────────┘
```

### Pipeline Components

#### OpenRouter Pipeline (Primary)
Complete 19-step pipeline (A-S + T-U):
- **A-B**: Model fetching and filtering
- **C-M**: License extraction (Google, Meta, HuggingFace) and standardization
- **N-O**: Modality processing
- **P**: Provider information enrichment
- **Q**: Database data creation
- **R**: Data filtering
- **S**: Field comparison with existing database
- **T**: Refresh Supabase working version
- **U**: Deploy to production table

#### Google Pipeline
Focused on Google AI models with similar flow (A-H)

#### Groq Pipeline
Focused on Groq models with production scraping and deployment (A-J)

#### HuggingFace Pipeline (Shelved)
⚠️ **Status: NOT VIABLE** - HuggingFace Free Inference API limitations ($0.10/month = ~100 requests) make it impractical for production use. Pipeline code is complete but shelved.

## Prerequisites

- Python 3.11+
- PostgreSQL (via Supabase)
- Git
- API Keys:
  - OpenRouter API Key
  - HuggingFace API Key (for license lookups)
  - Supabase credentials

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-models-discoverer_v3.git
cd ai-models-discoverer_v3
```

### 2. Set up virtual environment

```bash
# For OpenRouter pipeline
cd openrouter_pipeline
python3.11 -m venv openrouter_env
source openrouter_env/bin/activate  # On Windows: openrouter_env\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your credentials:

```bash
# Pipeline Database Connection (PostgreSQL - pipeline_writer role)
PIPELINE_SUPABASE_URL=postgresql://pipeline_writer:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres

# Vercel App (Public - anon key)
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=YOUR_ANON_KEY

# API Keys
OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY
HUGGINGFACE_API_KEY=YOUR_HF_KEY
GROQ_API_KEY=YOUR_GROQ_KEY
```

### 4. Initialize database

Ensure your Supabase database has the required tables:
- `ai_models_main` (production table)
- `ai_models_working_version` (staging table)

Refer to `supabase-rls-security-checklist.md` for RLS policies and security setup.

## Usage

### Running Pipelines Locally

#### OpenRouter Pipeline (Complete A-S)
```bash
cd openrouter_pipeline/01_scripts
python Z_run_A_to_S.py
```

#### Individual Scripts
```bash
# Fetch models
python A_fetch_api_models.py

# Filter models
python B_filter_models.py

# Run through license extraction
python C_extract_google_licenses.py
python D_extract_meta_licenses.py
# ... etc
```

#### Google Pipeline
```bash
cd google_pipeline/01_scripts
python Z_run_A_to_F.py
```

#### Groq Pipeline
```bash
cd groq_pipeline/01_scripts
# Run individual scripts as needed
```

### Automated Runs (GitHub Actions)

Pipelines run automatically:
- **Daily**: Scheduled at midnight UTC
- **On Push**: When pipeline code or configs change
- **Manual**: Via workflow dispatch

#### Workflow Files
- `.github/workflows/openrouter-pipeline-a-to-s.yml`
- `.github/workflows/google-pipeline-a-to-f.yml`
- `.github/workflows/groq-pipeline-a-to-h.yml`

#### Manual Deployment Workflows
- `openrouter-deploy-t-u-manual.yml` - Deploy OpenRouter data to production
- `google-deploy-g-h-manual.yml` - Deploy Google data
- `groq-deploy-i-j-manual.yml` - Deploy Groq data

## Pipeline Details

### OpenRouter Pipeline Stages

| Stage | Script | Description |
|-------|--------|-------------|
| A | `A_fetch_api_models.py` | Fetch models from OpenRouter API |
| B | `B_filter_models.py` | Filter by criteria (modalities, availability) |
| C | `C_extract_google_licenses.py` | Extract Google model licenses |
| D | `D_extract_meta_licenses.py` | Extract Meta/Llama licenses |
| E | `E_fetch_other_license_info_urls_from_hf.py` | Fetch license URLs from HuggingFace |
| F | `F_fetch_other_license_names_from_hf.py` | Fetch license names from HuggingFace |
| G | `G_standardize_other_license_names_from_hf.py` | Standardize license names |
| H | `H_bucketize_other_license_names.py` | Categorize as opensource/custom |
| I | `I_opensource_license_urls.py` | Generate opensource license URLs |
| J | `J_custom_license_urls.py` | Generate custom license URLs |
| K | `K_collate_opensource_licenses.py` | Collate opensource licenses |
| L | `L_collate_custom_licenses.py` | Collate custom licenses |
| M | `M_final_list_of_licenses.py` | Create final license list |
| N | `N_extract_raw_modalities.py` | Extract raw modality data |
| O | `O_standardize_raw_modalities.py` | Standardize modality formats |
| P | `P_enrich_provider_info.py` | Enrich with provider metadata |
| Q | `Q_create_db_data.py` | Transform to database schema |
| R | `R_filter_db_data.py` | Filter final dataset |
| S | `S_compare_pipeline_with_supabase.py` | Validate against database |
| T | `T_refresh_supabase_working_version.py` | Update staging table |
| U | `U_deploy_to_ai_models_main.py` | Deploy to production |

### Output Files

All pipeline outputs are stored in `<pipeline_name>/02_outputs/`:

```
02_outputs/
├── A-fetched-api-models.json
├── A-fetched-api-models-report.txt
├── B-filtered-models.json
├── B-filtered-models-report.txt
├── ... (through M)
├── N-raw-modalities.json
├── O-standardized-modalities.json
├── P-provider-enriched.json
├── Q-created-db-data.json
├── R_filtered_db_data.json
├── S-field-comparison-report.txt
├── Z-pipeline-execution-report.txt
└── last-run.txt
```

## Configuration

### Pipeline Configurations

Each pipeline includes configuration files in `03_configs/`:

- `01_api_configuration.json` - API endpoints and pagination
- `02_prefetch_filters.json` - Filters applied during API fetch
- `03_postfetch_filters.json` - Post-processing filters
- `04_postfetch_field_removal.json` - Fields to exclude
- `provider_enrichment_config.json` - Provider metadata

### Modality Mappings

Standardized modalities include:
- Text (text-to-text, chat)
- Image (text-to-image, image-to-text)
- Video (text-to-video, video-to-text)
- Audio (text-to-audio, audio-to-text)
- Code (code generation, code completion)

## Database Schema

### ai_models_main (Production Table)

Key fields:
- `model_id` - Unique model identifier
- `model_name` - Display name
- `provider_name` - Provider (OpenRouter, Google, Groq)
- `context_window` - Maximum context length
- `modalities` - Supported capabilities (JSON array)
- `license_name` - License type
- `license_url` - License documentation URL
- `pricing_*` - Cost per token (prompt/completion)
- `created_at` / `updated_at` - Timestamps

## Development

### Project Structure

```
ai-models-discoverer_v3/
├── .github/workflows/        # GitHub Actions workflows
├── openrouter_pipeline/      # Primary pipeline
│   ├── 01_scripts/          # Pipeline scripts (A-U, Z)
│   ├── 02_outputs/          # Generated data and reports
│   ├── 03_configs/          # Configuration files
│   └── 04_utils/            # Utility modules
├── google_pipeline/          # Google AI pipeline
├── groq_pipeline/           # Groq pipeline
├── huggingface_pipeline/    # Shelved pipeline (reference only)
├── db_utils.py              # Database utilities
├── requirements.txt         # Root dependencies
└── .env.local               # Environment variables (not tracked)
```

### Adding a New Provider

1. Create new pipeline directory: `<provider>_pipeline/`
2. Set up standard structure: `01_scripts/`, `02_outputs/`, `03_configs/`
3. Implement core scripts following A-Z convention
4. Create orchestrator script: `Z_run_A_to_X.py`
5. Add GitHub Actions workflow: `.github/workflows/<provider>-pipeline.yml`
6. Update root `requirements.txt` to include pipeline dependencies

## Monitoring

### Pipeline Reports

Each pipeline run generates:
- **Execution Report** (`Z-pipeline-execution-report.txt`) - Full pipeline status
- **Stage Reports** (`X-*-report.txt`) - Individual stage details
- **GitHub Actions Artifacts** - Uploaded automatically (30-day retention)

### Logs

Check GitHub Actions logs for:
- Pipeline execution status
- Error details
- Data validation warnings
- Deployment confirmations

## Troubleshooting

### Common Issues

**API Rate Limits**
- OpenRouter: Check your account limits
- HuggingFace: Free tier very limited (~100 requests/month)
- Solution: Implement exponential backoff, use caching

**Database Connection Failures**
- Verify `PIPELINE_SUPABASE_URL` in `.env.local`
- Check Supabase project status
- Ensure `pipeline_writer` role has correct permissions

**Missing Output Files**
- Check previous pipeline stage completed successfully
- Review stage report for errors
- Verify input file paths in configuration

**Merge Conflicts in Output Files**
- Output files are auto-generated and may conflict during git operations
- Safe to resolve by accepting incoming changes or regenerating

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test locally
4. Commit with descriptive messages
5. Push and create a Pull Request

## License

[Specify your license here]

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Review existing documentation in pipeline directories
- Check `PIPELINE_STATUS.txt` files for pipeline-specific details

## Acknowledgments

- OpenRouter for comprehensive AI model API
- HuggingFace for model license metadata
- Supabase for database infrastructure
- GitHub Actions for automation

---

**Last Updated**: 2025-11-10
**Version**: 3.0
**Status**: Production
