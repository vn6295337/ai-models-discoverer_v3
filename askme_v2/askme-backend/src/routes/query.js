import express from 'express';
import { validateQuery, validateBatchQueries } from '../middleware/validate.js';
import { classifyQuery } from '../classification/classifier.js';
import { selectPrimaryProvider, selectModelDynamic } from '../routing/router.js';
import { executeWithFailover } from '../failover/failover.js';
import { checkRateLimit } from '../rate-limiting/limiter.js';
import { normalizeResponse } from '../utils/normalize.js';

const router = express.Router();

/**
 * POST /api/query
 * Process a single query
 * Request: { query: string }
 * Response: { response: string, llm_used: string, category: string, response_time: number }
 */
router.post('/query', validateQuery, async (req, res) => {
  const startTime = Date.now();

  try {
    const query = req.validatedQuery;

    // Step 1: Classify query
    const classification = classifyQuery(query);
    console.log(`[Query] Classified as: ${classification.type}`);

    // Step 2: Select optimal model using intelligent selector
    let selection = null;
    try {
      selection = await selectModelDynamic(classification.type, query, ['text']);
      console.log(`[Query] Dynamic selection: ${selection.provider} - ${selection.modelName}`);
    } catch (error) {
      console.warn(`[Query] Dynamic selection failed, using static fallback:`, error.message);
      // Fallback to static selection
      const primaryProvider = selectPrimaryProvider(classification.type);
      selection = { provider: primaryProvider, modelName: null, isFallback: true };
    }

    // Step 3: Check rate limit
    const rateLimitCheck = checkRateLimit(selection.provider);
    if (!rateLimitCheck.allowed) {
      console.warn(`[Query] Rate limit exceeded: ${selection.provider}`);
      return res.status(429).json({
        error: rateLimitCheck.error,
        status: 429,
        retryAfter: rateLimitCheck.retryAfter,
      });
    }

    // Step 4: Execute with failover
    const result = await executeWithFailover(
      query,
      selection.provider,
      classification.type,
      selection.modelName
    );

    if (!result.success) {
      console.error(`[Query] All providers failed:`, result.error);
      return res.status(500).json({
        error: result.error,
        status: 500,
      });
    }

    // Step 5: Return response
    const responseTime = Date.now() - startTime;

    res.json({
      response: result.response,
      llm_used: result.llm_used,
      category: classification.type,
      response_time: responseTime,
      confidence: classification.confidence,
    });
  } catch (error) {
    console.error('[Query] Unexpected error:', error);
    const responseTime = Date.now() - startTime;

    res.status(500).json({
      error: error.message || 'Internal server error',
      status: 500,
      response_time: responseTime,
    });
  }
});

/**
 * POST /api/queue/sync
 * Sync offline queries when app comes online
 * Request: { queries: [{ id: number, query: string, timestamp: number }] }
 * Response: { responses: [{id: number, response: string, llm_used: string, response_time: number, ...}] }
 */
router.post('/queue/sync', validateBatchQueries, async (req, res) => {
  const startTime = Date.now();

  try {
    const queries = req.validatedQueries;
    const responses = [];

    console.log(`[Sync] Processing ${queries.length} offline queries`);

    for (const queryItem of queries) {
      const itemStartTime = Date.now();
      try {
        const { id, query } = queryItem;

        // Classify and route
        const classification = classifyQuery(query);

        // Select optimal model using intelligent selector
        let selection = null;
        try {
          selection = await selectModelDynamic(classification.type, query, ['text']);
        } catch (error) {
          console.warn(`[Sync] Dynamic selection failed, using static fallback:`, error.message);
          const primaryProvider = selectPrimaryProvider(classification.type);
          selection = { provider: primaryProvider, modelName: null, isFallback: true };
        }

        // Check rate limit before executing
        const rateLimitCheck = checkRateLimit(selection.provider);
        if (!rateLimitCheck.allowed) {
          console.warn(`[Sync] Rate limit for ${selection.provider}, skipping queue ID ${id}`);
          responses.push({
            id: id,
            query: query,
            success: false,
            error: `Rate limit exceeded for ${selection.provider}`,
            llm_used: null,
            response_time: Date.now() - itemStartTime,
          });
          continue;
        }

        // Execute with failover
        const result = await executeWithFailover(
          query,
          selection.provider,
          classification.type,
          selection.modelName
        );
        const itemResponseTime = Date.now() - itemStartTime;

        if (result.success) {
          responses.push({
            id: id,
            query: query,
            response: result.response,
            llm_used: result.llm_used,
            category: classification.type,
            response_time: itemResponseTime,
            success: true,
          });
        } else {
          responses.push({
            id: id,
            query: query,
            success: false,
            error: result.error,
            llm_used: null,
            response_time: itemResponseTime,
          });
        }
      } catch (error) {
        console.error(`[Sync] Error processing queue ID ${queryItem.id}:`, error.message);
        responses.push({
          id: queryItem.id,
          query: queryItem.query,
          success: false,
          error: error.message || 'Unknown error',
          llm_used: null,
          response_time: Date.now() - itemStartTime,
        });
      }
    }

    const responseTime = Date.now() - startTime;

    res.json({
      responses: responses,
      synced: responses.filter((r) => r.success).length,
      failed: responses.filter((r) => !r.success).length,
      response_time: responseTime,
    });
  } catch (error) {
    console.error('[Sync] Unexpected error:', error);
    const responseTime = Date.now() - startTime;

    res.status(400).json({
      error: error.message || 'Invalid sync request',
      status: 400,
      response_time: responseTime,
    });
  }
});

export default router;
