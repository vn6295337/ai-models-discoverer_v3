import config from '../config.js';
import {
  selectModelWithFallback,
  calculateComplexity,
} from '../utils/modelSelectorClient.js';
import modelCache from '../services/modelCache.js';

/**
 * Routing Engine
 * Selects primary LLM provider based on query classification
 * Now uses intelligent_model_selector service for dynamic selection
 * Fallback chain: Primary → Groq → OpenRouter
 */

/**
 * Select best model from cache (based on Intelligence Index)
 * Uses cached results from intelligent_model_selector /best-model endpoint
 * @param {string} queryType - Query category
 * @returns {Object} Selection with provider, modelName, metadata
 */
export const selectModelFromCache = (queryType) => {
  try {
    // Select provider based on query type
    const provider = selectPrimaryProviderStatic(queryType);

    // Get best model for this provider from cache
    const model = modelCache.getModel(provider);

    if (!model) {
      console.warn('[Router] No cached model for provider:', provider);
      throw new Error(`No cached model available for ${provider}`);
    }

    console.log('[Router] Cache selection:', {
      provider: model.provider,
      model: model.modelSlug,
      humanName: model.humanReadableName,
      intelligenceIndex: model.intelligenceIndex,
      isFallback: model.isFallback,
      cacheAge: model.cacheAge + 's',
    });

    return {
      provider: model.provider,
      modelName: model.modelSlug,
      humanReadableName: model.humanReadableName,
      intelligenceIndex: model.intelligenceIndex,
      codingIndex: model.codingIndex,
      mathIndex: model.mathIndex,
      isFallback: model.isFallback,
      cacheAge: model.cacheAge,
      selectionMethod: 'intelligence_index_cached',
    };
  } catch (error) {
    console.error('[Router] Cache selection error:', error.message);
    // Fall back to static provider selection
    const provider = selectPrimaryProviderStatic(queryType);
    return {
      provider,
      modelName: null,
      isFallback: true,
      error: error.message,
      selectionMethod: 'static_fallback',
    };
  }
};

/**
 * Select provider and model using intelligent model selector
 * @param {string} queryType - Query category
 * @param {string} queryText - Query text
 * @param {Array<string>} modalities - Required modalities (default: ['text'])
 * @returns {Promise<Object>} Selection with provider, modelName, metadata
 */
export const selectModelDynamic = async (queryType, queryText, modalities = ['text']) => {
  try {
    // Calculate complexity score
    const complexityScore = calculateComplexity(queryText, queryType);

    // Call intelligent model selector
    const selection = await selectModelWithFallback({
      queryType,
      queryText,
      modalities,
      complexityScore,
    });

    console.log('[Router] Dynamic selection:', {
      provider: selection.provider,
      model: selection.modelName,
      score: selection.score,
      complexity: complexityScore,
      isFallback: selection.isFallback || false,
    });

    return selection;
  } catch (error) {
    console.error('[Router] Dynamic selection error:', error.message);
    // Fall back to static selection
    return {
      provider: selectPrimaryProviderStatic(queryType),
      modelName: null,
      isFallback: true,
      error: error.message,
    };
  }
};

/**
 * Select primary provider based on query classification (STATIC - fallback only)
 * @param {string} queryType - Query category (business_news, creative, general_knowledge)
 * @returns {string} Provider name
 */
export const selectPrimaryProviderStatic = (queryType) => {
  try {
    switch (queryType) {
      case config.queryCategories.BUSINESS_NEWS:
        // News queries go to Groq compound (reliable, no payment issues)
        return config.providerNames.GROQ;

      case config.queryCategories.FINANCIAL_ANALYSIS:
        // Financial queries go to Groq compound (reliable, no payment issues)
        return config.providerNames.GROQ;

      case config.queryCategories.CREATIVE:
        // Creative queries go to Groq (fast, good at creative)
        return config.providerNames.GROQ;

      case config.queryCategories.GENERAL_KNOWLEDGE:
      default:
        // Default to Gemini for general knowledge
        return config.providerNames.GEMINI;
    }
  } catch (error) {
    console.error('Routing error:', error.message);
    // Fallback to Gemini on error
    return config.providerNames.GEMINI;
  }
};

/**
 * Select primary provider (wrapper for backward compatibility)
 * Uses static selection if MODEL_SELECTOR_ENABLED=false
 * @param {string} queryType - Query category
 * @returns {string} Provider name
 */
export const selectPrimaryProvider = (queryType) => {
  return selectPrimaryProviderStatic(queryType);
};

/**
 * Get failover chain for a provider
 * Returns: [Primary, Secondary, Tertiary]
 * @param {string} primaryProvider - Primary provider name
 * @returns {string[]} Ordered list of providers to try
 */
export const getFailoverChain = (primaryProvider) => {
  // Start with primary provider
  const chain = [primaryProvider];

  // Standard failover chain for all providers
  // Primary → Groq (secondary) → OpenRouter (tertiary)

  // Add secondary and tertiary from config
  const secondary = config.failoverChain[0] || config.providerNames.GROQ;
  const tertiary = config.failoverChain[1] || config.providerNames.OPENROUTER;

  // Don't add duplicates
  if (secondary !== primaryProvider) {
    chain.push(secondary);
  }
  if (tertiary !== primaryProvider && tertiary !== secondary) {
    chain.push(tertiary);
  }

  return chain;
};

/**
 * Test routing logic
 */
export const testRouting = () => {
  console.log('Testing Query Routing:');

  const testCases = [
    {
      type: config.queryCategories.BUSINESS_NEWS,
      expected: config.providerNames.GEMINI,
    },
    {
      type: config.queryCategories.CREATIVE,
      expected: config.providerNames.GROQ,
    },
    {
      type: config.queryCategories.GENERAL_KNOWLEDGE,
      expected: config.providerNames.GROQ,
    },
  ];

  let passed = 0;

  testCases.forEach((testCase) => {
    const primary = selectPrimaryProvider(testCase.type);
    const isCorrect = primary === testCase.expected;

    console.log(
      `${isCorrect ? '✅' : '❌'} ${testCase.type} → ${primary}`
    );

    if (isCorrect) passed++;

    // Also test failover chain
    const chain = getFailoverChain(primary);
    console.log(
      `    Failover chain: ${chain.join(' → ')}`
    );
  });

  console.log(`\nRouting Tests: ${passed}/${testCases.length} passed`);
  return passed === testCases.length;
};

export default {
  selectPrimaryProvider,
  selectModelFromCache,
  selectModelDynamic,
  getFailoverChain,
  testRouting,
};
