/**
 * Intelligent Model Selector Service
 * Express API server for dynamic AI model selection
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';
import { selectModel } from './services/modelSelector.js';
import cacheManager from './services/cacheManager.js';
import rateLimitTracker from './services/rateLimitTracker.js';
import { fetchLatestModels, testConnection } from './utils/supabase.js';
import { CACHE_TTLS } from './config/constants.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;
const startTime = Date.now();

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));

// Health check endpoint
app.get('/health', (req, res) => {
  const uptime = (Date.now() - startTime) / 1000;
  const cacheStats = cacheManager.getStats();
  const rateLimitStats = rateLimitTracker.getStats();

  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime,
    cache: {
      size: cacheStats.size,
      entries: cacheStats.entries.map(e => ({
        key: e.key,
        age: Math.round(e.age / 1000) + 's',
        expired: e.expired
      }))
    },
    rateLimits: rateLimitStats
  });
});

// Get all available models
app.get('/models', async (req, res) => {
  try {
    const models = await cacheManager.getOrFetch(
      'ai_models_main',
      fetchLatestModels,
      CACHE_TTLS.models
    );

    const cacheAge = cacheManager.getAge('ai_models_main');

    res.json({
      models,
      count: models.length,
      cached: cacheAge > 0,
      cacheAge: cacheAge > 0 ? Math.round(cacheAge / 1000) + 's' : null,
      lastUpdate: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching models:', error);
    res.status(500).json({
      error: 'Failed to fetch models',
      message: error.message
    });
  }
});

// Select optimal model
app.post('/select-model', async (req, res) => {
  try {
    const { queryType, queryText, modalities, complexityScore } = req.body;

    // Validation
    if (!queryType) {
      return res.status(400).json({
        error: 'Missing required field: queryType',
        code: 'INVALID_REQUEST'
      });
    }

    if (!queryText) {
      return res.status(400).json({
        error: 'Missing required field: queryText',
        code: 'INVALID_REQUEST'
      });
    }

    if (complexityScore === undefined || complexityScore === null) {
      return res.status(400).json({
        error: 'Missing required field: complexityScore',
        code: 'INVALID_REQUEST'
      });
    }

    if (complexityScore < 0 || complexityScore > 1) {
      return res.status(400).json({
        error: 'complexityScore must be between 0 and 1',
        code: 'INVALID_REQUEST'
      });
    }

    // Default modalities
    const effectiveModalities = modalities || ['text'];

    // Select model
    const startTime = Date.now();
    const selection = await selectModel({
      queryType,
      queryText,
      modalities: effectiveModalities,
      complexityScore
    });

    const duration = Date.now() - startTime;

    // Log selection
    console.log('Model selected:', {
      provider: selection.provider,
      modelName: selection.modelName,
      score: selection.score,
      headroom: selection.rateLimitHeadroom,
      duration: duration + 'ms'
    });

    res.json({
      ...selection,
      selectionDuration: duration
    });
  } catch (error) {
    console.error('Model selection error:', error);

    if (error.message.includes('No models')) {
      return res.status(500).json({
        error: error.message,
        code: 'NO_MODELS_AVAILABLE',
        details: {
          queryType: req.body.queryType,
          modalities: req.body.modalities
        }
      });
    }

    res.status(500).json({
      error: 'Model selection failed',
      message: error.message,
      code: 'SELECTION_ERROR'
    });
  }
});

// Manually refresh cache
app.post('/cache/refresh', async (req, res) => {
  try {
    cacheManager.invalidate('ai_models_main');
    const models = await fetchLatestModels();
    cacheManager.set('ai_models_main', models, CACHE_TTLS.models);

    res.json({
      message: 'Cache refreshed',
      timestamp: new Date().toISOString(),
      modelCount: models.length
    });
  } catch (error) {
    console.error('Cache refresh error:', error);
    res.status(500).json({
      error: 'Cache refresh failed',
      message: error.message
    });
  }
});

// Reset rate limit counters (for testing)
app.post('/rate-limits/reset', (req, res) => {
  rateLimitTracker.resetAll();

  res.json({
    message: 'Rate limit counters reset',
    timestamp: new Date().toISOString()
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);

  res.status(500).json({
    error: 'Internal server error',
    message: err.message,
    code: 'INTERNAL_ERROR'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    code: 'NOT_FOUND',
    path: req.path
  });
});

// Start server
async function startServer() {
  try {
    // Test Supabase connection
    console.log('Testing Supabase connection...');
    const connected = await testConnection();

    if (!connected) {
      console.error('Failed to connect to Supabase. Check your credentials.');
      process.exit(1);
    }

    console.log('✓ Supabase connection successful');

    // Pre-warm cache
    console.log('Pre-warming cache...');
    const models = await fetchLatestModels();
    cacheManager.set('ai_models_main', models, CACHE_TTLS.models);
    console.log(`✓ Cached ${models.length} models`);

    // Start listening
    app.listen(PORT, () => {
      console.log(`\n🚀 Intelligent Model Selector running on port ${PORT}`);
      console.log(`   Health check: http://localhost:${PORT}/health`);
      console.log(`   Environment: ${process.env.NODE_ENV || 'development'}\n`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

export default app;
