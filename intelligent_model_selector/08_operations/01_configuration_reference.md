# Configuration Reference

**Last Updated:** 2025-11-19
**Purpose:** Environment variables and configuration options

---

## Environment Variables

### Required Variables

**SUPABASE_URL**
- Description: Supabase project URL
- Format: `https://your-project.supabase.co`
- Example: `https://abcdefghijklmnop.supabase.co`
- Required: Yes
- Default: None

**SUPABASE_KEY**
- Description: Supabase anon/public API key
- Format: Long JWT string
- Example: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- Required: Yes
- Default: None
- Note: Use anon key, NOT service_role key

---

### Optional Variables

**ARTIFICIAL_ANALYSIS_API_KEY**
- Description: API key for Intelligence Index data
- Format: String
- Required: No
- Default: None
- Fallback: Heuristic scoring if not provided

**PORT**
- Description: HTTP server port
- Format: Integer (1024-65535)
- Required: No
- Default: `3001`
- Example: `3002`

**CACHE_TTL**
- Description: Cache time-to-live in milliseconds
- Format: Integer
- Required: No
- Default: `1800000` (30 minutes)
- Example: `3600000` (1 hour)

**NODE_ENV**
- Description: Node environment
- Format: `development` | `production` | `test`
- Required: No
- Default: `development`

**LOG_LEVEL**
- Description: Logging verbosity
- Format: `error` | `warn` | `info` | `debug`
- Required: No
- Default: `info`
- Development: `debug`
- Production: `warn`

---

## Configuration Files

### constants.js

**File:** `src/config/constants.js`

**Selection Weights:**
```javascript
export const SELECTION_WEIGHTS = {
  intelligenceIndex: 0.35,
  latency: 0.25,
  rateLimitHeadroom: 0.25,
  geography: 0.10,
  license: 0.05
}
```

**Latency Scores:**
```javascript
export const LATENCY_SCORES = {
  groq: 1.0,      // Fastest
  google: 0.8,    // Fast
  openrouter: 0.6 // Moderate
}
```

**Complexity Thresholds:**
```javascript
export const COMPLEXITY_THRESHOLDS = {
  high: 0.7,      // Requires headroom > 0.6
  medium: 0.4     // Requires headroom > 0.3
}
```

**Rate Limit Defaults:**
```javascript
export const RATE_LIMIT_DEFAULTS = {
  groq: {
    limit: 30,
    window: 60000  // 1 minute
  },
  google: {
    limit: 60,
    window: 60000
  },
  openrouter: {
    limit: 200,
    window: 60000
  }
}
```

**Cache TTLs:**
```javascript
export const CACHE_TTLS = {
  models: process.env.CACHE_TTL || 1800000,      // 30 min
  intelligenceIndex: 604800000                    // 7 days
}
```

---

## Runtime Configuration

### Modifying Selection Weights

To adjust scoring factors:

1. Edit `src/config/constants.js`
2. Ensure weights sum to 1.0
3. Restart service
4. Test selection behavior

Example:
```javascript
// Prioritize latency over intelligence
export const SELECTION_WEIGHTS = {
  intelligenceIndex: 0.25,  // Reduced from 0.35
  latency: 0.35,            // Increased from 0.25
  rateLimitHeadroom: 0.25,
  geography: 0.10,
  license: 0.05
}
```

### Adjusting Cache Duration

**Via Environment Variable:**
```bash
CACHE_TTL=3600000 npm start  # 1 hour cache
```

**Via Configuration File:**
```javascript
// src/config/constants.js
export const CACHE_TTLS = {
  models: 3600000,           // 1 hour
  intelligenceIndex: 604800000
}
```

### Modifying Rate Limits

Update `RATE_LIMIT_DEFAULTS` to match actual provider limits:

```javascript
export const RATE_LIMIT_DEFAULTS = {
  groq: {
    limit: 50,     // Updated from 30
    window: 60000
  }
}
```

---

## Deployment Configuration

### Render (Recommended)

**render.yaml:**
```yaml
services:
  - type: web
    name: intelligent-model-selector
    env: node
    buildCommand: npm install
    startCommand: npm start
    envVars:
      - key: NODE_ENV
        value: production
      - key: PORT
        value: 3001
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: ARTIFICIAL_ANALYSIS_API_KEY
        sync: false
```

Set environment variables in Render dashboard.

### Docker

**Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY src ./src

EXPOSE 3001

CMD ["npm", "start"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  selector:
    build: .
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - PORT=3001
```

---

## Monitoring Configuration

### Logging

**Structured Logging Format:**
```javascript
{
  "timestamp": "2025-11-19T12:00:00.000Z",
  "level": "info",
  "message": "Model selected",
  "provider": "groq",
  "modelName": "llama-3.3-70b-versatile",
  "score": 0.89,
  "headroom": 0.85,
  "duration": 45
}
```

**Log Levels:**
- `error`: Critical failures
- `warn`: Degraded mode, fallbacks
- `info`: Selection events, cache refreshes
- `debug`: Detailed scoring, filter steps

### Health Check Configuration

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-19T12:00:00.000Z",
  "uptime": 3600.5,
  "cache": {
    "models": {
      "status": "valid",
      "age": 600
    },
    "intelligenceIndex": {
      "status": "valid",
      "age": 86400
    }
  },
  "rateLimits": {
    "groq": { "headroom": 0.9 },
    "google": { "headroom": 0.7 },
    "openrouter": { "headroom": 0.85 }
  }
}
```

---

## Troubleshooting

### Configuration Issues

**Missing Environment Variables:**
```bash
# Check all required vars are set
env | grep SUPABASE
```

**Invalid Cache TTL:**
```bash
# Must be positive integer
CACHE_TTL=invalid npm start  # Error
CACHE_TTL=1800000 npm start  # OK
```

**Port Conflicts:**
```bash
# Change port if 3001 in use
PORT=3002 npm start
```

### Performance Tuning

**High Cache Miss Rate:**
- Increase CACHE_TTL
- Check refresh logic
- Monitor ai_models_main update frequency

**Slow Selection Times:**
- Verify Supabase query performance
- Check network latency
- Enable caching
- Review log level (debug adds overhead)

**Rate Limit Tracking Inaccurate:**
- Verify RATE_LIMIT_DEFAULTS match provider limits
- Check counter reset logic
- Consider Redis for persistent tracking

---

## Configuration Checklist

Before deployment:
- [ ] SUPABASE_URL configured
- [ ] SUPABASE_KEY configured (anon key)
- [ ] PORT available and accessible
- [ ] CACHE_TTL appropriate for use case
- [ ] NODE_ENV set to production
- [ ] LOG_LEVEL set to warn or error
- [ ] Selection weights reviewed
- [ ] Rate limit defaults verified
- [ ] Health check responding

---

**Document Status:** ✅ Complete
**Document Owner:** Development Team
