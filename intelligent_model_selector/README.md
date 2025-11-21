# Intelligent Model Selector

**Version**: 1.0.0
**Status**: ✅ 92% Complete - Fully Integrated with askme_v2
**Timeline**: Phase 4 Complete, Phase 5 In Progress

Dynamic, intelligent model selection service that queries ai_models_main table in Supabase to select optimal AI models based on query characteristics, performance metrics, rate limits, and geographic considerations.

**🎉 Latest Achievement**: Successfully integrated with askme_v2 backend with 2-20ms selection latency (50x faster than target)!

## System Architecture

```
┌─────────────────┐
│   askme_v2      │
│   Backend       │
└────────┬────────┘
         │ HTTP Request
         │ (query, type, modalities)
         ↓
┌─────────────────────────────┐
│ Intelligent Model Selector  │
│  ┌──────────────────────┐   │
│  │ Selection Algorithm  │   │
│  │  - Intelligence Index│   │
│  │  - Rate Limit Tracker│   │
│  │  - Latency Scoring   │   │
│  │  - Geography Filter  │   │
│  └──────────────────────┘   │
└────────┬────────────────────┘
         │
         ├─→ Supabase (ai_models_main)
         │   - Daily updated model data
         │   - 75+ free models
         │
         └─→ Artificial Analysis API
             - Intelligence Index scores
             - Performance benchmarks
```

## Project Goals

- ✅ Real-time model selection from daily-updated ai_models_main table (70 models cached)
- ✅ Multi-factor scoring algorithm (performance, latency, rate limits, geography)
- ✅ Smart rate limit distribution across all providers
- ✅ Modality-aware routing (text, image, audio, video)
- ✅ Geographic compliance filtering
- ⏳ Intelligence Index integration from Artificial Analysis (using fallback scoring)
- ✅ Sub-100ms selection latency with caching (achieved 2-20ms!)
- ✅ Seamless integration with askme_v2 backend

**📊 Status**: 7/8 goals complete (87.5%)

## Quick Start

### Prerequisites

- Node.js 18+ LTS
- npm 9.6+
- Supabase account with ai_models_main table access
- (Optional) Artificial Analysis API key

### Setup

```bash
cd selector-service
npm install
cp .env.example .env
# Edit .env with your credentials
npm run dev
```

### Testing

```bash
npm test              # Run all tests
npm run test:watch    # Watch mode
```

## Key Features

**Dynamic Model Discovery**
- Queries ai_models_main table for latest available models
- Adapts to daily model additions/removals automatically
- No hardcoded model assumptions

**Intelligent Selection Algorithm**
- Intelligence Index scoring from Artificial Analysis
- Provider latency considerations (Groq > Google > OpenRouter)
- Rate limit headroom matching (complex queries → high headroom)
- Geographic filtering by model_provider_country
- Modality matching (text, image, audio, video inputs/outputs)

**Rate Limit Intelligence**
- Tracks API usage per provider
- Distributes load strategically (not avoidance)
- Simple queries use low-headroom providers
- Complex queries routed to high-headroom providers

**Performance Optimizations**
- 30-minute cache for ai_models_main snapshot
- Background cache refresh (no query latency)
- In-memory rate limit counters
- Sub-100ms selection time

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Runtime | Node.js 18+ LTS | ES Modules, native watch mode |
| Framework | Express 4.18+ | Lightweight HTTP API |
| Database | Supabase (PostgreSQL) | ai_models_main table access |
| Caching | Node.js in-memory | 30-min TTL, background refresh |
| Testing | Jest 29 | Unit + integration tests |
| External API | Artificial Analysis | Intelligence Index data |

## API Endpoints

### POST /select-model

Select optimal model based on query characteristics.

**Request:**
```json
{
  "queryType": "financial_analysis",
  "queryText": "Analyze the Q4 earnings...",
  "modalities": ["text"],
  "complexityScore": 0.8
}
```

**Response:**
```json
{
  "provider": "groq",
  "modelName": "llama-3.3-70b-versatile",
  "humanReadableName": "Llama 3.3 70B Versatile",
  "score": 0.92,
  "rateLimitHeadroom": 0.85,
  "estimatedLatency": "low",
  "intelligenceIndex": 0.89,
  "selectionReason": "High Intelligence Index, excellent rate limit headroom, optimized for complex queries"
}
```

## Selection Criteria Priority

1. **Model availability** (from latest ai_models_main data)
2. **Modality match** (filter by required input/output modalities)
3. **Intelligence Index** (performance score from Artificial Analysis)
4. **Query complexity + rate limit headroom**:
   - Simple query + low headroom = OK
   - Complex query + low headroom = deprioritize
   - Complex query + high headroom = prioritize
5. **Latency** (Groq fastest, then Google, then OpenRouter)
6. **Geographic compliance** (configurable filtering)
7. **License preference** (configurable, not mandatory)

## Integration with askme_v2

The selector service integrates with askme_v2 backend at the routing layer:

**Current (askme_v2):**
```javascript
// Hardcoded model selection
const model = MODELS.groq; // 'llama-3.1-8b-instant'
```

**New (with selector):**
```javascript
// Dynamic model selection
const selection = await selectModel({
  queryType: category,
  queryText: query,
  modalities: ['text']
});
const { provider, modelName } = selection;
```

Integration points:
- `askme-backend/src/routing/router.js` - Replace selectPrimaryProvider()
- `askme-backend/src/failover/failover.js` - Use dynamic model names
- `askme-backend/src/utils/supabase.js` - Add selector API client

## Data Privacy

✅ **What we do:**
- Query ai_models_main table for model metadata
- Track aggregate rate limit usage (no user data)
- Cache model lists temporarily (30 minutes)

❌ **What we don't do:**
- Store user queries or responses
- Log personally identifiable information
- Share data with third parties (except Artificial Analysis API)

## Documentation

Organized by topic with serial numbering (MECE):

- **00_project/** - Project planning, charter, checklists
- **01_getting_started/** - Setup and installation guides
- **03_architecture/** - System design and data flows
- **05_database/** - Database schema documentation
- **06_testing/** - Testing strategies and guides
- **08_operations/** - Configuration and troubleshooting

Start with [INDEX.md](INDEX.md) for navigation.

## Implementation Status

**📋 Detailed Summary**: See [05_implementation_summary.md](00_project/05_implementation_summary.md) for complete implementation details.

**📊 Progress**: 92% complete (89/97 tasks)
- ✅ Phase 1: Foundation & Infrastructure (100%)
- 🟡 Phase 2: Selection Algorithm (94%)
- ✅ Phase 3: Rate Limit Intelligence (100%)
- ✅ Phase 4: API & Integration (96%)
- 🟡 Phase 5: Testing & Operations (75%)

**🎯 Key Metrics**:
- 2-20ms selection latency (50x faster than 100ms target)
- 70 models cached from Supabase
- 45 unit tests (~85% coverage)
- 2,534 lines of code across 18 files

**🔗 Integration**:
- ✅ Selector service running on port 3001
- ✅ askme_v2 backend integrated on port 3000
- ✅ Dynamic model selection working end-to-end
- ✅ Provider name normalization (Google→gemini)

## Development

### Service Commands

```bash
npm run dev          # Start with hot reload
npm start            # Production mode
npm test             # Run tests with coverage
npm run lint         # Check code style
npm run lint:fix     # Auto-fix style issues
```

### Environment Variables

Required:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon key

Optional:
- `ARTIFICIAL_ANALYSIS_API_KEY` - Intelligence Index API key
- `PORT` - Service port (default: 3001)
- `CACHE_TTL` - Cache duration in ms (default: 1800000)

## Troubleshooting

**Selection returns no models:**
- Check Supabase connection and ai_models_main table access
- Verify modality filters aren't too restrictive
- Review logs for database query errors

**Slow selection times:**
- Ensure cache is enabled and working
- Check Supabase query performance
- Verify network latency to Supabase

**Rate limit tracking inaccurate:**
- Counters reset on service restart (in-memory)
- Consider Redis for persistent tracking in production
- Check counter reset logic matches provider windows

## License

MIT License - see [LICENSE](LICENSE) file for details.
