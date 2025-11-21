/**
 * Model Selector Client
 * HTTP client for intelligent_model_selector service
 */

import config from '../config.js';

const SELECTOR_SERVICE_URL = process.env.MODEL_SELECTOR_URL || 'http://localhost:3001';
const REQUEST_TIMEOUT = 5000; // 5 seconds

/**
 * Select optimal model from intelligent_model_selector service
 * @param {Object} criteria - Selection criteria
 * @param {string} criteria.queryType - Query category
 * @param {string} criteria.queryText - Query text
 * @param {Array<string>} criteria.modalities - Required modalities (default: ['text'])
 * @param {number} criteria.complexityScore - Query complexity (0-1)
 * @returns {Promise<Object>} Selected model with metadata
 */
export async function selectModel(criteria) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    const response = await fetch(`${SELECTOR_SERVICE_URL}/select-model`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(criteria),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(`Selector service error: ${response.status} - ${error.message || error.error || 'Unknown error'}`);
    }

    const selection = await response.json();

    console.log('[ModelSelector] Selected model:', {
      provider: selection.provider,
      modelName: selection.modelName,
      score: selection.score,
      headroom: selection.rateLimitHeadroom,
      duration: selection.selectionDuration,
    });

    return selection;
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error('[ModelSelector] Request timeout after', REQUEST_TIMEOUT, 'ms');
      throw new Error('Model selection timeout');
    }

    console.error('[ModelSelector] Selection failed:', error.message);
    throw error;
  }
}

/**
 * Calculate query complexity score based on various factors
 * @param {string} query - Query text
 * @param {string} queryType - Query category
 * @returns {number} Complexity score (0-1)
 */
export function calculateComplexity(query, queryType) {
  let score = 0.3; // Base score

  // Factor 1: Query length (longer queries are more complex)
  const wordCount = query.trim().split(/\s+/).length;
  if (wordCount > 100) {
    score += 0.3;
  } else if (wordCount > 50) {
    score += 0.2;
  } else if (wordCount > 20) {
    score += 0.1;
  }

  // Factor 2: Query type complexity
  const complexQueryTypes = {
    financial_analysis: 0.3,
    business_news: 0.2,
    creative: 0.1,
    general_knowledge: 0,
  };
  score += complexQueryTypes[queryType] || 0;

  // Factor 3: Technical keywords (analysis, research, detailed, comprehensive, etc.)
  const technicalKeywords = [
    'analyze', 'analysis', 'research', 'detailed', 'comprehensive',
    'evaluate', 'assessment', 'investigate', 'examine', 'breakdown',
    'comparison', 'contrast', 'implications', 'forecast', 'predict',
  ];

  const lowerQuery = query.toLowerCase();
  const keywordCount = technicalKeywords.filter(keyword =>
    lowerQuery.includes(keyword)
  ).length;

  score += Math.min(keywordCount * 0.05, 0.2);

  // Factor 4: Multiple questions or tasks
  const questionMarks = (query.match(/\?/g) || []).length;
  if (questionMarks > 2) {
    score += 0.1;
  } else if (questionMarks > 1) {
    score += 0.05;
  }

  // Ensure score is between 0 and 1
  return Math.min(Math.max(score, 0), 1);
}

/**
 * Get fallback model selection (used when selector service is unavailable)
 * @param {string} queryType - Query category
 * @returns {Object} Fallback selection
 */
export function getFallbackSelection(queryType) {
  const fallbackMap = {
    business_news: {
      provider: config.providerNames.GROQ,
      modelName: 'groq/compound',
    },
    financial_analysis: {
      provider: config.providerNames.GROQ,
      modelName: 'llama-3.3-70b-versatile',
    },
    creative: {
      provider: config.providerNames.OPENROUTER,
      modelName: 'kwaipilot/kat-coder-pro:free',
    },
    general_knowledge: {
      provider: config.providerNames.GEMINI,
      modelName: 'models/gemini-2.0-flash',
    },
  };

  const fallback = fallbackMap[queryType] || fallbackMap.general_knowledge;

  console.log('[ModelSelector] Using fallback:', fallback);

  return {
    provider: fallback.provider,
    modelName: fallback.modelName,
    score: null,
    rateLimitHeadroom: null,
    estimatedLatency: 'unknown',
    intelligenceIndex: null,
    selectionReason: 'Fallback selection (selector service unavailable)',
    isFallback: true,
  };
}

/**
 * Select model with automatic fallback
 * @param {Object} criteria - Selection criteria
 * @returns {Promise<Object>} Selected model
 */
export async function selectModelWithFallback(criteria) {
  try {
    return await selectModel(criteria);
  } catch (error) {
    console.warn('[ModelSelector] Falling back to static selection due to error:', error.message);
    return getFallbackSelection(criteria.queryType);
  }
}

export default {
  selectModel,
  selectModelWithFallback,
  calculateComplexity,
  getFallbackSelection,
};
