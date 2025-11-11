# AI Models Discoverer v3

Automated multi-pipeline system for discovering, enriching, and managing AI model metadata from OpenRouter, Google AI, and Groq. Deploys curated datasets to Supabase database for production use by [askme](https://github.com/vn6295337/askme) and [ai-land](https://github.com/vn6295337/ai-land).

## Overview

Production-grade data pipeline system that:
- Fetches free AI model metadata from 3 providers (OpenRouter, Google AI, Groq)
- Extracts and standardizes licensing information
- Processes model capabilities (modalities, context windows, pricing)
- Validates data quality and consistency
- Deploys to Supabase `ai_models_main` table (shared with askme and ai-land)
- Runs automatically via GitHub Actions daily

**Current Dataset**: 75 models (OpenRouter: 44, Google: 24, Groq: 7)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              AI Models Discoverer v3                         │
└─────────────────────────────────────────────────────────────┘
                          │
      ┌───────────────────┼───────────────────┐
      │                   │                   │
 ┌────▼────┐         ┌────▼────┐        ┌────▼────┐
 │OpenRouter│       │ Google  │        │  Groq   │
 │Pipeline │        │Pipeline │        │Pipeline │
 │  (A-U)  │        │  (A-H)  │        │  (A-J)  │
 └────┬────┘         └────┬────┘        └────┬────┘
      │                   │                   │
      └───────────────────┼───────────────────┘
                          │
                    ┌─────▼─────┐
                    │ Supabase  │
                    │ai_models  │
                    │   _main   │
                    └─────┬─────┘
                          │
           ┌──────────────┴──────────────┐
           │                             │
      ┌────▼────┐                   ┌────▼────┐
      │ askme   │                   │ai-land  │
      │(backend)│                   │dashboard│
      └─────────┘                   └─────────┘
```

## Pipelines

### OpenRouter Pipeline (19 stages: A-U)

Processes models from OpenRouter API with comprehensive license extraction:

| Stage | Description |
|-------|-------------|
| A | Fetch models from OpenRouter API |
| B | Filter by availability and modalities |
| C-F | Extract licenses (Google, Meta, open-source) |
| G-M | Standardize and consolidate license data |
| N-O | Process and standardize modalities |
| P | Enrich with provider metadata |
| Q | Transform to database schema |
| R | Filter final dataset |
| S | Compare with existing database |
| T | Refresh Supabase working version |
| U | Deploy to production table |

**Run**: `cd openrouter_pipeline/01_scripts && python Z_run_A_to_S.py`

### Google Pipeline (8 stages: A-H)

Processes Google AI models (Gemini family) with web scraping:

| Stage | Description |
|-------|-------------|
| A | Fetch models from Google AI API |
| B | Filter by availability |
| C | Scrape modalities from documentation |
| D | Enrich modality metadata |
| E | Transform to database schema |
| F | Compare with existing database |
| G | Refresh Supabase working version |
| H | Deploy to production table |

**Run**: `cd google_pipeline/01_scripts && python Z_run_A_to_F.py`

### Groq Pipeline (10 stages: A-J)

Processes Groq models with web scraping and rate limit detection:

| Stage | Description |
|-------|-------------|
| A | Scrape production models from Groq website |
| B | Scrape rate limits and quotas |
| C | Scrape modalities from documentation |
| D | Extract Meta/Llama licenses |
| E | Extract open-source licenses |
| F | Consolidate all licenses |
| G | Normalize data to standard schema |
| H | Compare with existing database |
| I | Refresh Supabase working version |
| J | Deploy to production table |

**Run**: `cd groq_pipeline/01_scripts && python Z_run_A_to_H.py`

## Prerequisites

- Python 3.11+
- Supabase account with `ai_models_main` table
- API Keys:
  - OpenRouter API Key
  - Google AI API Key (Gemini)
  - Groq API Key

## Installation

### 1. Clone repository

```bash
git clone https://github.com/vn6295337/ai-models-discoverer_v3.git
cd ai-models-discoverer_v3
```

### 2. Configure environment

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
PIPELINE_SUPABASE_URL=postgresql://pipeline_writer:password@db.project.supabase.co:5432/postgres

# API Keys
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_API_KEY=your_google_ai_key
GROQ_API_KEY=your_groq_key
```

### 3. Set up virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Initialize Supabase tables

Ensure your Supabase database has:
- `ai_models_main` (production table)
- `ai_models_working_version` (staging table)

## Usage

### Local Execution

```bash
# OpenRouter pipeline
cd openrouter_pipeline/01_scripts
python Z_run_A_to_S.py

# Google pipeline
cd google_pipeline/01_scripts
python Z_run_A_to_F.py

# Groq pipeline
cd groq_pipeline/01_scripts
python Z_run_A_to_H.py
```

### Automated Runs (GitHub Actions)

Pipelines run automatically:
- **Daily**: Midnight UTC
- **On Push**: When pipeline code changes
- **Manual**: Via workflow dispatch

**Workflows**:
- `.github/workflows/openrouter-pipeline-a-to-s.yml`
- `.github/workflows/google-pipeline-a-to-f.yml`
- `.github/workflows/groq-pipeline-a-to-h.yml`

**Manual Deployment**:
- `openrouter-deploy-t-u-manual.yml`
- `google-deploy-g-h-manual.yml`
- `groq-deploy-i-j-manual.yml`

## Database Schema

### ai_models_main Table

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | text | Unique identifier |
| `canonical_slug` | text | Canonical model slug |
| `human_readable_name` | text | Display name |
| `inference_provider` | text | Provider (OpenRouter, Google, Groq) |
| `model_provider` | text | Model creator/owner |
| `context_window` | integer | Maximum context length |
| `modalities` | jsonb | Supported capabilities |
| `license_name` | text | License type |
| `license_url` | text | License documentation |
| `pricing_prompt` | numeric | Cost per 1M prompt tokens |
| `pricing_completion` | numeric | Cost per 1M completion tokens |
| `created_at` | timestamp | Record creation time |
| `updated_at` | timestamp | Last update time |

## Project Structure

```
ai-models-discoverer_v3/
├── .github/workflows/        # Automation workflows
├── openrouter_pipeline/
│   ├── 01_scripts/          # A-U pipeline stages
│   ├── 02_outputs/          # Generated JSON and reports
│   └── 03_configs/          # API and filter configs
├── google_pipeline/
│   ├── 01_scripts/          # A-H pipeline stages
│   └── 02_outputs/          # Generated data
├── groq_pipeline/
│   ├── 01_scripts/          # A-J pipeline stages
│   └── 02_outputs/          # Generated data
├── db_utils.py              # Shared database utilities
└── requirements.txt         # Python dependencies
```

## Integration

This system provides data for:

**[askme](https://github.com/vn6295337/askme)** - CLI tool for querying AI models
- Backend queries `ai_models_main` for available models
- Uses Google → Groq → OpenRouter fallback priority

**[ai-land](https://github.com/vn6295337/ai-land)** - Dashboard visualizing AI models
- Real-time queries of `ai_models_main` table
- Displays 75+ models with filtering by provider, modality, pricing

## Monitoring

Pipeline reports stored in `<pipeline>/02_outputs/`:
- `Z-pipeline-execution-report.txt` - Full execution status
- `X-*-report.txt` - Stage-specific details
- GitHub Actions artifacts (30-day retention)

## Troubleshooting

**Database Connection Issues**
- Verify `PIPELINE_SUPABASE_URL` format
- Check `pipeline_writer` role permissions

**API Rate Limits**
- OpenRouter: Monitor account limits
- Google AI: Check quota in Cloud Console
- Groq: Rate limits auto-detected in Stage B

**Missing Output Files**
- Ensure previous stage completed successfully
- Check stage report for errors

## Contributing

1. Fork repository
2. Create feature branch
3. Test changes locally
4. Submit Pull Request

## License

MIT License - See LICENSE file

## Related Projects

- **[askme](https://github.com/vn6295337/askme)** - Zero-config CLI for instant AI queries
- **[ai-land](https://github.com/vn6295337/ai-land)** - Real-time dashboard for AI model visualization
- **[ai_portfolio](https://github.com/vn6295337/ai_portfolio)** - Portfolio landing page

---

**Last Updated**: 2025-11-11
**Version**: 3.0
**Status**: Production
