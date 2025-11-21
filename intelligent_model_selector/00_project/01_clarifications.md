# Intelligent Model Selector - Clarifications & Decisions

**Document Type:** Clarifications & Q&A
**Last Updated:** 2025-11-19
**Purpose:** Record key decisions and clarifications during development

---

## Selection Criteria

**Q: Should we filter models by open-source licenses only?**

**A:** No. License filtering should be configurable, not mandatory. The selection algorithm should:
- Accept license preference as optional parameter
- Include license score as minor weight (5%) in overall scoring
- Allow all licenses by default
- Enable client to specify license requirements if needed

**Rationale:** Flexibility for different use cases. askme_v2 prefers open-source but shouldn't exclude proprietary models entirely.

---

**Q: How do we handle models with no Intelligence Index scores?**

**A:** Graceful degradation:
1. Use fallback scoring based on:
   - Model size (inferred from name: 70b > 27b > 8b)
   - Provider latency baseline
   - Rate limit headroom
2. Log missing Intelligence Index entries
3. Don't exclude models without scores
4. Weight other factors more heavily (redistribute 35% weight)

**Rationale:** External API may be unavailable or not cover all models. Service must remain functional.

---

**Q: What modality filters should we apply?**

**A:** Dynamic, query-based filtering:
- Do NOT filter by "text output capable" (almost all models support this)
- Do NOT hardcode "open-source only" filter
- DO filter by required input modalities based on query needs:
  - Text-only queries: any model
  - Image queries: filter for image input support
  - Audio queries: filter for audio input support
- Output modality filtering only for specific needs (e.g., embedding models)

**Rationale:** User feedback indicated most models support text output. Only filter when truly necessary.

---

## Rate Limit Handling

**Q: Should we avoid rate-limited providers?**

**A:** No. All providers are rate-limited. Instead:
- Track usage intelligently
- Distribute load strategically based on:
  - Query complexity
  - Available headroom
  - Provider capabilities
- Simple queries → providers with less headroom
- Complex queries → providers with most headroom

**Rationale:** "Avoidance" is impossible. Smart distribution optimizes total capacity.

---

**Q: How accurate does rate limit tracking need to be?**

**A:** Approximate tracking is acceptable for MVP:
- In-memory counters (reset on restart)
- Simple increment/decrement
- Window-based reset (every 60 seconds)
- Trade-off: Simplicity vs perfect accuracy

**Future:** Redis for persistent tracking in production if needed.

**Rationale:** Perfect tracking is overkill. Approximate is sufficient for intelligent distribution.

---

## Performance Metrics

**Q: Where do we get model performance scores?**

**A:** Artificial Analysis Intelligence Index API:
- Primary source for performance data
- Industry-standard benchmarks
- Updated regularly
- API integration in Phase 2

**Rationale:** User specifically requested Intelligence Index. Don't build proprietary benchmarks.

---

**Q: What if Intelligence Index API is down?**

**A:** Fallback scoring:
1. Use cached Intelligence Index data (7-day TTL)
2. If no cache, use heuristic scoring:
   - Model size from name (70b = 0.9, 27b = 0.7, 8b = 0.5)
   - Provider reputation baseline
   - Latency scores
3. Log degraded mode
4. Continue serving requests

**Rationale:** External dependency shouldn't break service. Degrade gracefully.

---

## Caching Strategy

**Q: How fresh does model data need to be?**

**A:** 30-minute cache TTL:
- ai_models_main updates daily (via GitHub Actions)
- 30-minute staleness acceptable vs performance benefit
- Background refresh minimizes cache miss latency
- Force refresh endpoint for manual updates

**Rationale:** Balance freshness vs performance. Daily updates don't require real-time sync.

---

**Q: Should cache be in-memory or external (Redis)?**

**A:** In-memory for MVP, Redis option for production:
- **MVP:** Node.js in-memory (simple, fast)
- **Production:** Redis if needed for:
  - Multi-instance deployment
  - Persistent rate limit tracking
  - Shared cache across services

**Rationale:** Start simple. Add complexity only when needed.

---

## Integration

**Q: Should this be a microservice or integrated into askme_v2?**

**A:** Microservice (separate service):
- Clean separation of concerns
- Independent deployment
- Reusable by other projects
- Easier testing in isolation
- Network latency acceptable for <100ms target

**Rationale:** Modularity > slight latency increase. Well-designed API keeps integration simple.

---

**Q: What's the integration path for askme_v2?**

**A:** Minimal changes to existing code:
1. Add selector client utility
2. Replace hardcoded models in router.js
3. Pass dynamic model names to providers
4. Keep fallback to constants.js if selector unavailable

**Integration points:**
- `askme-backend/src/routing/router.js` - Primary selection
- `askme-backend/src/failover/failover.js` - Use returned model names
- `askme-backend/src/utils/modelSelectorClient.js` - New client (HTTP calls)

**Rationale:** Minimize risk. Keep existing architecture largely intact.

---

## Complexity Scoring

**Q: How do we determine query complexity?**

**A:** Client (askme_v2) calculates complexity score:
- Query length (longer = more complex)
- Keyword detection (technical terms, analysis requests)
- Query classification category
- Returns score 0.0-1.0

**Selector service:**
- Accepts complexityScore as input
- Uses for headroom matching
- Doesn't calculate complexity itself

**Rationale:** Domain knowledge in askme_v2. Selector focuses on selection logic only.

---

## Geographic Filtering

**Q: What geographic filtering do we need?**

**A:** Configurable, optional filtering:
- Query ai_models_main.model_provider_country
- Accept geographic preferences from client
- Default: No geographic filtering
- Enable when needed (compliance, preference)

**Example use cases:**
- Exclude specific countries
- Prefer specific regions
- Compliance requirements

**Rationale:** Flexibility for future needs. Not critical for MVP but easy to support.

---

## Error Handling

**Q: What happens if no models match criteria?**

**A:** Graceful degradation chain:
1. Relax modality requirements (if possible)
2. Relax license requirements (if specified)
3. Relax geographic requirements (if specified)
4. Return error if still no matches
5. Client (askme_v2) falls back to hardcoded defaults

**Error response:**
```json
{
  "error": "No models match criteria",
  "code": "NO_MODELS_AVAILABLE",
  "details": {
    "requestedModalities": ["text", "image"],
    "appliedFilters": ["open-source", "US-only"],
    "relaxedCriteria": ["license", "geography"],
    "availableModels": 0
  }
}
```

**Rationale:** Never leave client without response. Fail gracefully with context.

---

## Testing Strategy

**Q: What test coverage is required?**

**A:** 80% minimum across all metrics:
- Branch coverage: 80%
- Function coverage: 80%
- Line coverage: 80%
- Statement coverage: 80%

**Test types:**
- Unit tests: All services, utils
- Integration tests: End-to-end selection flow
- Supabase query tests (mocked)
- Cache behavior tests
- Error handling tests

**Rationale:** High confidence in core selection logic. Not 100% to avoid diminishing returns.

---

## Deployment

**Q: Where will this service run?**

**A:** Initially same infrastructure as askme_v2:
- Render free tier (or similar)
- Environment variables for configuration
- Single instance for MVP
- Scale horizontally if needed (Redis for shared state)

**Rationale:** Minimize operational complexity. Proven deployment model from askme_v2.

---

## Documentation

**Q: What documentation is required?**

**A:** Following askme_v2 conventions:
- Root README (project overview, quick start)
- INDEX.md (navigation hub)
- CLAUDE.md (AI assistant guide)
- Numbered topic folders (00-08)
- Serial numbered docs within folders
- Atomic task checklist

**Rationale:** Consistency with existing projects. Proven structure.

---

## Future Considerations

**Q: What features are explicitly deferred?**

**A:** Post-MVP (V2 or later):
- User-specific model preferences
- Real-time performance monitoring
- Adaptive scoring weight adjustments
- Multi-region deployment
- Admin UI for configuration
- GraphQL API
- Cost optimization (all models currently free)

**Rationale:** Focus MVP on core value. Add complexity incrementally.

---

## Decision Log

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| 2025-11-19 | No mandatory license filtering | Flexibility for different use cases | Selection algorithm accepts optional license preference |
| 2025-11-19 | Intelligence Index from Artificial Analysis | User requested, industry standard | Phase 2 dependency on external API |
| 2025-11-19 | 30-minute cache TTL | Balance freshness vs performance | Acceptable staleness given daily updates |
| 2025-11-19 | Microservice architecture | Clean separation, reusability | Network latency acceptable for target |
| 2025-11-19 | In-memory cache for MVP | Simplicity over complexity | Redis option for production if needed |
| 2025-11-19 | 80% test coverage target | High confidence without diminishing returns | Comprehensive test suite required |

---

**Document Status:** ✅ Active
**Next Review:** As questions arise during development
**Document Owner:** Development Team
