# Dev Checklist

---

# PHASE 1: BACKEND DEVELOPMENT

## Section 1.1: Environment & Project Setup

- ✅ 1.1.1 Set up backend project directory (Node.js 18 LTS)
- ✅ 1.1.2 Initialize git repository: `git init`
- ✅ 1.1.3 Create package.json with Express dependency
- ✅ 1.1.4 Create .env.example with API key placeholders
- ✅ 1.1.5 Add .env to .gitignore
- ✅ 1.1.6 Create README.md with setup instructions
- ✅ 1.1.7 Install project dependencies: `npm install`
- ✅ 1.1.8 Set up environment variable loading (dotenv)

## Section 1.2: Backend Architecture & Core Setup

- ✅ 1.2.1 Create `src/index.js` - main Express server entry point
- ✅ 1.2.2 Set up Express app with middleware: `cors()`, `helmet()`, `morgan()`, `express.json()`
- ✅ 1.2.3 Implement global error handling middleware
- ✅ 1.2.4 Create health check: `GET /api/health`
- ✅ 1.2.5 Test server starts and responds to GET /api/health

## Section 1.3: Configuration Management

- ✅ 1.3.1 Create `src/config/index.js` with centralized settings
- ✅ 1.3.2 Load config from environment if needed

## Section 1.4: Database Setup

- ✅ 1.4.1 Create `src/db/schema.sql` with SQLite schema
- ✅ 1.4.2 Note: Not used in MVP (stateless backend)

## Section 1.5: API Key Management

- ✅ 1.5.1 Create Supabase account
- ✅ 1.5.2 Create project in Supabase
- ✅ 1.5.3 Add Gemini API key to Supabase Vault
- ✅ 1.5.4 Add Groq API key to Supabase Vault
- ✅ 1.5.5 Add OpenRouter API key to Supabase Vault
- ✅ 1.5.6 Create `src/utils/supabase.js` to retrieve keys from Supabase
- ✅ 1.5.7 Test API key retrieval works

## Section 1.6: Input Validation Middleware

- ✅ 1.6.1 Create `src/middleware/validate.js`
- ✅ 1.6.2 Apply validation to all endpoints

## Section 1.7: LLM Provider Integration

- ✅ 1.7.1 Create `src/providers/gemini.js`
- ✅ 1.7.2 Implement Gemini API client (models/gemini-2.0-flash)
- ✅ 1.7.3 Add method: `callGemini(query, model)`
- ✅ 1.7.4 Add rate limit tracking (60 req/min)
- ✅ 1.7.5 Add error handling & retry logic
- ✅ 1.7.6 Test Gemini integration with sample query
- ✅ 1.7.7 Create `src/providers/groq.js`
- ✅ 1.7.8 Implement Groq API client with model override support
- ✅ 1.7.9 Add method: `callGroq(query, modelOverride)`
- ✅ 1.7.10 Add rate limit tracking (30 req/min)
- ✅ 1.7.11 Add error handling & retry logic
- ✅ 1.7.12 Test Groq integration with sample query
- ✅ 1.7.13 Add support for groq/compound (reasoning + browser_search via Groq API)
- ✅ 1.7.14 Add token limit handling (1024 for compound, 2048 for standard)
- ✅ 1.7.15 Create `src/providers/openrouter.js`
- ✅ 1.7.16 Implement OpenRouter API client (fallback only)
- ✅ 1.7.17 Add method: `callOpenRouter(query, enableWebSearch, queryType)`
- ✅ 1.7.18 Add browser_search tool support for OpenRouter GPT-OSS models
- ✅ 1.7.19 Add rate limit tracking
- ✅ 1.7.20 Add error handling & retry logic
- ✅ 1.7.21 Test OpenRouter integration with sample query

## Section 1.8: Response Normalization

- ✅ 1.8.1 Create `src/utils/normalize.js`
- ✅ 1.8.2 Test normalization with sample responses
- ✅ 1.8.3 Handle errors: Missing fields, null responses, empty strings

## Section 1.9: Query Classification Engine

- ✅ 1.9.1 Create `src/classification/classifier.js`
- ✅ 1.9.2 Implement keyword-based classification
- ✅ 1.9.3 Add method: `classifyQuery(query)`
- ✅ 1.9.4 Support categories: "business_news", "financial_analysis", "creative", "general_knowledge"
- ✅ 1.9.5 Use keyword list from config
- ✅ 1.9.6 Test classification with sample queries
- ✅ 1.9.7 Add financial_analysis category with market-related keywords

## Section 1.10: Routing Engine & Model Selection

- ✅ 1.10.1 Create `src/routing/router.js`
- ✅ 1.10.2 Implement routing logic based on query classification
- ✅ 1.10.3 Add method: `selectPrimaryProvider(queryType)`
- ✅ 1.10.4 Define global failover chain (Groq → OpenRouter)
- ✅ 1.10.5 Test routing for each query type
- ✅ 1.10.6 Route news to Groq (groq/compound via Groq API with browser_search)
- ✅ 1.10.7 Route financial_analysis to Groq (groq/compound via Groq API with browser_search)
- ✅ 1.10.8 Route creative to Groq (llama-3.1-8b-instant, standard model)
- ✅ 1.10.9 Route general_knowledge to Gemini (models/gemini-2.0-flash)
- ✅ 1.10.10 Fallback: OpenRouter (GPT-OSS 20B for news, 120B for financial)
- ✅ 1.10.11 Document model selection strategy in 00_project/03_model_routing_strategy.md

## Section 1.11: Failover & Retry Logic

- ✅ 1.11.1 Create `src/failover/failover.js`
- ✅ 1.11.2 Implement failover orchestration
- ✅ 1.11.3 Add method: `executeWithFailover(query, primaryProvider)`
- ✅ 1.11.4 No backend queueing - app handles offline retry
- ✅ 1.11.5 Test failover chain
- ✅ 1.11.6 Handle 429 responses from LLM APIs

## Section 1.12: Rate Limiting

- ✅ 1.12.1 Create `src/rate-limiting/limiter.js`
- ✅ 1.12.2 Implement global rate limiter
- ✅ 1.12.3 Add method: `checkRateLimit(provider)`
- ✅ 1.12.4 Test rate limiting with burst requests
- ✅ 1.12.5 Verify errors returned when rate limited

## Section 1.13: API Endpoints

- ✅ 1.13.1 Create `src/routes/query.js`
- ✅ 1.13.2 Implement POST /api/query endpoint
- ✅ 1.13.3 Implement POST /api/queue/sync endpoint
- ✅ 1.13.4 GET /api/health endpoint already created
- ✅ 1.13.5 Add error handling for all endpoints
- ✅ 1.13.6 Test all endpoints with Postman or curl

## Section 1.14: Backend Database

- ✅ 1.14.1 Note: Backend is stateless in MVP
- ✅ 1.14.2 All request queuing handled by app
- [ ] 1.14.3 If future phases need rate limit persistence or request logging
- ✅ 1.14.4 For MVP: Skip detailed implementation

## Section 1.15: Backend Deployment

- ✅ 1.15.1 Create Render account
- ✅ 1.15.2 Create render.yaml
- ✅ 1.15.3 Create DEPLOYMENT.md
- ✅ 1.15.4 Connect GitHub repository to Render
- ✅ 1.15.5 Set environment variables in Render
- ✅ 1.15.6 Deploy backend to Render
- ✅ 1.15.7 Test production API endpoint
- ✅ 1.15.8 Record Render backend URL

---

# PHASE 2: ANDROID APP DEVELOPMENT

## Section 2.1: Project Setup

- ✅ 2.1.1 Framework: React Native (Expo)
- ✅ 2.1.2 Create askme-app directory structure
- ✅ 2.1.3 Initialize git repository
- ✅ 2.1.4 Create .env.example
- ✅ 2.1.5 Create package.json with dependencies
- ✅ 2.1.6 Create app.json
- ✅ 2.1.7 Create babel.config.js
- ✅ 2.1.8 Create .gitignore
- ✅ 2.1.9 Create README.md

## Section 2.2: Minimalist GUI - Search Interface

- ✅ 2.2.1 Create HomeScreen component
- ✅ 2.2.2 Add TextInput for query
- ✅ 2.2.3 Add Send button with loading state
- ~~2.2.4 Add response display area~~ → Replaced with message bubbles (2.2.14)
- ~~2.2.5 Add loading spinner~~ → Replaced with skeleton animation (2.2.15)
- ✅ 2.2.6 Add error message display
- ~~2.2.7 Add info bar (Model, Category, Response Time)~~ → Moved to message metadata (2.2.14)
- ✅ 2.2.8 Add offline status banner
- ✅ 2.2.9 Add empty state
- ✅ 2.2.10 Style for minimalist look

## Section 2.2.1: UI Enhancements (NEW)

- ✅ 2.2.1.1 Move search bar to bottom of screen (fixed input area)
- ✅ 2.2.1.2 Enable Return/Enter key submission with keyboard dismiss
- ✅ 2.2.1.3 Register app icon in app.json
- ✅ 2.2.1.4 Create conversation-style UI with message bubbles (MessageBubble component)
- ✅ 2.2.1.5 Add loading skeleton animation with shimmer effect (SkeletonLoader component)
- ✅ 2.2.1.6 Add model name formatting with subtitles (Groq/compound, Gemini/2.0-Flash)
- ✅ 2.2.1.7 Create ThemeContext for dark mode management
- ✅ 2.2.1.8 Implement dark mode with light/dark color palettes
- ✅ 2.2.1.9 Add dark mode toggle in Settings screen
- ✅ 2.2.1.10 Persist theme preference to AsyncStorage
- ✅ 2.2.1.11 Update Redux querySlice with message history state (addMessage, updateLastMessage, clearMessages)
- ✅ 2.2.1.12 Add chat_history table to SQLite database
- ✅ 2.2.1.13 Implement chat history persistence (saveMessage, updateMessage, loadChatHistory, clearChatHistory)
- ✅ 2.2.1.14 Auto-load chat history on app start
- ✅ 2.2.1.15 Wrap App with ThemeProvider for theme support
- ✅ 2.2.1.16 Create providerFormatter utility for model name formatting

## Section 2.3: State Management

- ✅ 2.3.1 Create Redux store
- ✅ 2.3.2 Create querySlice reducer with actions
- ✅ 2.3.3 Integrate Redux in App.js
- ✅ 2.3.4 Use Redux hooks in HomeScreen
- ✅ 2.3.5 Manage all state
- ✅ 2.3.6 Handle offline status

## Section 2.4: API Integration

- ✅ 2.4.1 Create APIClient service
- ✅ 2.4.2 Implement response time measurement
- ✅ 2.4.3 Add timeout (10 seconds)
- ✅ 2.4.4 Add detailed error handling
- ✅ 2.4.5 Add retry logic on network error
- ✅ 2.4.6 Test API integration with Render backend
- ✅ 2.4.7 Handle cold start

## Section 2.5: Offline Queueing

- ✅ 2.5.1 Initialize SQLite database
- ✅ 2.5.2 Create tables
- ✅ 2.5.3 Implement offline check
- ✅ 2.5.4 When offline: Store query to SQLite
- ✅ 2.5.5 On network restore: Sync queries
- ✅ 2.5.6 Set up background sync
- ✅ 2.5.7 Queue depth limit

## Section 2.6: Caching

- ✅ 2.6.1 Implement response cache with expiration
- ✅ 2.6.2 Cache expiration cleanup
- ✅ 2.6.3 Check cache before API call
- ✅ 2.6.4 Test cache hit/miss scenarios

## Section 2.8: User Feedback

- ✅ 2.8.1 Show LLM provider label (with subtitles via providerFormatter)
- [ ] 2.8.2 On failover: Show backup notification
- ✅ 2.8.3 Show response time (in message metadata)
- ✅ 2.8.4 Show query category (in message metadata)

## Section 2.9: Settings/Info Screen

- ✅ 2.9.1 Create Settings screen
- ✅ 2.9.2 Display app version
- ✅ 2.9.3 Display cache size
- ✅ 2.9.4 Add "Clear Cache" button
- ✅ 2.9.5 Display privacy statement
- ✅ 2.9.6 Add dark mode toggle (NEW)

## Section 2.10: Performance Optimization

- [ ] 2.10.1 Ensure app launches in <3 seconds
- [ ] 2.10.2 Ensure response displays in <10 seconds
- [ ] 2.10.3 Optimize bundle size
- [ ] 2.10.4 Test on low-end device

---

# PHASE 3: TESTING

## Section 3.5: Backend Testing

- ✅ 3.5.1 Set up Jest for backend testing
- ✅ 3.5.2 Test classification engine
- ✅ 3.5.3 Test routing engine
- ✅ 3.5.4 Test rate limiter
- ✅ 3.5.5 Test response normalization
- ✅ 3.5.6 Test API endpoints with Supertest
- ✅ 3.5.7 Test error handling

## Section 3.1: End-to-End Testing

- [ ] 3.1.1 Test normal flow
- [ ] 3.1.2 Test failover
- [ ] 3.1.3 Test offline
- [ ] 3.1.4 Test cache
- [ ] 3.1.5 Test all 3 query types

## Section 3.2: Stress Testing

- [ ] 3.2.1 Test 10 concurrent queries
- [ ] 3.2.2 Test rate limiting behavior
- [ ] 3.2.3 Test queue with 5 offline queries

## Section 3.3: Security Testing

- [ ] 3.3.1 Verify no API keys in APK
- [ ] 3.3.2 Verify all queries stored locally
- [ ] 3.3.3 Test with network proxy
- [ ] 3.3.4 Verify SQLite encryption

## Section 3.4: Accessibility

- [ ] 3.4.1 Add content descriptions to buttons
- [ ] 3.4.2 Ensure text size is readable
- [ ] 3.4.3 Test with screen reader

---

# PHASE 4: BUILD & RELEASE

## Section 4.1: Build Preparation

- [ ] 4.1.1 Update app version to 1.0.0
- [ ] 4.1.2 Update app name
- [ ] 4.1.3 Create app icon (512x512)
- [ ] 4.1.4 Create app banner/splash screen
- [ ] 4.1.5 Ensure README.md is updated

## Section 4.2: APK Build & Signing

- [ ] 4.2.1 Build release APK with EAS
- [ ] 4.2.2 Download signed APK from EAS Build
- [ ] 4.2.3 Verify APK size
- [ ] 4.2.4 Test APK on physical Android device
- [ ] 4.2.5 Test all features on device
- [ ] 4.2.6 Test cold start

## Section 4.3: Distribution

- [ ] 4.3.1 Create GitHub Release
- [ ] 4.3.2 Upload APK to GitHub Release
- [ ] 4.3.3 Create APK download instructions
- [ ] 4.3.4 Document installation steps
- [ ] 4.3.5 Test downloading and installing APK

## Section 4.4: Documentation

- [ ] 4.4.1 Create USER_GUIDE.md
- [ ] 4.4.2 Create API_DOCS.md
- [ ] 4.4.3 Create DEPLOYMENT.md
- [ ] 4.4.4 Create ARCHITECTURE_OVERVIEW.md

## Section 4.5: Version Control & Tagging

- [ ] 4.5.1 Commit all code
- [ ] 4.5.2 Tag release
- [ ] 4.5.3 Push code and tags

## Section 4.6: Post-Launch Monitoring

- [ ] 4.6.1 Monitor Render backend logs
- [ ] 4.6.2 Monitor app crashes
- [ ] 4.6.3 Collect user feedback
- [ ] 4.6.4 Plan Phase 2 features
