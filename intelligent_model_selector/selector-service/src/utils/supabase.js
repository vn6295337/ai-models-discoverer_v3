/**
 * Supabase database utilities for querying ai_models_main table
 */

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

// Initialize Supabase client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('SUPABASE_URL and SUPABASE_KEY must be set in environment variables');
}

const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * Fetch all models from ai_models_main table
 * @returns {Promise<Array>} Array of model objects
 */
export async function fetchLatestModels() {
  try {
    const { data, error } = await supabase
      .from('ai_models_main')
      .select('*')
      .order('updated_at', { ascending: false });

    if (error) {
      throw new Error(`Supabase query error: ${error.message}`);
    }

    return data || [];
  } catch (error) {
    console.error('Error fetching models from Supabase:', error);
    throw error;
  }
}

/**
 * Fetch models filtered by inference provider
 * @param {string} provider - Provider name (groq, google, openrouter)
 * @returns {Promise<Array>} Array of model objects
 */
export async function getModelsByProvider(provider) {
  try {
    const { data, error } = await supabase
      .from('ai_models_main')
      .select('*')
      .eq('inference_provider', provider)
      .order('updated_at', { ascending: false });

    if (error) {
      throw new Error(`Supabase query error: ${error.message}`);
    }

    return data || [];
  } catch (error) {
    console.error(`Error fetching models for provider ${provider}:`, error);
    throw error;
  }
}

/**
 * Fetch models filtered by modalities
 * @param {Array<string>} inputModalities - Required input modalities
 * @param {Array<string>} outputModalities - Required output modalities
 * @returns {Promise<Array>} Array of model objects
 */
export async function getModelsByModalities(inputModalities = [], outputModalities = []) {
  try {
    let query = supabase
      .from('ai_models_main')
      .select('*');

    // Apply input modality filters
    inputModalities.forEach(modality => {
      query = query.ilike('input_modalities', `%${modality}%`);
    });

    // Apply output modality filters
    outputModalities.forEach(modality => {
      query = query.ilike('output_modalities', `%${modality}%`);
    });

    const { data, error } = await query.order('updated_at', { ascending: false });

    if (error) {
      throw new Error(`Supabase query error: ${error.message}`);
    }

    return data || [];
  } catch (error) {
    console.error('Error fetching models by modalities:', error);
    throw error;
  }
}

/**
 * Fetch models filtered by license
 * @param {Array<string>} licenses - License names to filter by
 * @returns {Promise<Array>} Array of model objects
 */
export async function getModelsByLicense(licenses) {
  try {
    const { data, error } = await supabase
      .from('ai_models_main')
      .select('*')
      .in('license_name', licenses)
      .order('updated_at', { ascending: false });

    if (error) {
      throw new Error(`Supabase query error: ${error.message}`);
    }

    return data || [];
  } catch (error) {
    console.error('Error fetching models by license:', error);
    throw error;
  }
}

/**
 * Test Supabase connection
 * @returns {Promise<boolean>} True if connection successful
 */
export async function testConnection() {
  try {
    const { data, error } = await supabase
      .from('ai_models_main')
      .select('id')
      .limit(1);

    if (error) {
      console.error('Supabase connection test failed:', error);
      return false;
    }

    return true;
  } catch (error) {
    console.error('Supabase connection test error:', error);
    return false;
  }
}

export default supabase;
