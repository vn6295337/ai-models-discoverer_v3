# Testing Strategy

**Last Updated:** 2025-11-19
**Purpose:** Testing approach and guidelines

---

## Coverage Requirements

**Minimum Coverage: 80%**
- Branch coverage: 80%
- Function coverage: 80%
- Line coverage: 80%
- Statement coverage: 80%

---

## Testing Pyramid

```
        ┌─────────────┐
        │   E2E/API   │  ~10% (Integration)
        │   Tests     │
        └─────────────┘
       ┌───────────────┐
       │  Integration  │   ~30% (Component Integration)
       │    Tests      │
       └───────────────┘
      ┌─────────────────┐
      │   Unit Tests    │    ~60% (Individual Functions)
      └─────────────────┘
```

---

## Unit Testing

### Scope

Test individual functions and modules in isolation with mocked dependencies.

### Files to Test

**src/services/modelSelector.js:**
```javascript
describe('modelSelector', () => {
  describe('filterByModalities', () => {
    it('should filter models by required input modalities', () => {})
    it('should handle missing modality fields gracefully', () => {})
  })

  describe('calculateScores', () => {
    it('should calculate scores with all factors', () => {})
    it('should handle missing Intelligence Index gracefully', () => {})
    it('should apply correct weights', () => {})
  })

  describe('matchComplexityToHeadroom', () => {
    it('should filter high complexity queries to high headroom', () => {})
    it('should allow low complexity queries any headroom', () => {})
  })

  describe('selectBestModel', () => {
    it('should return top-scored model', () => {})
    it('should return null if no models available', () => {})
  })
})
```

**src/services/cacheManager.js:**
```javascript
describe('cacheManager', () => {
  it('should store and retrieve data', () => {})
  it('should expire data after TTL', () => {})
  it('should trigger background refresh on expiration', () => {})
  it('should invalidate cache manually', () => {})
})
```

**src/services/intelligenceIndex.js:**
```javascript
describe('intelligenceIndex', () => {
  it('should fetch scores from API', async () => {})
  it('should cache scores with 7-day TTL', async () => {})
  it('should provide fallback scores when API unavailable', () => {})
  it('should calculate fallback from model size', () => {})
})
```

**src/services/rateLimitTracker.js:**
```javascript
describe('rateLimitTracker', () => {
  it('should increment usage counter', () => {})
  it('should calculate headroom correctly', () => {})
  it('should reset counters after window expires', () => {})
  it('should return all provider headroom', () => {})
})
```

**src/utils/supabase.js:**
```javascript
describe('supabase', () => {
  it('should fetch models from ai_models_main', async () => {})
  it('should filter by provider', async () => {})
  it('should handle database errors gracefully', async () => {})
})
```

---

## Integration Testing

### Scope

Test component interactions and end-to-end flows with mocked external dependencies (Supabase, Artificial Analysis API).

### Test Scenarios

**Selection Flow:**
```javascript
describe('Model Selection Flow', () => {
  it('should select model from cached data', async () => {
    // Mock cache with sample models
    // Call selectModel()
    // Verify correct model selected
  })

  it('should fetch from DB when cache expired', async () => {
    // Mock expired cache
    // Mock Supabase query
    // Call selectModel()
    // Verify DB query executed
  })

  it('should apply complexity-headroom matching', async () => {
    // Mock high complexity query
    // Mock low headroom provider
    // Verify provider filtered out
  })
})
```

**Cache Behavior:**
```javascript
describe('Cache Refresh', () => {
  it('should return stale data on expiration', async () => {})
  it('should trigger background refresh', async () => {})
  it('should handle refresh failures gracefully', async () => {})
})
```

**Rate Limit Tracking:**
```javascript
describe('Rate Limit Integration', () => {
  it('should track usage across multiple selections', async () => {})
  it('should prevent selection when headroom too low', async () => {})
  it('should reset counters after window', async () => {})
})
```

---

## API Testing

### Scope

Test HTTP endpoints with supertest.

### Test Cases

**POST /select-model:**
```javascript
describe('POST /select-model', () => {
  it('should return 200 with valid request', async () => {
    const response = await request(app)
      .post('/select-model')
      .send({
        queryType: 'general_knowledge',
        queryText: 'Test query',
        modalities: ['text'],
        complexityScore: 0.5
      })

    expect(response.status).toBe(200)
    expect(response.body).toHaveProperty('provider')
    expect(response.body).toHaveProperty('modelName')
  })

  it('should return 400 with missing fields', async () => {
    const response = await request(app)
      .post('/select-model')
      .send({ queryType: 'general' })

    expect(response.status).toBe(400)
  })

  it('should return 500 when no models available', async () => {
    // Mock empty model list
    const response = await request(app)
      .post('/select-model')
      .send(validRequest)

    expect(response.status).toBe(500)
    expect(response.body.code).toBe('NO_MODELS_AVAILABLE')
  })
})
```

**GET /health:**
```javascript
describe('GET /health', () => {
  it('should return 200 with health status', async () => {
    const response = await request(app).get('/health')

    expect(response.status).toBe(200)
    expect(response.body.status).toBe('ok')
  })
})
```

**POST /cache/refresh:**
```javascript
describe('POST /cache/refresh', () => {
  it('should invalidate and refresh cache', async () => {
    const response = await request(app).post('/cache/refresh')

    expect(response.status).toBe(200)
    expect(response.body.message).toBe('Cache refreshed')
  })
})
```

---

## Mocking Strategy

### External Dependencies

**Supabase:**
```javascript
jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(() => ({
    from: jest.fn(() => ({
      select: jest.fn(() => ({
        eq: jest.fn(() => ({
          data: mockModels,
          error: null
        }))
      }))
    }))
  }))
}))
```

**Artificial Analysis API:**
```javascript
jest.mock('node-fetch', () => jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve(mockIntelligenceScores)
  })
))
```

### Time-Dependent Tests

```javascript
jest.useFakeTimers()

it('should expire cache after TTL', () => {
  const cache = new CacheManager()
  cache.set('key', 'value', 1000)

  jest.advanceTimersByTime(1001)

  expect(cache.isExpired('key')).toBe(true)
})
```

---

## Test Data

### Sample Models

```javascript
const mockModels = [
  {
    inference_provider: 'groq',
    model_provider: 'Meta',
    human_readable_name: 'Llama 3.3 70B Versatile',
    input_modalities: 'Text',
    output_modalities: 'Text',
    license_name: 'Llama-3.3',
    model_provider_country: 'United States',
    rate_limits: '30 requests per minute'
  },
  {
    inference_provider: 'google',
    model_provider: 'Google',
    human_readable_name: 'Gemini 2.0 Flash',
    input_modalities: 'Text, Image',
    output_modalities: 'Text',
    license_name: 'Gemini',
    rate_limits: '60 requests per minute'
  }
]
```

### Sample Intelligence Scores

```javascript
const mockIntelligenceScores = {
  'llama-3.3-70b-versatile': 0.89,
  'gemini-2.0-flash': 0.78
}
```

---

## Running Tests

### All Tests

```bash
npm test
```

### Watch Mode

```bash
npm run test:watch
```

### Coverage Report

```bash
npm test -- --coverage
```

Coverage report generated in `coverage/` directory.

### Specific Test File

```bash
npm test -- modelSelector.test.js
```

---

## Continuous Integration

### GitHub Actions (Future)

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: npm test
      - run: npm run lint
```

---

## Test Checklist

Before marking a feature complete:
- [ ] Unit tests written (80%+ coverage)
- [ ] Integration tests for critical paths
- [ ] API endpoint tests
- [ ] Error handling tested
- [ ] Edge cases covered
- [ ] Mocks properly isolated
- [ ] Tests pass consistently
- [ ] Coverage report reviewed

---

**Document Status:** ✅ Complete
**Document Owner:** Development Team
