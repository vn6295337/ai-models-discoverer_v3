import { GoogleGenerativeAI } from '@google/generative-ai';
import { getApiKey } from '../utils/supabase.js';
import config from '../config.js';

let geminiClient = null;

/**
 * Initialize Gemini client
 */
const initializeGemini = async () => {
  try {
    const apiKey = await getApiKey('gemini');
    geminiClient = new GoogleGenerativeAI(apiKey);
    return geminiClient;
  } catch (error) {
    console.error('Failed to initialize Gemini:', error.message);
    throw error;
  }
};

/**
 * Call Gemini API
 * @param {string} query - User query
 * @param {string} modelName - Optional model name override (from selector service)
 * @returns {Promise<{response: string, model: string, usage: object}>}
 */
export const callGemini = async (query, modelName = null) => {
  try {
    if (!geminiClient) {
      await initializeGemini();
    }

    const modelToUse = modelName || config.models.gemini;

    const model = geminiClient.getGenerativeModel({
      model: modelToUse,
    });

    const result = await model.generateContent(query);

    // Extract response text
    const response =
      result.response.candidates?.[0]?.content?.parts?.[0]?.text ||
      'No response from Gemini';

    return {
      response,
      model: modelToUse,
      provider: 'gemini',
      usage: {
        promptTokens: result.response.usageMetadata?.promptTokenCount || 0,
        completionTokens: result.response.usageMetadata?.candidatesTokenCount || 0,
        totalTokens: result.response.usageMetadata?.totalTokenCount || 0,
      },
    };
  } catch (error) {
    console.error('Gemini API error:', error.message);
    throw {
      provider: 'gemini',
      error: error.message,
      status: error.status || 500,
    };
  }
};

/**
 * Test Gemini connection
 */
export const testGemini = async () => {
  try {
    const result = await callGemini('Say hello');
    console.log('✅ Gemini test successful:', result);
    return true;
  } catch (error) {
    console.error('❌ Gemini test failed:', error.message);
    return false;
  }
};

export default {
  callGemini,
  testGemini,
};
