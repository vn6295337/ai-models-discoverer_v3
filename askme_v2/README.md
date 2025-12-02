# AskMe Mobile App

**Version**: 0.1.0 (MVP)
**Status**: In Development 
**Timeline**: 2-week MVP launch

An intelligent LLM query router for Android that automatically routes user queries to the most suitable free LLM provider (Gemini, Groq, OpenRouter) based on query classification, with built-in failover, offline queueing, and privacy-first design.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              ASKME MOBILE APP (MVP)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Android App (React Native + Expo)                          │
│  ├── Search UI + Response Display                           │
│  ├── Offline Queue (SQLite)                                 │
│  └── 7-day Response Cache (Privacy-focused)                 │
│           ↓ [HTTP / Offline Detection]                      │
│  Backend API (Node.js + Express on Render)                  │
│  ├── Query Classification (Keyword-based)                   │
│  ├── Provider Routing (Gemini/Groq/OpenRouter)              │
│  ├── Failover Chain (Primary → Secondary → Tertiary)        │
│  └── Global Rate Limiting                                   │
│           ↓ [Supabase Vault]                                │
│  LLM Providers                                              │
│  ├── Google Gemini (60 req/min, web search)                 │
│  ├── Groq (30 req/min, ultra-fast)                          │
│  └── OpenRouter (Fallback aggregator)                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Project Goals

**MVP Scope (2 weeks):**
- ✅ Minimalist Android GUI (search interface)
- ✅ Intelligent query classification (3 categories: news, general, creative)
- ✅ Multi-provider failover (Gemini → Groq → OpenRouter)
- ✅ Offline queueing & sync
- ✅ Privacy-first (local storage only, no history)
- ✅ Direct APK distribution
- ✅ Backend deployed on Render (free tier)

**Phase 2:** CLI mode, F-Droid distribution, iOS support
**Phase 3:** Play Store, per-user quotas, advanced scaling

## Quick Start

### Backend Setup

```bash
cd askme-backend
npm install
npm run dev
# Server running on http://localhost:3000
```

### Frontend Setup (When Ready)

```bash
npx create-expo-app askme
cd askme
npm install
npm run android  # or iOS
```

### Configuration

Backend requires `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-public-key
PORT=3000
NODE_ENV=development
```

**Note:** API keys for Gemini, Groq, OpenRouter are stored in Supabase Vault (server-side only).

## Key Features

- **Intelligent Classification**: Keyword-based query routing (instant, no LLM call overhead)
- **Multi-Provider Failover**: Automatic fallback chain ensures reliability
- **Offline-First**: Queue queries locally, sync when online
- **Privacy-Focused**: No history, temporary cache only (7-day TTL), local storage only
- **Zero Configuration**: No API keys needed in app or local config
- **Free to Use**: All free-tier LLM providers, free backend hosting (Render)
- **Minimal Size**: <50MB APK, lightweight architecture

## Tech Stack

| Layer        | Technology                | Notes                      |
| ------------ | ------------------------- | -------------------------- |
| **Frontend** | React Native (Expo 51+)   | Android app, clean UI      |
| **Backend**  | Node.js 18+ LTS (Express) | Stateless, Render-hosted   |
| **Database** | SQLite (mobile)           | Offline queue + cache only |
| **LLM APIs** | Gemini, Groq, OpenRouter  | Free tiers, rate-limited   |
| **Secrets**  | Supabase Vault            | Server-side key management |
| **Hosting**  | Render (free tier)        | Auto-deploy from GitHub    |

## API Endpoints

### Health Check
```bash
GET /api/health
# Response: { status: "ok" }
```

### Query Processing
```bash
POST /api/query
# Request: { "query": "What is AI?" }
# Response: { "response": "...", "llm_used": "Groq", "category": "general_knowledge" }
```

### Offline Sync
```bash
POST /api/queue/sync
# Request: { "queries": [...] }
# Response: { "responses": [...] }
```

## Development

### Backend Commands

```bash
cd askme-backend

# Install dependencies
npm install

# Development (watch mode)
npm run dev

# Tests
npm test
npm run test:watch

# Linting
npm run lint
npm run lint:fix

# Deployment
git push origin main  # Auto-deploys to Render
```

### Testing API Locally

```bash
# Health check
curl http://localhost:3000/api/health

# Query
curl -X POST http://localhost:3000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is quantum computing?"}'
```

## Data Privacy

✅ **What we do:**
- Store queries + responses locally on device only
- Cache responses for 7 days (performance + privacy balance)
- Manage API keys server-side (Supabase Vault)
- No user authentication required
- No cloud sync

❌ **What we don't do:**
- Store query history
- Track user behavior
- Collect personal data
- Expose API keys in APK
- Require user accounts

## Documentation

- **`01_charter.md`** — Project vision, goals, success criteria
- **`03_architecture.md`** — Detailed system design, data flows, components
- **`03_tech_stack.md`** — Technology versions, dependencies, setup
- **`askme-backend/README.md`** — Backend-specific docs
- **`CLAUDE.md`** — Developer guide for Claude Code

## Troubleshooting

### Backend Won't Start
```bash
# Check Node version (must be 18+)
node --version

# Clear cache
rm -rf node_modules && npm install
```

### Slow Responses
- Render free tier has 15-min idle timeout (first request slower)
- Expected response time: 2-8 seconds (LLM + network)

### Rate Limiting (429 errors)
- Backend will try failover chain automatically
- App queues locally if all providers fail
- Check Render logs for rate limit state

## Distribution

**Phase 1:** Direct APK distribution (fastest MVP)
**Phase 2:** F-Droid (open-source friendly)
**Phase 3:** Google Play Store

## License

MIT License - See LICENSE file for terms

---

**For detailed architecture & development guidance, see `CLAUDE.md`**