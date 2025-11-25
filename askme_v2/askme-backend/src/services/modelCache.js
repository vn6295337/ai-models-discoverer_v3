/**
 * Model Cache Service
 * Caches best models from intelligent_model_selector /best-model endpoint
 * Refreshes every 30 minutes
 * Provides fallback to hardcoded defaults
 * Provider name mapping: askme (lowercase) -> selector (capitalized)
 */

import config from '../config.js';

const SELECTOR_SERVICE_URL = process.env.MODEL_SELECTOR_URL || 'http://localhost:3001';
const CACHE_REFRESH_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours (matches database update frequency)
const REQUEST_TIMEOUT = 5000; // 5 seconds

/**
 * Provider name mapping from askme config to selector service
 * askme uses lowercase ('groq', 'gemini'), selector uses capitalized ('Groq', 'Google')
 */
const PROVIDER_NAME_MAPPING = {
  [config.providerNames.GROQ]: 'Groq',
  [config.providerNames.GEMINI]: 'Google',
  [config.providerNames.OPENROUTER]: 'OpenRouter',
};

/**
 * Hardcoded fallback models (used when selector service unavailable)
 */
const FALLBACK_MODELS = {
  [config.providerNames.GROQ]: {
    provider: 'Groq',
    modelSlug: 'openai/gpt-oss-20b',
    humanReadableName: 'GPT OSS 20B',
    intelligenceIndex: 52.4,
  },
  [config.providerNames.GEMINI]: {
    provider: 'Google',
    modelSlug: 'gemini-2.5-pro',
    humanReadableName: 'Gemini 2.5 Pro',
    intelligenceIndex: 59.6,
  },
  [config.providerNames.OPENROUTER]: {
    provider: 'OpenRouter',
    modelSlug: null, // TBD when OpenRouter models added
    humanReadableName: 'TBD',
    intelligenceIndex: null,
  },
};

class ModelCache {
  constructor() {
    this.cache = {};
    this.lastRefresh = null;
    this.refreshInterval = null;
    this.isRefreshing = false;
  }

  /**
   * Initialize cache and start refresh interval
   */
  async initialize() {
    console.log('[ModelCache] Initializing...');

    // Initial cache population
    await this.refresh();

    // Set up periodic refresh
    this.refreshInterval = setInterval(() => {
      this.refresh();
    }, CACHE_REFRESH_INTERVAL);

    console.log(`[ModelCache] Initialized. Refresh interval: ${CACHE_REFRESH_INTERVAL / 1000 / 60} min`);
  }

  /**
   * Refresh cache for all providers
   */
  async refresh() {
    if (this.isRefreshing) {
      console.log('[ModelCache] Refresh already in progress, skipping...');
      return;
    }

    this.isRefreshing = true;
    console.log('[ModelCache] Refreshing cache...');

    const providers = [
      config.providerNames.GROQ,
      config.providerNames.GEMINI,
    ];

    const results = await Promise.allSettled(
      providers.map(provider => this.fetchBestModel(provider))
    );

    let successCount = 0;
    let failCount = 0;

    results.forEach((result, index) => {
      const provider = providers[index];

      if (result.status === 'fulfilled' && result.value) {
        this.cache[provider] = result.value;
        successCount++;
        console.log(`[ModelCache] ✓ Cached ${provider}: ${result.value.humanReadableName} (Index: ${result.value.intelligenceIndex})`);
      } else {
        failCount++;
        console.warn(`[ModelCache] ✗ Failed to fetch ${provider}, using fallback`);
        this.cache[provider] = FALLBACK_MODELS[provider];
      }
    });

    this.lastRefresh = new Date();
    this.isRefreshing = false;

    console.log(`[ModelCache] Refresh complete: ${successCount} success, ${failCount} failures`);
  }

  /**
   * Fetch best model for a provider from selector service
   * @param {string} provider - Provider name (askme format: 'groq', 'gemini')
   * @returns {Promise<Object>} Model data
   */
  async fetchBestModel(provider) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

      // Map askme provider name to selector service format
      const selectorProviderName = PROVIDER_NAME_MAPPING[provider] || provider;

      const response = await fetch(
        `${SELECTOR_SERVICE_URL}/best-model?provider=${encodeURIComponent(selectorProviderName)}`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      return {
        provider: data.model.provider,
        modelSlug: data.model.modelSlug,
        humanReadableName: data.model.humanReadableName,
        intelligenceIndex: data.model.intelligenceIndex,
        codingIndex: data.model.codingIndex,
        mathIndex: data.model.mathIndex,
        cached: true,
        fetchedAt: new Date().toISOString(),
      };
    } catch (error) {
      if (error.name === 'AbortError') {
        console.error(`[ModelCache] Timeout fetching ${provider}`);
      } else {
        console.error(`[ModelCache] Error fetching ${provider}:`, error.message);
      }
      return null;
    }
  }

  /**
   * Get best model for a provider
   * @param {string} provider - Provider name
   * @returns {Object} Model data (cached or fallback)
   */
  getModel(provider) {
    const model = this.cache[provider] || FALLBACK_MODELS[provider];

    if (!model) {
      console.warn(`[ModelCache] No model found for provider: ${provider}`);
      return null;
    }

    return {
      ...model,
      isFallback: !this.cache[provider] || model === FALLBACK_MODELS[provider],
      cacheAge: this.lastRefresh
        ? Math.round((Date.now() - this.lastRefresh.getTime()) / 1000)
        : null,
    };
  }

  /**
   * Get cache statistics
   */
  getStats() {
    return {
      providers: Object.keys(this.cache),
      lastRefresh: this.lastRefresh,
      cacheAge: this.lastRefresh
        ? Math.round((Date.now() - this.lastRefresh.getTime()) / 1000) + 's'
        : 'never',
      refreshInterval: `${CACHE_REFRESH_INTERVAL / 1000 / 60}min`,
      models: this.cache,
    };
  }

  /**
   * Stop refresh interval (cleanup)
   */
  stop() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
      console.log('[ModelCache] Stopped');
    }
  }
}

// Singleton instance
const modelCache = new ModelCache();

export default modelCache;
