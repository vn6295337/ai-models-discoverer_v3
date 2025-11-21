# Setup Guide

**Last Updated:** 2025-11-19
**Purpose:** Environment setup and configuration

---

## Prerequisites

**Required:**
- Node.js 18+ LTS
- npm 9.6+
- Supabase account with ai_models_main table access

**Optional:**
- Artificial Analysis API key (for Intelligence Index)
- Redis (for production deployment)

---

## Installation

### 1. Clone Repository

```bash
cd intelligent_model_selector/selector-service
```

### 2. Install Dependencies

```bash
npm install
```

Expected dependencies:
- express
- cors
- helmet
- morgan
- dotenv
- @supabase/supabase-js

Dev dependencies:
- jest
- supertest
- eslint

### 3. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Optional
ARTIFICIAL_ANALYSIS_API_KEY=your-api-key
PORT=3001
CACHE_TTL=1800000
NODE_ENV=development
LOG_LEVEL=debug
```

**Obtaining Supabase Credentials:**
1. Go to your Supabase project dashboard
2. Navigate to Project Settings → API
3. Copy Project URL → SUPABASE_URL
4. Copy anon/public key → SUPABASE_KEY

### 4. Verify ai_models_main Access

```bash
curl "https://your-project.supabase.co/rest/v1/ai_models_main?limit=1" \
  -H "apikey: your-anon-key"
```

Expected response: JSON array with model data

---

## Running the Service

### Development Mode

```bash
npm run dev
```

Uses Node.js `--watch` flag for automatic reloading.

### Production Mode

```bash
npm start
```

### Running Tests

```bash
npm test              # Run all tests with coverage
npm run test:watch    # Watch mode for TDD
```

---

## Verification

### Health Check

```bash
curl http://localhost:3001/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2025-11-19T...",
  "uptime": 123.45
}
```

### List Available Models

```bash
curl http://localhost:3001/models
```

Expected response:
```json
{
  "models": [...],
  "count": 75,
  "cached": true,
  "lastUpdate": "2025-11-19T..."
}
```

### Test Model Selection

```bash
curl -X POST http://localhost:3001/select-model \
  -H "Content-Type: application/json" \
  -d '{
    "queryType": "general_knowledge",
    "queryText": "What is the capital of France?",
    "modalities": ["text"],
    "complexityScore": 0.3
  }'
```

Expected response:
```json
{
  "provider": "groq",
  "modelName": "llama-3.1-8b-instant",
  "humanReadableName": "Llama 3.1 8B Instant",
  "score": 0.87,
  "rateLimitHeadroom": 0.95,
  "estimatedLatency": "low",
  "intelligenceIndex": 0.75,
  "selectionReason": "High rate limit headroom, low complexity query"
}
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 3001
lsof -i :3001

# Kill process
kill -9 <PID>

# Or change port in .env
PORT=3002
```

### Supabase Connection Failed

**Check credentials:**
```bash
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

**Test connection:**
```bash
curl "https://your-project.supabase.co/rest/v1/" \
  -H "apikey: your-anon-key"
```

**Common issues:**
- Wrong API key (use anon key, not service_role key)
- RLS policies blocking read access
- Network firewall blocking Supabase

### Intelligence Index API Unavailable

Service will operate with fallback scoring if Artificial Analysis API is unavailable or API key not provided. Check logs for:

```
[WARN] Intelligence Index unavailable, using fallback scoring
```

---

## Next Steps

- Review [System Architecture](../03_architecture/01_system_architecture.md)
- Check [Development Checklist](../00_project/04_dev_checklist.md)
- Explore [Testing Strategy](../06_testing/01_testing_strategy.md)

---

**Document Status:** ✅ Complete
**Document Owner:** Development Team
