# AskMe Mobile App - System Architecture

**Document Type:** System Architecture & Design
**Project:** AskMe Mobile App - Intelligent LLM Query Router for Android
**Date:** November 13, 2025
**Version:** 1.0

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ANDROID USER DEVICE                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          AskMe Mobile App (React Native/Flutter)         │  │
│  │  ┌────────────────┐      ┌──────────────────────┐       │  │
│  │  │  UI Layer      │      │  State Management    │       │  │
│  │  │ - Search Box   │◄────►│ - Query State        │       │  │
│  │  │ - Response     │      │ - Response State     │       │  │
│  │  │ - Settings     │      │ - Loading State      │       │  │
│  │  │ (No History)   │      │ - Error State        │       │  │
│  │  └────────────────┘      └──────────────────────┘       │  │
│  │            ▲                      ▲                      │  │
│  │            │                      │                      │  │
│  │  ┌─────────┴──────────────────────┴────────┐           │  │
│  │  │      API Client Service                 │           │  │
│  │  │  - HTTP calls to backend                │           │  │
│  │  │  - Offline detection                    │           │  │
│  │  │  - Retry logic                          │           │  │
│  │  └─────────┬──────────────────────────────┬┘           │  │
│  │            │                              │             │  │
│  │  ┌─────────▼──────┐          ┌───────────▼──────┐     │  │
│  │  │  SQLite DB     │          │  Network Stack   │     │  │
│  │  │ - Offline Q    │          │ - WiFi/Mobile    │     │  │
│  │  │ - Cache (7d)   │          │ - Offline Queue  │     │  │
│  │  │ (No history)   │          │ - Sync Manager   │     │  │
│  │  └────────────────┘                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   INTERNET       │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌────▼────┐
    │  Render    │      │ Supabase  │      │ LLM     │
    │  Backend   │      │ Vault     │      │Providers│
    │  (Node.js/ │      │(API Keys) │      │         │
    │   Python)  │      └───────────┘      └─────────┘
    └─────┬─────┘
          │
    ┌─────┴────────────────────────────┬──────────────┐
    │                                   │              │
┌───▼────────┐  ┌──────────────┐  ┌───▼───┐  ┌──────▼────┐
│ Classifier │  │ Failover     │  │Router │  │ Rate      │
│ Engine     │  │ Orchestrator │  │Engine │  │ Limiter   │
└────────────┘  └──────────────┘  └───────┘  └───────────┘
    │                │                │           │
    └────────┬───────┴────────┬───────┴───────────┘
             │                │
      ┌──────▼────────┐      │
      │ LLM Providers │◄─────┘
      │ Integrations  │
      │ - Gemini      │
      │ - Groq        │
      │ - OpenRouter  │
      └───────────────┘
            │
    ┌───────┴────────────────┬─────────────┐
    │                        │             │
┌───▼──────┐  ┌──────────┐  ┌──────────────┐
│  Gemini  │  │  Groq    │  │  OpenRouter  │
│  API     │  │  API     │  │    API       │
│(60req/m) │  │(30req/m) │  │ (Aggregator) │
└──────────┘  └──────────┘  └──────────────┘
```

---

## 2. Component Details

### 2.1 Android Frontend (React Native / Flutter)

**Responsibility:** User interface, local data storage, offline queueing

**Key Components:**
- **UI Layer**
  - HomeScreen: Search interface (text input, send button)
  - ResponseDisplay: Show LLM response with metadata
  - SettingsScreen: App info, cache management

- **State Management**
  - Redux/Provider/Riverpod for global state
  - Local state for UI (loading, error, etc.)
  - **No session/history state** (fresh start on each app launch)

- **API Client Service**
  - HTTP client (axios/http)
  - Handles online/offline detection
  - Retry logic for failed requests
  - Request queuing when offline

- **SQLite Database**
  - `queries` table: id, text, category, timestamp, status (offline queue only)
  - `responses` table: id, query_id, text, llm_used, timestamp (offline queue only)
  - `cache` table: query_hash, response, expiry_date
  - Stores ~1000 cached responses (50MB limit)
  - **No history persistence** (responses cleared on app close or cache TTL)

- **Network Stack**
  - NetInfo for connectivity detection
  - Background sync when online
  - Handles WiFi/Mobile switching

---

### 2.2 Backend API (Node.js or Python on Render)

**Responsibility:** Query classification, provider selection, failover orchestration, rate limiting

**Architecture:**
```
┌─────────────────────────────────────────┐
│      Backend API (Render - Free Tier)   │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐  │
│  │     Express.js Router           │  │
│  │  POST /api/query                │  │
│  │  POST /api/queue/sync           │  │
│  │  GET  /api/health               │  │
│  └─────────────────────────────────┘  │
│              │                         │
│  ┌───────────┴──────────────────────┐ │
│  │  Request Handler Middleware      │ │
│  │  - Validation                    │ │
│  │  - Auth (if needed)              │ │
│  │  - Logging                       │ │
│  └────────────────┬─────────────────┘ │
│                   │                    │
│  ┌────────────────▼─────────────────┐ │
│  │  Classification Engine           │ │
│  │  - Keyword-based category detect │ │
│  │  - "news/latest/today" → Gemini  │ │
│  │  - "write/poem/creative" → Groq  │ │
│  │  - Default → Groq                │ │
│  └────────────────┬─────────────────┘ │
│                   │                    │
│  ┌────────────────▼─────────────────┐ │
│  │  Routing Engine                  │ │
│  │  - Simple keyword-based routing  │ │
│  │  - Select primary provider       │ │
│  │  - Setup global failover chain   │ │
│  └────────────────┬─────────────────┘ │
│                   │                    │
│  ┌────────────────▼─────────────────┐ │
│  │  Failover Orchestrator           │ │
│  │  - Global failover chain         │ │
│  │  - Primary → Groq → OpenRouter   │ │
│  │  - Return error if all fail      │ │
│  │  - App handles queueing          │ │
│  └────────────────┬─────────────────┘ │
│                   │                    │
│  ┌────────────────▼─────────────────┐ │
│  │  Provider Manager                │ │
│  │  - Calls each provider API       │ │
│  │  - Tracks rate limits            │ │
│  │  - Error handling                │ │
│  └────────────────┬─────────────────┘ │
│                   │                    │
│  ┌────────────────▼─────────────────┐ │
│  │  Rate Limiter                    │ │
│  │  - Global request counter        │ │
│  │  - Per-provider limits:          │ │
│  │    * Gemini: 60 req/min          │ │
│  │    * Groq: 30 req/min            │ │
│  │    * OpenRouter: aggregated      │ │
│  │  - Return error if rate limited  │ │
│  └─────────────────────────────────┘ │
│                                       │
└─────────────────────────────────────┘
```

**Key Flows:**

1. **Query Processing Flow**
   ```
   POST /api/query { query: "..." }
     ↓
   Validate input
     ↓
   Classify query (keyword-based, instant)
     ↓
   Select primary provider
     ↓
   Check rate limits
     ↓
   Try primary provider → if fails, try Groq → if fails, try OpenRouter
     ↓ (all fail)
   Return error to app
     ↓ (success)
   Return { response, llm_used, category }
   ```

2. **Failover Chain (Global, All Categories)**
   ```
   Try Primary Provider (context-based)
     ↓ (fails or rate limited)
   Try Groq (universal backup)
     ↓ (fails or rate limited)
   Try OpenRouter (final fallback)
     ↓ (all fail)
   Return error to app
   App handles queueing and retry locally
   ```

3. **Primary Provider Selection (Keyword-Based)**
   ```
   Query contains "news", "latest", "today"?
     → Primary: Gemini (has web search)

   Query contains "write", "poem", "creative", "story"?
     → Primary: Groq (fast, creative)

   Default/Other
     → Primary: Groq (fast, general knowledge)

   Failover: If primary fails, use global chain
     → Secondary: Groq (if primary was Gemini)
     → Tertiary: OpenRouter (final fallback)
   ```

---

### 2.3 API Key Management (Supabase Vault)

**Responsibility:** Secure storage and retrieval of API keys

**Flow:**
```
Backend Startup
  ↓
Load Supabase Project URL & Anon Key
  ↓
Initialize Supabase Client
  ↓
On each request:
  1. Retrieve Gemini key from Vault
  2. Retrieve Groq key from Vault
  3. Retrieve OpenRouter key from Vault
  ↓
Use keys for API calls
  ↓
Never expose keys to client
```

**Benefits:**
- Keys never in .env file
- Rotate keys without redeploying
- Audit key access
- Centralized management

---

### 2.4 LLM Providers

#### Gemini (Google)
- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/`
- **Models:** gemini-1.5-pro, gemini-1.5-flash
- **Rate Limit:** 60 req/min
- **Features:** Web search capability, long context
- **Use Case:** Business news (requires search), general knowledge

#### Groq
- **Endpoint:** `https://api.groq.com/openai/v1/`
- **Models:** mixtral-8x7b-32768 (fast)
- **Rate Limit:** 30 req/min
- **Features:** Ultra-fast inference
- **Use Case:** General knowledge, creative queries

#### OpenRouter (Fallback Aggregator)
- **Endpoint:** `https://openrouter.ai/api/v1/`
- **Models:** Aggregates 100+ models
- **Rate Limit:** Provider-dependent
- **Features:** Fallback for any model
- **Use Case:** Tertiary fallback when primary/secondary unavailable

---

## 3. Data Flow Diagrams

### 3.1 Successful Query Flow (Online)

```
User enters query
      ↓
App: Send to backend
      ↓
Backend: Classify query
      ↓
Backend: Select providers
      ↓
Backend: Check rate limits
      ↓
Backend: Call Groq (example)
      ↓
Groq: Returns response
      ↓
Backend: Update response metadata
      ↓
Backend: Return to app
      ↓
App: Display response + "Using Groq"
      ↓
App: Store in SQLite cache (7-day TTL)
      ↓
App: Response cleared on app close or after TTL expires
```

### 3.2 Failover Flow (Primary Provider Unavailable)

```
User enters query
      ↓
App: Send to backend
      ↓
Backend: Classify & select providers
      ↓
Backend: Try Gemini (rate limited)
      ↓
Backend: Try Groq (success!)
      ↓
Backend: Return response + "Primary unavailable, using Groq"
      ↓
App: Display warning badge
      ↓
App: Cache response (7-day TTL)
      ↓
App: Response not persisted to history
```

### 3.3 Offline Query Flow

```
User enters query (no internet)
      ↓
App: Detects offline
      ↓
App: Store query to offline_queue table
  - status: "pending"
  - created_at: now
      ↓
App: Show "Query saved. Will sync when online."
      ↓
User: Gets internet back
      ↓
App: Detects online (via NetInfo)
      ↓
App: Fetch pending queries from offline_queue
      ↓
App: POST pending queries to /api/queue/sync
      ↓
Backend: Process queued requests
      ↓
Backend: Return responses
      ↓
App: Store responses to offline_responses table
      ↓
App: Update offline_queue status to "synced"
      ↓
App: Display responses (not persisted to history)
      ↓
App: Clear offline_responses after display or on app close
```

### 3.4 Rate Limiting Flow

```
Request comes in
      ↓
Backend: Check rate limiter state
      ↓
Try primary provider (check rate limit)
  → If rate limited, try secondary
      ↓
Try secondary provider (Groq)
  → If rate limited, try tertiary
      ↓
Try tertiary provider (OpenRouter)
  → If rate limited or fails, return error
      ↓
If success → Return response { response, llm_used, category }
If all fail → Return error { error: "All providers unavailable" }
App receives error → Queues request locally for retry when online
```

---

## 4. Data Models

### 4.1 Query Request (App → Backend)

```json
{
  "query": "What is the latest AI news?",
  "timestamp": "2025-11-13T10:30:00Z"
}
```

### 4.2 Query Response (Backend → App)

```json
{
  "response": "Recent AI news includes...",
  "llm_used": "Gemini",
  "category": "business_news",
  "confidence": 0.95,
  "response_time_ms": 2500,
  "timestamp": "2025-11-13T10:30:05Z",
  "failover_chain": ["Gemini"],
  "cached": false
}
```

### 4.3 Classification Response

```json
{
  "category": "business_news",
  "confidence": 0.95,
  "alternatives": [
    { "category": "general_knowledge", "confidence": 0.04 },
    { "category": "creative", "confidence": 0.01 }
  ]
}
```

### 4.4 SQLite Tables

**offline_queue** (for queries sent while offline)
```sql
CREATE TABLE offline_queue (
  id INTEGER PRIMARY KEY,
  query_text TEXT NOT NULL,
  timestamp DATETIME,
  status TEXT, -- pending, synced
  created_at DATETIME
);
```

**offline_responses** (responses when queue syncs)
```sql
CREATE TABLE offline_responses (
  id INTEGER PRIMARY KEY,
  queue_id INTEGER,
  response_text TEXT,
  llm_used TEXT,
  synced_at DATETIME,
  FOREIGN KEY(queue_id) REFERENCES offline_queue(id)
);
```

**cache** (7-day TTL cache for responses)
```sql
CREATE TABLE cache (
  query_hash TEXT PRIMARY KEY,
  response_text TEXT,
  llm_used TEXT,
  category TEXT,
  created_at DATETIME,
  expires_at DATETIME -- 7 days from creation
);
```

**Note:** No history table. Responses are temporary (cache TTL or cleared on app close).

---

## 5. Technology Stack

**See `03_tech_stack.md` for complete technology stack documentation including versions, dependencies, tool backups, and installation instructions.**

**Quick Reference:**
- **Frontend:** React Native (Expo) + Redux + axios + react-native-sqlite-storage
- **Backend:** Node.js + Express on Render (free tier)
- **APIs:** Gemini, Groq, OpenRouter with Supabase Vault for key management
- **Distribution:** Direct APK via GitHub Releases

---

## 6. Deployment Architecture

```
┌──────────────────────────────────────────┐
│        GitHub Repository                 │
│  /askme (project root)                   │
│  ├── /backend (Node.js/Python)           │
│  │   ├── src/                            │
│  │   ├── package.json / requirements.txt │
│  │   └── Render.yaml                     │
│  └── /app (React Native/Flutter)         │
│      ├── src/                            │
│      ├── app.json / pubspec.yaml         │
│      └── build/ (APK artifacts)          │
└──────────────────────────────────────────┘
          │                    │
          │                    │
    ┌─────▼────────┐   ┌──────▼──────┐
    │  Render      │   │   GitHub    │
    │  Backend     │   │   Releases  │
    │  (Deployed)  │   │   (APK)     │
    └──────────────┘   └─────────────┘
```

---

## 7. Scaling Considerations (Future)

**Current MVP (10 users, 10 QPM):**
- Single Render instance sufficient
- Single rate limiter in memory
- SQLite in app (no cloud DB)

**Phase 2 (100 users, 100 QPM):**
- Render standard instance
- Redis for distributed rate limiting
- PostgreSQL for request queue persistence
- Monitoring/alerting

**Phase 3 (1000+ users):**
- Load balancer
- Multiple backend instances
- Caching layer (Redis)
- Database replication
- CDN for APK distribution

---

## 8. Security Architecture

```
┌─────────────────────────────────────┐
│   Security Layers                   │
├─────────────────────────────────────┤
│                                     │
│  Layer 1: App Security              │
│  - No API keys in APK               │
│  - All calls through backend        │
│  - HTTPS only                       │
│  - SQLite encryption (optional)     │
│                                     │
│  Layer 2: Backend Security          │
│  - API keys in Supabase Vault       │
│  - Input validation                 │
│  - Rate limiting                    │
│  - HTTPS/TLS                        │
│                                     │
│  Layer 3: Data Privacy              │
│  - Queries: offline queue only      │
│  - Responses: 7-day cache + cleared │
│  - No history persistence           │
│  - No cloud sync                    │
│  - No user accounts                 │
│  - No tracking                      │
│                                     │
│  Layer 4: Provider Security         │
│  - Official APIs only               │
│  - Encrypted communication          │
│                                     │
└─────────────────────────────────────┘
```

---

## 9. Monitoring & Observability

**Backend Monitoring (Render):**
- Request logs: all API calls
- Error logs: failures and exceptions
- Response times: performance metrics
- Rate limiter state: current limits

**App Monitoring (Optional):**
- Crash analytics (Crashlytics/Sentry)
- User feedback forms
- Error logs (local)
- Cache hit rate

**Metrics to Track:**
- Avg response time (target <10s)
- Provider failover rate
- Cache hit rate (target >60%)
- Offline queue depth (max 10 pending)
- Rate limit hits per provider
- Cache TTL expiration rate

---

## 10. Architecture Summary

**Three-Tier System:**
1. **Client Tier** (Android app)
   - Minimalist GUI
   - Local SQLite: offline queue + 7-day cache only (no history)
   - Offline queueing & sync
   - Fresh start on app launch

2. **API Tier** (Render backend)
   - Query classification
   - Provider selection & failover
   - Rate limiting
   - Stateless (no session storage)

3. **External Tier** (LLM providers)
   - Gemini, Groq, OpenRouter APIs
   - Supabase Vault for keys (server-side)

**Key Design Principles:**
- ✅ **Privacy-first:** No history, temporary cache only (7-day TTL)
- ✅ **Fault-tolerant:** Failover chain for reliability
- ✅ **Offline-capable:** Queue and sync when online
- ✅ **Stateless:** Fresh app start, no session persistence
- ✅ **Simple:** Minimalist interface and architecture
- ✅ **Scalable:** Render + stateless backend design

---

**Document Status:** ✅ **Complete**
**Ready for:** Implementation & Development
