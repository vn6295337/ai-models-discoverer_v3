/**
 * Model Selector - Core selection logic
 */

import cacheManager from './cacheManager.js';
import rateLimitTracker from './rateLimitTracker.js';
import { fetchLatestModels } from '../utils/supabase.js';
import {
  SELECTION_WEIGHTS,
  LATENCY_SCORES,
  COMPLEXITY_THRESHOLDS,
  CACHE_TTLS,
  MODEL_SIZE_SCORES,
  QUERY_TYPE_PREFERENCES,
  OPEN_SOURCE_LICENSES,
  GEOGRAPHY_SCORES,
  LICENSE_SCORES
} from '../config/constants.js';

/**
 * Select optimal model based on query characteristics
 * @param {Object} criteria - Selection criteria
 * @param {string} criteria.queryType - Query category
 * @param {string} criteria.queryText - Query text
 * @param {Array<string>} criteria.modalities - Required modalities
 * @param {number} criteria.complexityScore - Query complexity (0-1)
 * @returns {Promise<Object>} Selected model with metadata
 */
export async function selectModel(criteria) {
  const { queryType, queryText, modalities, complexityScore } = criteria;

  // 1. Fetch models from cache/DB
  const models = await getModels();

  if (!models || models.length === 0) {
    throw new Error('No models available');
  }

  // 2. Filter by modalities
  const filteredModels = filterByModalities(models, modalities);

  if (filteredModels.length === 0) {
    throw new Error('No models match required modalities');
  }

  // 3. Get current headroom data
  const headroomData = rateLimitTracker.getAllHeadroom();

  // 4. Calculate scores for each model
  const scoredModels = calculateScores(
    filteredModels,
    queryType,
    complexityScore,
    headroomData
  );

  // 5. Apply complexity-headroom matching
  const matchedModels = matchComplexityToHeadroom(
    scoredModels,
    complexityScore,
    headroomData
  );

  if (matchedModels.length === 0) {
    // Relax headroom requirements if no matches
    console.warn('No models match headroom requirements, relaxing constraints');
    return selectBestModel(scoredModels, headroomData);
  }

  // 6. Select best model
  return selectBestModel(matchedModels, headroomData);
}

/**
 * Get models from cache or fetch from database
 * @returns {Promise<Array>} Array of models
 */
async function getModels() {
  return await cacheManager.getOrFetch(
    'ai_models_main',
    fetchLatestModels,
    CACHE_TTLS.models
  );
}

/**
 * Filter models by required modalities
 * @param {Array} models - Models to filter
 * @param {Array<string>} requiredModalities - Required modalities
 * @returns {Array} Filtered models
 */
export function filterByModalities(models, requiredModalities = ['text']) {
  if (!requiredModalities || requiredModalities.length === 0) {
    return models;
  }

  return models.filter(model => {
    const inputMods = (model.input_modalities || '').toLowerCase();
    const outputMods = (model.output_modalities || '').toLowerCase();

    // Check if all required input modalities are present
    const hasRequiredInputs = requiredModalities.every(mod =>
      inputMods.includes(mod.toLowerCase())
    );

    // Ensure text output (most queries need text output)
    const hasTextOutput = outputMods.includes('text');

    // Exclude embedding models unless specifically requested
    const isEmbeddingOnly = outputMods.includes('embedding') && !outputMods.includes('text');

    return hasRequiredInputs && hasTextOutput && !isEmbeddingOnly;
  });
}

/**
 * Calculate scores for each model
 * @param {Array} models - Models to score
 * @param {string} queryType - Query type
 * @param {number} complexityScore - Complexity score
 * @param {Object} headroomData - Provider headroom
 * @returns {Array} Models with scores
 */
export function calculateScores(models, queryType, complexityScore, headroomData) {
  return models.map(model => {
    const provider = normalizeProviderName(model.inference_provider);

    // Intelligence Index score (or fallback)
    const intelligenceScore = getIntelligenceScore(model);

    // Latency score
    const latencyScore = LATENCY_SCORES[provider] || 0.5;

    // Headroom score
    const headroomScore = headroomData[provider] || 0;

    // Geography score
    const geographyScore = getGeographyScore(model);

    // License score
    const licenseScore = getLicenseScore(model);

    // Calculate weighted score
    const score =
      intelligenceScore * SELECTION_WEIGHTS.intelligenceIndex +
      latencyScore * SELECTION_WEIGHTS.latency +
      headroomScore * SELECTION_WEIGHTS.rateLimitHeadroom +
      geographyScore * SELECTION_WEIGHTS.geography +
      licenseScore * SELECTION_WEIGHTS.license;

    // Apply query type preference boost
    const preferredProviders = QUERY_TYPE_PREFERENCES[queryType] || [];
    const preferenceBoost = preferredProviders.includes(provider) ? 0.05 : 0;

    return {
      ...model,
      score: Math.min(1.0, score + preferenceBoost),
      intelligenceScore,
      latencyScore,
      headroomScore,
      geographyScore,
      licenseScore
    };
  });
}

/**
 * Get intelligence score for a model (with fallback)
 * @param {Object} model - Model object
 * @returns {number} Intelligence score (0-1)
 */
function getIntelligenceScore(model) {
  // TODO: Integrate with Artificial Analysis API
  // For now, use fallback based on model size

  const modelName = model.human_readable_name.toLowerCase();

  // Try to extract model size
  for (const [size, score] of Object.entries(MODEL_SIZE_SCORES)) {
    if (modelName.includes(size)) {
      return score;
    }
  }

  // Default moderate score
  return 0.6;
}

/**
 * Get geography score for a model
 * @param {Object} model - Model object
 * @returns {number} Geography score (0-1)
 */
function getGeographyScore(model) {
  const country = model.model_provider_country;
  return GEOGRAPHY_SCORES[country] || GEOGRAPHY_SCORES.default;
}

/**
 * Get license score for a model
 * @param {Object} model - Model object
 * @returns {number} License score (0-1)
 */
function getLicenseScore(model) {
  const license = model.license_name;

  if (!license) {
    return LICENSE_SCORES.custom;
  }

  if (OPEN_SOURCE_LICENSES.includes(license)) {
    return LICENSE_SCORES.opensource;
  }

  // Proprietary licenses
  if (license.toLowerCase().includes('gemini')) {
    return LICENSE_SCORES.proprietary;
  }

  return LICENSE_SCORES.custom;
}

/**
 * Match complexity score to headroom requirements
 * @param {Array} models - Scored models
 * @param {number} complexityScore - Query complexity
 * @param {Object} headroomData - Provider headroom
 * @returns {Array} Filtered models
 */
export function matchComplexityToHeadroom(models, complexityScore, headroomData) {
  let requiredHeadroom = 0;

  if (complexityScore > COMPLEXITY_THRESHOLDS.high) {
    requiredHeadroom = 0.6;
  } else if (complexityScore > COMPLEXITY_THRESHOLDS.medium) {
    requiredHeadroom = 0.3;
  }

  return models.filter(model => {
    const provider = normalizeProviderName(model.inference_provider);
    const headroom = headroomData[provider] || 0;
    return headroom >= requiredHeadroom;
  });
}

/**
 * Select the best model from scored models
 * @param {Array} models - Scored models
 * @param {Object} headroomData - Provider headroom
 * @returns {Object} Selected model with metadata
 */
export function selectBestModel(models, headroomData) {
  if (!models || models.length === 0) {
    throw new Error('No models available for selection');
  }

  // Sort by score (descending)
  const sorted = [...models].sort((a, b) => b.score - a.score);

  // Get top model
  const topModel = sorted[0];
  const provider = normalizeProviderName(topModel.inference_provider);

  // Increment usage tracker
  rateLimitTracker.incrementUsage(provider);

  // Build selection reason
  const selectionReason = buildSelectionReason(topModel, headroomData[provider]);

  return {
    provider,
    modelName: extractModelName(topModel),
    humanReadableName: topModel.human_readable_name,
    score: Math.round(topModel.score * 100) / 100,
    rateLimitHeadroom: Math.round(headroomData[provider] * 100) / 100,
    estimatedLatency: getLatencyEstimate(provider),
    intelligenceIndex: Math.round(topModel.intelligenceScore * 100) / 100,
    selectionReason,
    modalities: {
      input: topModel.input_modalities,
      output: topModel.output_modalities
    },
    license: topModel.license_name
  };
}

/**
 * Normalize provider name to lowercase for consistency
 * Maps database values (OpenRouter, Google, Groq) to askme_v2 format (openrouter, google, groq)
 * @param {string} provider - Provider name from database
 * @returns {string} Normalized provider name
 */
function normalizeProviderName(provider) {
  const normalized = provider.toLowerCase();
  // Map 'google' to 'gemini' for askme_v2 compatibility
  if (normalized === 'google') {
    return 'gemini';
  }
  return normalized;
}

/**
 * Extract model name for API calls
 * @param {Object} model - Model object
 * @returns {string} Model name
 */
function extractModelName(model) {
  // For Groq/OpenRouter, often the model name is in the human_readable_name
  // This may need adjustment based on actual data format
  const name = model.human_readable_name.toLowerCase();
  const provider = normalizeProviderName(model.inference_provider);

  if (provider === 'groq') {
    if (name.includes('llama-3.3-70b')) return 'llama-3.3-70b-versatile';
    if (name.includes('llama-3.1-8b')) return 'llama-3.1-8b-instant';
    if (name.includes('llama-3.1-70b')) return 'llama-3.1-70b-versatile';
  }

  if (provider === 'gemini') {
    if (name.includes('gemini-2.0-flash')) return 'models/gemini-2.0-flash';
    if (name.includes('gemini-2.5-pro')) return 'models/gemini-2.5-pro';
    if (name.includes('gemma')) return name;
  }

  // Default: use human_readable_name
  return model.human_readable_name;
}

/**
 * Get latency estimate for provider
 * @param {string} provider - Provider name
 * @returns {string} Latency estimate
 */
function getLatencyEstimate(provider) {
  const score = LATENCY_SCORES[provider] || 0.5;

  if (score >= 0.9) return 'low';
  if (score >= 0.7) return 'medium';
  return 'high';
}

/**
 * Build selection reason explanation
 * @param {Object} model - Selected model
 * @param {number} headroom - Provider headroom
 * @returns {string} Explanation
 */
function buildSelectionReason(model, headroom) {
  const reasons = [];

  if (model.intelligenceScore > 0.8) {
    reasons.push('High intelligence score');
  }

  if (headroom > 0.8) {
    reasons.push('Excellent rate limit headroom');
  } else if (headroom > 0.5) {
    reasons.push('Good rate limit headroom');
  }

  if (model.latencyScore >= 0.9) {
    reasons.push('Fastest provider');
  }

  if (OPEN_SOURCE_LICENSES.includes(model.license_name)) {
    reasons.push('Open-source license');
  }

  return reasons.join(', ') || 'Best overall match';
}

export default { selectModel, filterByModalities, calculateScores, matchComplexityToHeadroom, selectBestModel };
