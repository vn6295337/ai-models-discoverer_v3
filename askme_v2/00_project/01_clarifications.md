# AskMe Mobile App - Project Clarifications

**Status:** Awaiting answers
**Date:** 2025-11-13
**Purpose:** Define project requirements before architecture and implementation

---

## Module 1: Query Classification

**Q1.1:** Use lightweight classifier model or call an LLM to detect intent?
- [ ] On-device lightweight model
- [x] API call to LLM classifier
- [ ] Hybrid approach
- **Answer:**
- **✅ Comment:** API-based classification is correct. Avoids on-device complexity and leverages existing LLM infrastructure.

**Q1.2:** Which query categories/intent types do we need to classify?
- Examples: code, general, math, creative, translation, etc.
- **Answer:** business news, general knowledge, creative.  the first 2 requires web access
- **✅ Comment:** Three categories are clear and routing-friendly. Both news/knowledge requiring web access will drive provider selection (Gemini/Groq both have search capabilities).

**Q1.3:** Classification location - on-device or API?
- [ ] Run classifier on Android device
- [x] Call API for classification
- **Answer:**
- **✅ Comment:** Consistent with Q1.1. Confirmed: classification happens via API call (same LLM call that classifies will help route query).

---

## Module 2: Inference Providers & Routing

**Q2.1:** Which free inference APIs are you using?
- Examples: Together AI, HuggingFace Inference, Replicate, Ollama, Mistral API, etc.
- **Answer:** Free tiers of Gemini, Groq, Openrouter
- **✅ Comment:** Excellent choice. Strong coverage: Gemini (web search), Groq (speed + web search), OpenRouter (aggregator + fallback). Different rate limit profiles = good redundancy.

**Q2.2:** API credentials management
- Single API key per provider?
- Multiple keys for load balancing?
- Separate accounts?
- **Answer:** Currently I have single API per provider... what is your suggestion?
- **✅ APPROVED Comment:** Single API key per provider is sufficient for MVP (10 users, 10 QPM). Keep it simple. Add key rotation/pooling later if hitting rate limits. Recommendation: Yes, proceed with single key per provider.

**Q2.3:** Expected concurrent user load
- How many simultaneous users?
- Estimated queries per minute?
- **Answer:** 10 users, 10 queries per min
- **✅ Comment:** Modest scale. This means: ~6 req/sec average, spiky bursts. All three providers can handle this easily on free tier. No need for sophisticated load balancing in MVP.

---

## Module 3: Multi-User API Pooling

**Q3.1:** Multi-user routing behavior
- [ ] Share same API key across all users
- [ ] Load balance requests to same provider
- [ ] Manage rate limits centrally
- [ ] Other: _______________
- **Answer:** No sure, what is your suggestion?
- **💡 RECOMMENDATION:** Share same API key + manage rate limits centrally
  - All users routed through single API key per provider (Gemini, Groq, OpenRouter each get one key)
  - Rate limiting happens server-side (backend enforces fair sharing)
  - Simpler than per-user key management
  - No per-user quota complexity needed at 10 QPM scale
  - Load balance across providers based on availability/latency

**Q3.2:** Rate limiting strategy
- Per user? Per provider? Global?
- What are the limits (tokens/min, requests/min)?
- **Answer:** Global rate limiting (see Q7.2 for actual limits)
- **✅ Comment:** Global rate limiting (not per-user) is simpler for MVP. Server-side enforcement. Free tier limits (from Q7.2):
  - Gemini: 60 req/min, 2M tokens/day
  - Groq: 30 req/min
  - OpenRouter: aggregator coverage
  - Queue design: Max queue depth = 10 requests (modest scale), retry every 30sec if rate limited

**Q3.3:** User isolation
- Do users need isolated sessions/caches?
- Can users see each other's queries/responses?
- **Answer:** 1. No idea 2. No
- **✅ RECOMMENDATION:** Keep it simple for MVP
  - Each user's phone = isolated local session (own cache only)
  - No shared session server needed (backend stateless)
  - No multi-device sync in MVP
  - Sessions automatically isolated per-device
  - No history persistence (fresh start on each app launch)
  - Answers "no" to shared responses = users can't see each other's queries (good for privacy)

---

## Module 4: Failover & Reliability

**Q4.1:** Failover strategy
- [ ] Different LLM per query category (category-specific fallback)
- [ ] Generic fallback model for any query
- [x] Multiple fallbacks (primary → secondary → tertiary)
- **Answer:**
- **✅ Comment:** Multiple fallbacks (primary → secondary → tertiary) is production-appropriate for your scale. Smart choice. Examples:
  - Business news query: Gemini (primary, has search) → Groq (secondary, has search) → OpenRouter (tertiary, generic)
  - Creative query: Groq (primary, fast) → Gemini (secondary) → OpenRouter (tertiary)

**Q4.2:** Retry behavior
- [x] Immediate retry
- [ ] Exponential backoff (delays increase)
- [x] Queue failed requests
- [ ] Other: _______________
- Max retry attempts?
- **Answer:**
- **✅ Comment:** Good balance of responsiveness + reliability. Immediate retry catches transient errors. Queue handles rate limits gracefully. **Need clarification:** Max retry attempts? (Suggest: 3 retries before failover to next provider)

**Q4.3:** User notification on failover
- [ ] Silent fallback (no notification)
- [x] Show which LLM was used
- [x] Warn user on secondary LLM
- **Answer:**
- **✅ Comment:** Excellent UX transparency. Shows user:
  - Primary LLM used (or "used Groq")
  - If using secondary/tertiary: "Primary unavailable, using Groq as backup"
  - Helps users understand why response might differ in style/length

---

## Module 5: Offline Capability

**Q5.1:** Offline response handling
- [ ] Cache previous responses, serve from cache
- [ ] Pre-download model weights for on-device inference
- [x] Queue queries, sync when online
- [ ] Combination: _______________
- **Answer:**
- **✅ Comment:** Queue + sync when online is correct for 2-week MVP. Rationale:
  - Simpler than caching + fallback
  - Users expect "offline = wait, then retry" behavior
  - No on-device LLM complexity
  - Local SQLite queue = reliable retry

**Q5.2:** Cache/storage strategy
- Cache size limit?
- Cache expiration (TTL)?
- Which responses to cache (all or selective)?
- **Answer:** No idea
- **💡 RECOMMENDATIONS (for local mobile cache):**
  - Cache size limit: 50MB (stores ~1000 medium responses, reasonable for mobile)
  - TTL (Time-to-Live): 7 days (responses valid for a week, then re-fetch)
  - Cache all responses (don't selective cache in MVP—simpler logic, no filtering rules)
  - Storage: Android SharedPreferences or SQLite for structured queries

**Q5.3:** On-device inference (if using local models)
- Model size constraints (device storage)?
- Which query types support on-device?
- Memory/CPU requirements acceptable?
- **Answer:** Not applicable.. not using local models
- **✅ Comment:** Correct. No on-device inference in MVP. All queries go to cloud APIs (Gemini, Groq, OpenRouter). Local storage is only for caching responses and queueing requests.

---

## Module 6: Android Implementation

**Q6.1:** UI/Interface type
- [ ] CLI (terminal-based, Termux style)
- [ ] Minimalist GUI (simple text input + output)
- [x] Hybrid (CLI + GUI modes)
- **Answer:**
- **⚠️ CONCERN + RECOMMENDATION:** Hybrid is ambitious for 2-week timeline.
  - CLI adds: terminal detection, input parsing, output formatting, testing overhead
  - GUI gives you: single codebase, React Native/Flutter reuse for iOS
  - **Suggestion:** Focus MVP on minimalist GUI only (defer CLI to Phase 2 post-launch)
  - GUI-first = deliverable in 2 weeks, CLI can follow in sprint 2  ---- OK with this

**Q6.2:** Backend architecture
- [ ] Separate backend service (Node.js/Python server)
- [ ] Embedded in app (API calls directly from Android)
- [ ] Hybrid (local service + cloud backup)
- **Answer:** No idea
- **🚨 STRONG RECOMMENDATION:** Separate backend service (Node.js or Python)
  - **Why:**
    - Centralized rate limiting across all users
    - API key management (keys stay on server, not exposed in APK)
    - Query routing logic (classification → provider selection)
    - Request queueing for offline sync
    - Easy to maintain and debug across both Android + iOS
  - **Infrastructure:** MVP runs on free tier (Railway, Render, Heroku) --- already have Render. Also stored API keys in Supabase secrets.
  - **Alternative (Embedded):** Simpler but exposes API keys in app binary, no central rate limiting --- No need then
  - **Decision impact:** Required for production reliability + shared iOS backend (Q6.4)

**Q6.3:** App distribution
- Google Play Store?
- Direct APK distribution?
- F-Droid (open source)?
- **Answer:** all 3 possible?
- **✅ PHASED APPROACH (Recommended):**
  - **Phase 1 (Weeks 1-2):** Direct APK distribution (fastest, no approval delays, get feedback)
  - **Phase 2 (Month 2):** F-Droid (open source registry, faster than Play Store, good for privacy-focused users)
  - **Phase 3 (Month 3):** Google Play Store (larger audience, but compliance requirements, review delays)
  - **For MVP:** Focus on APK distribution + F-Droid preparation ---- ok

**Q6.4:** iOS requirement timeline
- Android only initially?
- iOS support later (timeline)?
- Shared backend for both?
- **Answer:** shared backend
- **✅ APPROVED:** Shared backend = smart decision. Means:
  - Single backend API serves both Android + iOS apps
  - Rate limiting, API keys, caching = managed once
  - No duplicate infrastructure
  - iOS app can reuse same backend logic (maybe different UI framework)

---

## Module 7: Additional Constraints

**Q7.1:** Data privacy/storage
- Store queries/responses locally?
- Sync to cloud storage?
- User authentication required?
- **Answer:** 1. Yes 2. No 3. No
- **✅ Comment:** Good privacy stance. Means:
  - Queries + responses stored on device only (SQLite)
  - No server-side history/sync
  - No user accounts = simpler backend
  - User controls their data completely

**Q7.2:** Cost considerations
- API costs acceptable (free tier limits)?
- Infrastructure (backend hosting)?
- **Answer:** All free to use models (rate limited)
- **✅ Comment:** Excellent constraint. All three providers (Gemini, Groq, OpenRouter) have generous free tiers:
  - Gemini: 60 req/min, 2M tokens/day
  - Groq: 30 req/min
  - OpenRouter: aggregator, covers multiple models
  - Backend hosting: Free tier (Railway/Render/Heroku = sufficient)
  - Cost = $0 for MVP + early users

**Q7.3:** Development timeline
- Target launch date?
- MVP features vs. phase 2?
- **Answer:** in a couple of weeks
- **✅ TIMELINE:** 2 weeks for GUI-only MVP
  - **MVP (Weeks 1-2):** Minimalist GUI search + 3 providers + failover + offline queue + APK
  - **Phase 2 (Weeks 3-4):** CLI mode + F-Droid + iOS
  - Status: GUI-only MVP confirmed (Q6.1)

---

## ✅ DECISIONS FINALIZED

| Decision | Status | Details |
|----------|--------|---------|
| **Query Classification** | ✅ Approved | API-based classification (using LLM), 3 categories: business news, general knowledge, creative |
| **Providers** | ✅ Approved | Gemini (60 req/min, 2M tokens/day), Groq (30 req/min), OpenRouter (aggregator) |
| **API Keys** | ✅ Approved | Single key per provider, centrally managed in Supabase secrets |
| **Multi-User Routing** | ✅ Approved | Shared API keys, global rate limiting (queue depth: 10 requests), load balance across providers |
| **Failover Strategy** | ✅ Approved | Primary → Secondary → Tertiary per query type, show LLM used, warn on secondary |
| **Offline Capability** | ✅ Approved | Queue queries + sync when online, 50MB local cache, 7-day TTL, SQLite storage |
| **UI/Interface** | ✅ Approved | Minimalist GUI only (defer CLI to Phase 2) |
| **Backend** | ✅ Approved | Separate service (Node.js or Python), Render hosting (existing account), Supabase for API key secrets |
| **Distribution** | ✅ Approved | Phase 1: Direct APK, Phase 2: F-Droid, Phase 3: Play Store |
| **iOS Support** | ✅ Approved | Shared backend, iOS app in Phase 2 |
| **Data Privacy** | ✅ Approved | Local-only storage (SQLite), no cloud sync, no user auth |
| **Tech Stack** | 🤔 Pending | Backend: (decide Node.js or Python), Android: (decide React Native or Flutter), Hosting: Render ✅ |

---

## 🎯 NEXT PHASE

Ready to proceed: **Architecture Design → Implementation Checklist → Development**

