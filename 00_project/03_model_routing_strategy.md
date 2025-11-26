# AskMe Model Selection & Routing Strategy

**Document:** Model strategy and provider routing decisions
**Last Updated:** 2025-11-17
**Status:** Active (Production)

---

## Query Classification → Provider → Model Map

All queries fall into exactly ONE category. Each category routes to ONE primary provider.

| Query Type | Trigger Keywords | Primary Provider | Model | Rationale | Fallback |
|---|---|---|---|---|---|
| **Business News** | news, latest, today, current, breaking, headline, trending | Groq | `groq/compound` | Real-time reasoning + low latency | OpenRouter (GPT-OSS 20B) |
| **Financial Analysis** | stock, investment, portfolio, financial, market, trading, crypto, bitcoin, ethereum, forex, bonds, etf, dividend, roi, profit, loss, revenue, earnings | Groq | `groq/compound` | Complex reasoning for calculations + market analysis | OpenRouter (GPT-OSS 120B) |
| **Creative** | poem, story, creative, compose, create, author, fiction, narrative | Groq | `llama-3.1-8b-instant` | Fast, good at creative writing | Gemini (2.0-Flash) |
| **General Knowledge** | (all other queries) | Gemini | `models/gemini-2.0-flash` | Best general reasoning + reliable | Groq (llama) |

---

## Key Design Decisions

### Why Groq Compound for News & Financial?
- ✅ Free tier, no payment required
- ✅ Multi-step reasoning capability
- ✅ Fast inference (sub-2s response)
- ❌ No built-in web search (limitation accepted)

### Why Gemini 2.0-Flash for General Knowledge?
- ✅ Best general-purpose reasoning
- ✅ Reliable free tier
- ✅ Better context understanding than competitors

### Why OpenRouter as Fallback Only?
- ⚠️ Requires payment (402 errors on free tier)
- ✅ GPT-OSS models support browser_search
- ✅ Used only when primary providers fail

---

## Failover Chain

**Global Failover Strategy:**
```
Primary Provider
    ↓ (if fails)
Secondary Provider (by category)
    ↓ (if fails)
Tertiary Provider
    ↓ (if all fail)
Return Error to Client
```

### Specific Chains
- **News/Financial:** Groq → OpenRouter (GPT-OSS with browser_search) → Error
- **Creative:** Groq → Gemini → Error
- **General:** Gemini → Groq → Error

---

## Rate Limits (Requests/Minute)

| Provider | Limit | Status |
|---|---|---|
| Groq | 30 RPM | ✅ Active |
| Gemini | 60 RPM | ✅ Active |
| OpenRouter | 100 RPM | ⚠️ Payment Required |

---

## Implementation Notes

### Token Limits
- **Standard models:** 2048 max_tokens
- **Groq compound:** 1024 max_tokens (stricter request limit)

### Tools Enabled
- **OpenRouter GPT-OSS models:** `browser_search` tool (web access)
- **Groq models:** None (knowledge-based only)

### Environment Variables Required
```
GEMINI_API_KEY        # For general knowledge queries
GROQ_API_KEY          # For news, financial, creative queries
OPENROUTER_API_KEY_2  # Fallback only (GPT-OSS models)
```

---

## Future Optimization

1. **Web Search for News:** Implement custom web crawler to inject context into Groq compound
2. **Cost Optimization:** Monitor OpenRouter spend; consider premium tier if volume increases
3. **Latency:** Profile response times; consider caching frequent queries

---
