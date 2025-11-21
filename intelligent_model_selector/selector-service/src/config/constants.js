/**
 * Configuration constants for model selection
 */

// Selection scoring weights (must sum to 1.0)
export const SELECTION_WEIGHTS = {
  intelligenceIndex: 0.35,
  latency: 0.25,
  rateLimitHeadroom: 0.25,
  geography: 0.10,
  license: 0.05
};

// Provider latency scores (higher = faster)
export const LATENCY_SCORES = {
  groq: 1.0,       // Fastest
  gemini: 0.8,     // Fast (Google Gemini)
  openrouter: 0.6  // Moderate
};

// Complexity thresholds for headroom matching
export const COMPLEXITY_THRESHOLDS = {
  high: 0.7,       // Requires headroom > 0.6
  medium: 0.4      // Requires headroom > 0.3
};

// Rate limit defaults by provider
export const RATE_LIMIT_DEFAULTS = {
  groq: {
    limit: 30,
    window: 60000    // 1 minute in milliseconds
  },
  gemini: {
    limit: 60,
    window: 60000
  },
  openrouter: {
    limit: 200,
    window: 60000
  }
};

// Cache TTLs
export const CACHE_TTLS = {
  models: parseInt(process.env.CACHE_TTL || '1800000', 10),      // 30 minutes default
  intelligenceIndex: 604800000                                    // 7 days
};

// Open source licenses
export const OPEN_SOURCE_LICENSES = [
  'MIT',
  'Apache-2.0',
  'GPL-3.0',
  'BSD-3-Clause',
  'Llama-2',
  'Llama-3',
  'Llama-3.1',
  'Llama-3.2',
  'Llama-3.3',
  'Llama-4',
  'Gemma',
  'CC0-1.0',
  'CC-BY-4.0',
  'CC-BY-SA-4.0'
];

// Model size to score mapping (for fallback scoring)
export const MODEL_SIZE_SCORES = {
  '405b': 1.0,
  '120b': 0.95,
  '70b': 0.9,
  '27b': 0.7,
  '8b': 0.5,
  '4b': 0.4,
  '2b': 0.35,
  '1b': 0.3
};

// Query type to provider preference (for scoring boost)
export const QUERY_TYPE_PREFERENCES = {
  business_news: ['groq', 'openrouter'],
  financial_analysis: ['groq', 'openrouter'],
  creative: ['openrouter', 'gemini'],
  general_knowledge: ['gemini', 'groq']
};

// Geographic preference scores (configurable)
export const GEOGRAPHY_SCORES = {
  'United States': 1.0,
  'default': 0.9  // For unknown or other countries
};

// License preference scores
export const LICENSE_SCORES = {
  opensource: 1.0,
  proprietary: 0.8,
  custom: 0.9
};
