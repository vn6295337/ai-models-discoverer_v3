# System Architecture - Intelligent Model Selector

**Last Updated:** 2025-11-19
**Purpose:** Detailed system design, algorithms, and data flows

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Component Design](#2-component-design)
3. [Selection Algorithm](#3-selection-algorithm)
4. [Caching Strategy](#4-caching-strategy)
5. [Rate Limit Intelligence](#5-rate-limit-intelligence)
6. [Data Flows](#6-data-flows)
7. [Integration Points](#7-integration-points)
8. [Performance Considerations](#8-performance-considerations)

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       askme_v2 Backend                       │
│  ┌────────────────────┐         ┌──────────────────────┐   │
│  │  Query Classifier  │────────→│  Model Selector      │   │
│  │  - Categorize      │         │  Client              │   │
│  │  - Calculate       │         │  - HTTP calls        │   │
│  │    complexity      │         │  - Error handling    │   │
│  └────────────────────┘         └──────────┬───────────┘   │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                                              │ HTTP POST /select-model
                                              │ {queryType, queryText,
                                              │  modalities, complexityScore}
                                              ↓
┌───────────────────────────────────────────────────────────────┐
│            Intelligent Model Selector Service                 │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Express API                        │   │
│  │  ┌────────────────┐  ┌──────────────────────────┐   │   │
│  │  │ POST /select   │  │ GET /health              │   │   │
│  │  │ POST /refresh  │  │ GET /models              │   │   │
│  │  └────────┬───────┘  └──────────────────────────┘   │   │
│  └───────────┼──────────────────────────────────────────┘   │
│              │                                                │
│              ↓                                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Model Selector Service                     │ │
│  │  ┌────────────────────────────────────────────────┐   │ │
│  │  │ 1. Fetch models from cache/DB                  │   │ │
│  │  │ 2. Filter by modalities                        │   │ │
│  │  │ 3. Calculate multi-factor scores               │   │ │
│  │  │ 4. Match complexity to headroom                │   │ │
│  │  │ 5. Select top-ranked model                     │   │ │
│  │  └────────────────────────────────────────────────┘   │ │
│  └─────┬──────────────────────────────────────────────────┘ │
│        │                                                      │
│    ┌───┴───┐      ┌──────────────┐      ┌────────────────┐ │
│    │ Cache │      │ Intelligence │      │ Rate Limit     │ │
│    │ Mgr   │      │ Index        │      │ Tracker        │ │
│    └───┬───┘      └──────┬───────┘      └────────┬───────┘ │
└────────┼──────────────────┼──────────────────────┼─────────┘
         │                  │                      │
         ↓                  ↓                      │
  ┌──────────────┐   ┌──────────────────┐         │
  │  Supabase    │   │  Artificial      │         │
  │  ai_models   │   │  Analysis API    │         │
  │  _main       │   │  (Intelligence   │         │
  │  table       │   │   Index)         │         │
  └──────────────┘   └──────────────────┘         │
                                                   │
                     (In-Memory Counters) ←───────┘
```

---

## 2. Component Design

### 2.1 Model Selector (Core)

**File:** `src/services/modelSelector.js`

**Responsibilities:**
- Orchestrate model selection process
- Apply filtering logic
- Calculate multi-factor scores
- Select optimal model

**Key Functions:**
```javascript
// Main entry point
async selectModel({queryType, queryText, modalities, complexityScore})

// Sub-functions
filterByModalities(models, requiredModalities)
calculateScores(models, queryType, complexityScore, headroomData)
matchComplexityToHeadroom(models, complexityScore, headroomData)
selectBestModel(scoredModels)
```

**Dependencies:**
- Cache Manager (model data)
- Intelligence Index (performance scores)
- Rate Limit Tracker (headroom data)

---

### 2.2 Cache Manager

**File:** `src/services/cacheManager.js`

**Responsibilities:**
- In-memory caching with TTL
- Background refresh
- Cache invalidation

**Data Structure:**
```javascript
cache = {
  models: {
    data: [],
    timestamp: Date.now(),
    ttl: 1800000  // 30 minutes
  },
  intelligenceIndex: {
    data: {},
    timestamp: Date.now(),
    ttl: 604800000  // 7 days
  }
}
```

**Key Functions:**
```javascript
get(key)                    // Retrieve from cache
set(key, value, ttl)        // Store with TTL
isExpired(key)              // Check if expired
refresh(key, fetchFn)       // Background refresh
invalidate(key)             // Force refresh
```

---

### 2.3 Intelligence Index

**File:** `src/services/intelligenceIndex.js`

**Responsibilities:**
- Fetch performance scores from Artificial Analysis
- Cache scores (7-day TTL)
- Provide fallback scoring

**Key Functions:**
```javascript
async fetchIntelligenceScores()
getScore(modelName)
calculateFallbackScore(modelName)  // Based on model size
```

**Fallback Scoring:**
```javascript
// Extract model size from name
// llama-3.3-70b → 70b → score: 0.9
// gemini-2.0-flash → small → score: 0.6
const sizeToScore = {
  '70b': 0.9,
  '27b': 0.7,
  '8b': 0.5,
  '4b': 0.4,
  '1b': 0.3
}
```

---

### 2.4 Rate Limit Tracker

**File:** `src/services/rateLimitTracker.js`

**Responsibilities:**
- Track API usage per provider
- Calculate headroom
- Reset counters periodically

**Data Structure:**
```javascript
counters = {
  groq: {
    count: 0,
    limit: 30,
    window: 60000,  // 1 minute
    lastReset: Date.now()
  },
  google: {
    count: 0,
    limit: 60,
    window: 60000
  },
  openrouter: {
    count: 0,
    limit: 200,
    window: 60000
  }
}
```

**Key Functions:**
```javascript
incrementUsage(provider)
getHeadroom(provider)        // (limit - count) / limit
resetIfExpired(provider)
getAllHeadroom()             // {groq: 0.8, google: 0.6, ...}
```

---

### 2.5 Supabase Utility

**File:** `src/utils/supabase.js`

**Responsibilities:**
- Database connection
- Query ai_models_main table
- Error handling

**Key Functions:**
```javascript
async fetchLatestModels()
async getModelsByProvider(provider)
async getModelsByModalities(inputMods, outputMods)
```

**Query Example:**
```sql
SELECT
  inference_provider,
  model_provider,
  human_readable_name,
  input_modalities,
  output_modalities,
  license_name,
  model_provider_country,
  rate_limits
FROM ai_models_main
WHERE input_modalities LIKE '%Text%'
  AND output_modalities LIKE '%Text%'
ORDER BY updated_at DESC
```

---

## 3. Selection Algorithm

### 3.1 Algorithm Overview

```
INPUT:
  - queryType: string ('business_news', 'financial_analysis', etc.)
  - queryText: string
  - modalities: string[] (['text'], ['text', 'image'], etc.)
  - complexityScore: float (0.0-1.0)

OUTPUT:
  - provider: string ('groq', 'google', 'openrouter')
  - modelName: string
  - score: float
  - rateLimitHeadroom: float
  - intelligenceIndex: float
  - selectionReason: string

STEPS:
  1. Fetch models from cache/DB
  2. Filter by modality requirements
  3. Calculate multi-factor scores
  4. Apply complexity-headroom matching
  5. Sort by score (descending)
  6. Return top-ranked model
```

### 3.2 Scoring Formula

```javascript
score = (
  intelligenceIndex * 0.35 +
  latencyScore * 0.25 +
  headroomScore * 0.25 +
  geographyScore * 0.10 +
  licenseScore * 0.05
)
```

**Factor Definitions:**

1. **Intelligence Index (35%)**
   - From Artificial Analysis API
   - Range: 0.0-1.0
   - Higher = better performance
   - Fallback: model size heuristic

2. **Latency Score (25%)**
   - Provider-based baseline
   - groq: 1.0 (fastest)
   - google: 0.8 (fast)
   - openrouter: 0.6 (moderate)

3. **Headroom Score (25%)**
   - (limit - count) / limit
   - Range: 0.0-1.0
   - Higher = more capacity available

4. **Geography Score (10%)**
   - Configurable preference
   - Default: 1.0 (no filtering)
   - Can penalize/boost by country

5. **License Score (5%)**
   - Configurable preference
   - Open-source: 1.0
   - Proprietary: 0.8
   - Custom: 0.9

### 3.3 Complexity-Headroom Matching

**Rationale:** Complex queries need providers with headroom to handle load.

```javascript
function matchComplexityToHeadroom(models, complexityScore, headroomData) {
  if (complexityScore > 0.7) {
    // High complexity: require high headroom
    return models.filter(m =>
      headroomData[m.inference_provider] > 0.6
    )
  } else if (complexityScore > 0.4) {
    // Medium complexity: require moderate headroom
    return models.filter(m =>
      headroomData[m.inference_provider] > 0.3
    )
  } else {
    // Low complexity: any headroom acceptable
    return models
  }
}
```

**Thresholds:**
- High complexity (> 0.7): Requires 60%+ headroom
- Medium complexity (0.4-0.7): Requires 30%+ headroom
- Low complexity (< 0.4): Any headroom OK

---

## 4. Caching Strategy

### 4.1 Cache Layers

**Layer 1: Models Cache (30-minute TTL)**
```javascript
{
  key: 'ai_models_main',
  data: [...],  // Array of model objects
  timestamp: Date.now(),
  ttl: 1800000  // 30 minutes
}
```

**Layer 2: Intelligence Index Cache (7-day TTL)**
```javascript
{
  key: 'intelligence_index',
  data: {
    'llama-3.3-70b': 0.89,
    'gemini-2.0-flash': 0.78,
    ...
  },
  timestamp: Date.now(),
  ttl: 604800000  // 7 days
}
```

### 4.2 Refresh Strategy

**Background Refresh:**
```javascript
// Check expiration on every access
if (isExpired(key)) {
  // Return stale data immediately
  const staleData = get(key)

  // Trigger background refresh (non-blocking)
  refresh(key, async () => {
    return await fetchLatestModels()
  })

  return staleData
}
```

**Benefits:**
- No cache-miss latency for users
- Always returns data (stale acceptable)
- Refresh happens asynchronously

**Manual Refresh:**
```http
POST /cache/refresh
```
Force immediate cache invalidation and refresh.

---

## 5. Rate Limit Intelligence

### 5.1 Tracking Mechanism

**In-Memory Counters:**
```javascript
// Global state
const rateLimits = {
  groq: {
    count: 15,        // Current usage
    limit: 30,        // Rate limit
    window: 60000,    // 1 minute
    lastReset: Date.now()
  },
  google: { count: 25, limit: 60, window: 60000 },
  openrouter: { count: 100, limit: 200, window: 60000 }
}
```

**Update Flow:**
```javascript
1. Selection made → incrementUsage(provider)
2. Every 60 seconds → resetIfExpired(provider)
3. On query → getHeadroom(provider) for scoring
```

### 5.2 Load Distribution

**Simple Queries (complexity < 0.4):**
- Can use providers with low headroom
- Optimize resource utilization
- Don't waste high-capacity providers

**Complex Queries (complexity > 0.7):**
- Require providers with high headroom
- Ensure capacity for intensive tasks
- Prevent overloading already-strained providers

**Example Scenario:**
```
Current state:
  groq:       headroom = 0.9 (27/30 available)
  google:     headroom = 0.3 (18/60 available)
  openrouter: headroom = 0.6 (120/200 available)

Simple query (complexity: 0.3):
  → Can select any provider
  → Likely chooses google (frees groq for complex queries)

Complex query (complexity: 0.8):
  → Filters out google (headroom < 0.6)
  → Chooses groq or openrouter
  → Preserves capacity strategically
```

---

## 6. Data Flows

### 6.1 Selection Flow

```
1. Client Request
   ├─→ POST /select-model
   └─→ {queryType, queryText, modalities, complexityScore}

2. Cache Check
   ├─→ IF expired:
   │   ├─→ Return stale data
   │   └─→ Trigger background refresh
   └─→ ELSE:
       └─→ Use cached models

3. Filter Models
   ├─→ By modalities (input/output match)
   ├─→ By geographic preference (optional)
   └─→ By license preference (optional)

4. Fetch Headroom Data
   └─→ rateLimitTracker.getAllHeadroom()

5. Calculate Scores
   ├─→ For each model:
   │   ├─→ intelligenceIndex * 0.35
   │   ├─→ latencyScore * 0.25
   │   ├─→ headroomScore * 0.25
   │   ├─→ geographyScore * 0.10
   │   └─→ licenseScore * 0.05
   └─→ Apply complexity-headroom filtering

6. Sort & Select
   ├─→ Sort by score (descending)
   └─→ Return top model

7. Update Usage
   └─→ rateLimitTracker.incrementUsage(provider)

8. Response
   └─→ {provider, modelName, score, headroom, ...}
```

### 6.2 Cache Refresh Flow

```
1. Timer Triggers
   └─→ setInterval(checkExpiration, 60000)  // Every minute

2. Check Expiration
   ├─→ IF timestamp + ttl < now:
   │   └─→ Mark as expired
   └─→ ELSE:
       └─→ Continue

3. Background Refresh
   ├─→ Fetch fresh data from Supabase
   ├─→ Update cache with new data
   ├─→ Reset timestamp
   └─→ Log refresh event

4. Error Handling
   ├─→ IF fetch fails:
   │   ├─→ Keep stale data
   │   ├─→ Log error
   │   └─→ Retry after delay
   └─→ ELSE:
       └─→ Update successful
```

---

## 7. Integration Points

### 7.1 askme_v2 Integration

**File:** `askme-backend/src/utils/modelSelectorClient.js`

```javascript
export async function selectModel(criteria) {
  try {
    const response = await fetch(SELECTOR_SERVICE_URL + '/select-model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(criteria),
      timeout: 5000
    })

    if (!response.ok) {
      throw new Error(`Selector service error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    logger.error('Model selection failed', { error })
    // Fallback to hardcoded defaults
    return fallbackSelection(criteria.queryType)
  }
}
```

**Integration in router.js:**
```javascript
// Before
const provider = selectPrimaryProvider(category)
const model = MODELS[provider]

// After
const selection = await selectModel({
  queryType: category,
  queryText: query,
  modalities: ['text'],
  complexityScore: calculateComplexity(query)
})
const { provider, modelName } = selection
```

### 7.2 Fallback Strategy

```javascript
function fallbackSelection(queryType) {
  // If selector service unavailable, use constants.js
  const fallbackMap = {
    business_news: { provider: 'groq', modelName: 'llama-3.1-8b-instant' },
    financial_analysis: { provider: 'groq', modelName: 'llama-3.3-70b-versatile' },
    creative: { provider: 'openrouter', modelName: 'kwaipilot/kat-coder-pro:free' },
    general_knowledge: { provider: 'google', modelName: 'gemini-2.0-flash' }
  }

  return fallbackMap[queryType] || fallbackMap.general_knowledge
}
```

---

## 8. Performance Considerations

### 8.1 Latency Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Cached selection | < 100ms | In-memory scoring |
| Uncached selection | < 500ms | Initial DB query |
| Background refresh | N/A | Non-blocking |
| Rate limit lookup | < 10ms | In-memory counter |

### 8.2 Optimization Strategies

**1. Cache Hit Rate:**
- 30-minute TTL balances freshness vs performance
- Expect > 95% cache hit rate
- Background refresh prevents cold-start latency

**2. Database Queries:**
- Minimize queries with caching
- Use Supabase connection pooling
- Add indexes on common filter fields

**3. Intelligence Index:**
- 7-day cache for external API data
- Batch fetch on startup
- Fallback scoring avoids blocking

**4. Scoring Calculation:**
- Vectorize operations where possible
- Early filtering reduces scoring overhead
- Pre-calculate static scores (latency, geography)

### 8.3 Scalability

**Current (MVP):**
- Single instance
- In-memory cache and counters
- Suitable for moderate load (< 100 req/s)

**Future (Production Scale):**
- Redis for shared cache
- Redis for persistent rate limit counters
- Load balancer for horizontal scaling
- Database connection pooling

---

**Document Status:** ✅ Complete
**Last Review:** 2025-11-19
**Document Owner:** Development Team
