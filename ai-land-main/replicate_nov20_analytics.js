#!/usr/bin/env node

/**
 * Replicate November 20th Analytics Data to November 21-23, 2025
 *
 * This script copies the model counts data from November 20th to the
 * subsequent three days (Nov 21, 22, 23) to populate missing analytics data.
 *
 * USAGE:
 *   node replicate_nov20_analytics.js
 *
 * PREREQUISITES:
 *   1. Create a .env file with your Supabase credentials:
 *      VITE_SUPABASE_URL=your_supabase_project_url
 *      VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
 *   2. Install dependencies: npm install @supabase/supabase-js dotenv
 */

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config({ path: join(__dirname, '.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Error: Missing Supabase credentials in .env file');
  console.error('Please ensure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function replicateNov20Data() {
  console.log('🔍 Querying November 20th data...\n');

  // Query November 20th data
  const { data: nov20Data, error: queryError } = await supabase
    .from('analytics_history')
    .select('*')
    .gte('timestamp', '2025-11-20T00:00:00Z')
    .lt('timestamp', '2025-11-21T00:00:00Z')
    .single();

  if (queryError) {
    console.error('❌ Error querying November 20th data:', queryError);
    process.exit(1);
  }

  if (!nov20Data) {
    console.error('❌ No data found for November 20th');
    process.exit(1);
  }

  console.log('✅ Found November 20th data:');
  console.log(`   Total Models: ${nov20Data.total_models}`);
  console.log(`   Inference Providers: ${JSON.stringify(nov20Data.inference_provider_counts)}`);
  console.log(`   Model Providers: ${JSON.stringify(nov20Data.model_provider_counts)}\n`);

  // Dates to replicate to
  const targetDates = [
    { date: '2025-11-21T00:00:00Z', label: 'November 21st' },
    { date: '2025-11-22T00:00:00Z', label: 'November 22nd' },
    { date: '2025-11-23T00:00:00Z', label: 'November 23rd' }
  ];

  // Insert data for each target date
  for (const { date, label } of targetDates) {
    console.log(`📝 Inserting data for ${label}...`);

    const { error: insertError } = await supabase
      .from('analytics_history')
      .insert({
        timestamp: date,
        total_models: nov20Data.total_models,
        inference_provider_counts: nov20Data.inference_provider_counts,
        model_provider_counts: nov20Data.model_provider_counts
      });

    if (insertError) {
      console.error(`   ❌ Error inserting ${label}:`, insertError);
    } else {
      console.log(`   ✅ Successfully inserted ${label}`);
    }
  }

  console.log('\n🎉 Replication complete! Verifying results...\n');

  // Verify the results
  const { data: verifyData, error: verifyError } = await supabase
    .from('analytics_history')
    .select('*')
    .gte('timestamp', '2025-11-20T00:00:00Z')
    .lt('timestamp', '2025-11-24T00:00:00Z')
    .order('timestamp', { ascending: true });

  if (verifyError) {
    console.error('❌ Error verifying data:', verifyError);
    process.exit(1);
  }

  console.log('📊 Analytics data for Nov 20-23:');
  console.log('─'.repeat(80));
  verifyData?.forEach(record => {
    const date = new Date(record.timestamp).toISOString().split('T')[0];
    console.log(`Date: ${date}`);
    console.log(`  Total Models: ${record.total_models}`);
    console.log(`  Inference Providers: ${JSON.stringify(record.inference_provider_counts)}`);
    console.log(`  Model Providers: ${JSON.stringify(record.model_provider_counts)}`);
    console.log('─'.repeat(80));
  });

  console.log('\n✅ All done! Check your analytics page at https://ai-land.vercel.app/analytics');
}

// Run the script
replicateNov20Data().catch(error => {
  console.error('❌ Unexpected error:', error);
  process.exit(1);
});
