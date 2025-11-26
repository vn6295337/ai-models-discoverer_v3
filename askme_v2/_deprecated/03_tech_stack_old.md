# AskMe - Tech Stack

**Project:** Mobile LLM Query Router (Android)
**Updated:** 2025-11-14
**Status:** MVP Ready

---

## 1. Frontend Stack (Android App)

### 1.1 Core

| Tool | Version | Purpose |
|------|---------|---------|
| React Native (Expo) | 51+ | Mobile framework |
| Node.js | 18 LTS | Runtime |
| npm | 9+ | Package manager |
| Expo CLI | 51+ | Build & deploy |

### 1.2 State & Storage

| Tool                            | Version | Purpose               |
| ------------------------------- | ------- | --------------------- |
| Redux Toolkit                   | 1.9+    | State management      |
| @react-native-community/netinfo | 9.3+    | Network detection     |
| react-native-sqlite-storage     | 6.0+    | Local SQLite database |

### 1.3 Networking & HTTP

| Tool | Version | Purpose |
|------|---------|---------|
| axios | 1.4+ | HTTP client (with retry on network errors) |
| @react-navigation/native | 6.0+ | Navigation |


---

## 2. Backend Stack (Node.js)

### 2.1 Core

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 18 LTS | Runtime |
| Express.js | 4.18+ | Web framework |
| npm | 9+ | Package manager |

### 2.2 LLM Providers & APIs

| Tool | Version | Purpose |
|------|---------|---------|
| @google/generative-ai | Latest | Gemini API client |
| groq-sdk | Latest | Groq API client |
| openrouter-js | Latest | OpenRouter client |
| @supabase/supabase-js | 2.33+ | API key vault (Supabase) |
| axios | 1.4+ | HTTP client |

### 2.3 Middleware & Routing

| Tool | Version | Purpose |
|------|---------|---------|
| express-rate-limit | 6.7+ | Rate limiting (global per provider) |
| cors | 2.8+ | CORS handling |
| helmet | 7.0+ | Security headers |
| morgan | 1.10+ | HTTP logging |
| dotenv | 16.0+ | Environment config |

### 2.4 Deployment

| Tool |  |
|------|---|
| Render | Free tier hosting |
| render.yaml | Deployment config |

---

## 3. External Services

| Service         | Purpose                            | Plan                       |
| --------------- | ---------------------------------- | -------------------------- |
| Gemini (Google) | LLM provider                       | 60 req/min free            |
| Groq            | LLM provider                       | 30 req/min free            |
| OpenRouter      | Fallback LLM aggregator            | Free tier                  |
| Supabase        | API key vault                      | Free tier (100MB)          |
| GitHub          | Version control & APK distribution | Free                       |
| Render          | Backend hosting                    | Free tier (0.5 CPU, 512MB) |

---

## 4. Backup Plans

**Frontend:** React Native (Expo) → Flutter (full rewrite)
**State Mgmt:** Redux Toolkit → Zustand → Context API
**Database:** react-native-sqlite-storage → WatermelonDB → AsyncStorage
**HTTP:** axios → fetch API
**Backend:** Node.js + Express → Node.js + Fastify → Python + FastAPI
**Hosting:** Render → Railway → Fly.io
**LLM Failover:** Primary (context-based) → Groq → OpenRouter (global chain for all queries)
**API Keys:** Supabase Vault → AWS Secrets Manager

---

## 5. Dependencies (Pinned & Compatible)

**Compatibility verified for Node 18 LTS**

### Frontend

```json
{
  "dependencies": {
    "react": "18.2.0",
    "react-native": "0.72.4",
    "expo": "51.0.0",
    "axios": "1.6.5",
    "@reduxjs/toolkit": "1.9.7",
    "react-redux": "8.1.3",
    "@react-navigation/native": "6.1.9",
    "@react-native-community/netinfo": "9.3.11",
    "react-native-sqlite-storage": "6.0.1"
  },
  "devDependencies": {
    "expo-cli": "51.0.0",
    "jest": "29.7.0",
    "eslint": "8.54.0"
  },
  "engines": { "node": ">=18.17.0", "npm": ">=9.6.0" }
}
```

**Compatibility:**
- React 18.2.0 ← → React Native 0.72.4 ✅
- Expo 51+ bundles RN 0.72.4 ✅
- Redux Toolkit 1.9+ ← → React Redux 8.1+ ✅
- react-native-sqlite-storage 6.0+ requires RN 0.72+ ✅
- @react-navigation/native 6+ requires RN 0.63+ ✅

### Backend

```json
{
  "dependencies": {
    "express": "4.18.2",
    "axios": "1.6.5",
    "@google/generative-ai": "0.3.0",
    "groq-sdk": "0.5.0",
    "openrouter-js": "0.0.12",
    "@supabase/supabase-js": "2.38.4",
    "express-rate-limit": "6.10.0",
    "cors": "2.8.5",
    "helmet": "7.1.0",
    "morgan": "1.10.0",
    "dotenv": "16.3.1"
  },
  "devDependencies": {
    "jest": "29.7.0",
    "supertest": "6.3.3",
    "nodemon": "3.0.2"
  },
  "engines": { "node": ">=18.17.0", "npm": ">=9.6.0" }
}
```

**Compatibility:**
- All deps tested with Node 18.17.0+ ✅
- @google/generative-ai 0.3+ requires Node 18+ ⚠️ (fails on Node 16)
- groq-sdk 0.5+ requires Node 18+ ⚠️ (avoid <0.4.0)
- Express 4.18+ works with Node 18 LTS ✅
- All middleware compatible with Express 4.18 ✅

**Avoid:**
- React 17 (RN 0.72 requires 18+)
- Node 16 (LLM SDKs require 18+)
- groq-sdk <0.4.0 (missing endpoints)

---

## 6. Dependency Management

- Weekly: `npm outdated` & `npm audit`
- Monthly: Update non-breaking patches, test after major upgrades
- Major upgrades: Create branch → test → verify APK → test on device → merge

---

## 7. Setup

```bash
# Frontend
npx create-expo-app askme
cd askme && npm install
eas build --platform android

# Backend
mkdir askme-backend
cd askme-backend
npm init -y && npm install
npm run dev

# Verify
npm list && npm run lint && npm test
```

---

**Status:** ✅ MVP Ready | **Last Updated:** 2025-11-14
