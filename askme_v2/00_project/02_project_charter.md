# AskMe Mobile App - Project Charter

**Document Type:** Project Charter
**Project:** AskMe Mobile App - Intelligent LLM Query Router for Android
**Last Updated:** November 13, 2025
**Timeline:** 2-week MVP

---

## 📋 Version History

| Version | Date       | Changes                                             | Author       |        |
| ------- | ---------- | --------------------------------------------------- | ------------ | ------ |
| 1.0     | 2025-11-13 | Initial charter based on requirements clarification | Changes      | Author |

---

## 📑 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [MVP Goals](#3-mvp-goals)
4. [Success Metrics](#4-success-metrics)
5. [Project Roadmap](#5-project-roadmap)

---

## 1. Project Overview

### 1.1 Project Mission

Deliver a simple, minimalist mobile app that intelligently routes user queries to the most suitable free LLM provider based on query classification, with built-in failover and offline queueing.

### 1.2 Core Value Proposition

- **Smart Query Routing:** AI-detected query classification (business news, general knowledge, creative) automatically selects best LLM
- **Automatic Failover:** Primary → Secondary → Tertiary provider fallback when unavailable
- **Minimalist Interface:** Lightweight, search-box-like GUI (Google Search experience)
- **Privacy-First:** Queries & responses stored locally only, no cloud sync, no user accounts
- **Offline Support:** Queue queries when offline, auto-sync when reconnected
- **Zero Cost:** All free-tier LLM providers with rate limiting

---

## 2. Problem Statement

### 2.1 Current Market Issues

Users need a simple way to access multiple free LLM providers via a mobile interface without managing API keys, handling rate limits, or learning complex interfaces.

**Current Gaps:**

2.1.1. **Fragmented LLM Access**
- Different apps for different providers (ChatGPT, Gemini, Groq, etc.)
- No unified query routing interface
- Manual provider switching required

2.1.2. **API Complexity & Rate Limits**
- Users exposed to rate limiting errors
- No intelligent failover when primary provider unavailable
- Requires advanced knowledge to manage multiple API keys

2.1.3. **Privacy & Data Concerns**
- Most mobile apps collect user data
- Cloud storage of queries
- Mandatory user authentication

2.1.4. **Poor Offline Experience**
- Apps fail when network unavailable
- No query queueing or offline support

---

## 3. MVP Goals

### 3.1 Core Features

**3.1.1. Minimalist GUI Search Interface**
- **Target:** Simple search box + response display (Google Search UX)
- **Deliverable:** Android React Native or Flutter app
- **Requirements:**
  - Text input field
  - Search button + voice input (optional)
  - Response display with LLM label
  - Failover warning notification

**3.1.2. Intelligent Query Classification**
- **Target:** Fast, keyword-based classification of query type
- **Categories:** Business news, general knowledge, creative
- **Implementation:** Keyword-based routing on backend (no LLM call needed)
  - Keywords like "news", "latest", "today" → Gemini (web search)
  - Keywords like "write", "poem", "creative", "story" → Groq (creative)
  - Default → Groq (fast, general knowledge)
- **Deliverable:** Backend classification service

**3.1.3. 3-Provider LLM Integration**
- **Providers:**
  - Gemini (60 req/min, 2M tokens/day) - primary for news/knowledge
  - Groq (30 req/min) - primary for general/creative
  - OpenRouter (aggregator) - fallback
- **Implementation:** Backend API with global rate limiting
- **Deliverable:** Backend service deployed on Render (free tier)
- **Architecture:** Reusable API for future iOS deployment

**3.1.4. Failover & Retry Logic**
- **Strategy:** Global failover chain (no per-category routing)
  - Primary: Context-based (Gemini for news, Groq for others)
  - Secondary: Groq (universal backup)
  - Tertiary: OpenRouter (final fallback)
- **Behavior:** If all providers fail, return error to app immediately (backend is stateless)
- **App Response:** App queues failed request locally for retry when online
- **Notification:** Show which LLM used, warn if secondary/tertiary used
- **Deliverable:** Failover orchestration in backend

**3.1.5. Offline Queueing**
- **Target:** Queue queries when offline, auto-sync when online
- **Implementation:** Local SQLite queue on device
- **Storage:** 50MB cache, 7-day TTL, all responses cached
- **Deliverable:** Local queue manager on Android app

**3.1.6. Privacy-First Architecture**
- **Local Storage Only:** Queries + responses stored on device (SQLite)
- **No Cloud Sync:** No server-side history
- **No User Auth:** Anonymous usage
- **Key Management:** API keys stored in Supabase secrets (server-side only)
- **Deliverable:** SQLite persistence layer

**3.1.7. Direct APK Distribution**
- **Target:** Quick MVP release without Play Store review
- **Implementation:** APK artifact from build
- **Feedback:** Immediate user feedback without approval delays
- **Deliverable:** Signed APK file

### 3.2 Success Criteria (MVP - Android)

✅ **Functional Requirements:**
- [ ] User can input query → receive response from LLM
- [ ] Query classification works (detects news vs. general vs. creative)
- [ ] Primary provider returns response successfully
- [ ] Failover works when primary unavailable
- [ ] Response shows which LLM was used
- [ ] App works offline (queues requests)
- [ ] Queries/responses persist locally
- [ ] APK can be installed and launched on Android device

✅ **Quality Requirements:**
- [ ] App launches in <3 seconds
- [ ] Response time <10 seconds (LLM + network)
- [ ] No crashes on error scenarios
- [ ] No data leaves device (local only)
- [ ] APK size <50MB

---

## 4. Success Metrics

### 4.1 Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| App Launch Time | <3 seconds | TBD |
| Query Response Time | <10 seconds | TBD |
| APK Size | <50MB | TBD |
| Cache Hit Rate | >60% (offline) | TBD |
| Uptime | >99% | TBD |

### 4.2 Reliability Targets

| Metric | Target | Status |
|--------|--------|--------|
| Failover Accuracy | 100% | TBD |
| Zero Crashes | 0 crashes in 100 queries | TBD |
| Classification Accuracy | >90% | TBD |
| Queue Sync Success | 100% when online | TBD |

### 4.3 Privacy Targets

| Metric | Target | Status |
|--------|--------|--------|
| Data Stored Locally | 100% queries/responses | TBD |
| Cloud Sync | 0 bytes | TBD |
| User Accounts | Not required | TBD |
| API Keys Exposed | 0 (server-side only) | TBD |

---

## 5. Project Roadmap

### Timeline Overview

```
Phase: Backend + Core Features
├── Days 1-2: Backend setup (Node.js or Python)
├── Days 2-3: LLM provider integration (Gemini, Groq, OpenRouter)
├── Days 3-4: Classification logic
├── Days 4-5: Rate limiting + failover
└── Days 5-6: Testing + deployment to Render

Phase: Android App + Integration + Delivery
├── Days 1-2: React Native/Flutter setup
├── Days 2-3: GUI search interface
├── Days 3-4: Backend API integration
├── Days 4-5: Offline queueing + caching
├── Days 5-6: Testing + bug fixes
└── Days 6-7: APK signing + release
```

### Deliverables

**MVP Launch:**
- ✅ Backend API service (deployed on Render)
- ✅ Android app with minimalist GUI
- ✅ Signed APK for distribution
- ✅ Documentation (setup, usage, API docs)
- ✅ Offline query queueing + caching (SQLite)
- ✅ Intelligent failover (Primary → Secondary → Tertiary)

---

## 7. Technical Stack

### Approved Decisions

| Component | Status | Details |
|-----------|--------|---------|
| Backend Language | ✅ Node.js | JavaScript everywhere (single language) |
| Android Framework | ✅ React Native (Expo) | Same language as backend, fast MVP development |
| Hosting | ✅ Render | Existing account, free tier |
| API Key Storage | ✅ Supabase | Secure secrets management |
| LLM Providers | ✅ Finalized | Gemini, Groq, OpenRouter |
| Local Storage | ✅ SQLite | Device-only, 50MB cache |
| Rate Limiting | ✅ Global | Server-side enforcement |
| Distribution | ✅ APK | Direct APK distribution |

---

## 8. Risk Assessment

### High Priority Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Provider rate limits exceeded | Medium | High | Queue requests, load balance |
| API key exposure | Low | Critical | Server-side key storage in Supabase |
| Network connectivity issues | Medium | Medium | Offline queueing + sync |
| Classification errors | Medium | Low | Show which LLM used, allow retry |

### Timeline Risk

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Backend deployment delays | Medium | Use Render (pre-configured) |
| LLM provider API changes | Low | Use OpenRouter as fallback aggregator |
| Network/connectivity issues | Medium | Offline queueing + SQLite cache |

---

## 9. Success Definition

### MVP Success Criteria

**Functional:**
- ✅ User submits query → receives response in <10 seconds
- ✅ Response comes from appropriate LLM (classified correctly)
- ✅ Failover works when primary unavailable
- ✅ App works offline (queues + syncs)
- ✅ No data leaves the device

**Technical:**
- ✅ Backend deployed on Render, stable
- ✅ Android app launches and runs without crashes
- ✅ APK <50MB, all features functional
- ✅ Security: No API keys exposed, all local storage

**Distribution:**
- ✅ APK signed and ready for download
- ✅ Users can install via direct APK without Play Store
- ✅ Documentation for APK installation and usage

---

## 10. Charter Sign-Off

**Project Approval:**
- **Vision:** ✅ Clear (intelligent mobile LLM router)
- **Scope:** ✅ Defined (Android GUI MVP, minimalist interface)
- **Timeline:** ✅ Confirmed (2-week MVP delivery)
- **Resources:** ✅ Identified (Backend, Android dev, Render hosting, Supabase secrets)
- **Success Metrics:** ✅ Defined (functional, performance, privacy)

**Charter Status:** ✅ **APPROVED**
**Project Status:** 🚀 **READY TO START ARCHITECTURE & IMPLEMENTATION**

---

*This charter defines the AskMe Mobile App vision, scope, and success criteria for the MVP. Proceed to Architecture Design (02_architecture.md) and Implementation Checklist (03_implementation_checklist.md).*

**Document Status:** ✅ **Complete and Ready for Development**
