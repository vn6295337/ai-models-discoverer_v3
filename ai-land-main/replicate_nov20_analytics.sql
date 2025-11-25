-- ============================================================================
-- Replicate November 20th Analytics Data to November 21-23, 2025
-- ============================================================================
-- This script copies the model counts data from November 20th to the
-- subsequent three days (Nov 21, 22, 23) to populate missing analytics data.
--
-- INSTRUCTIONS:
-- 1. Open your Supabase SQL Editor
-- 2. Copy and paste this entire script
-- 3. Run it to insert the replicated data
-- ============================================================================

-- First, let's verify what data exists for November 20th
-- (Uncomment the following line to view the data before inserting)
-- SELECT * FROM analytics_history WHERE DATE(timestamp) = '2025-11-20';

-- ============================================================================
-- Insert November 21st data (copy of Nov 20th)
-- ============================================================================
INSERT INTO analytics_history (timestamp, total_models, inference_provider_counts, model_provider_counts)
SELECT
  '2025-11-21T00:00:00Z'::timestamptz AS timestamp,
  total_models,
  inference_provider_counts,
  model_provider_counts
FROM analytics_history
WHERE DATE(timestamp) = '2025-11-20'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Insert November 22nd data (copy of Nov 20th)
-- ============================================================================
INSERT INTO analytics_history (timestamp, total_models, inference_provider_counts, model_provider_counts)
SELECT
  '2025-11-22T00:00:00Z'::timestamptz AS timestamp,
  total_models,
  inference_provider_counts,
  model_provider_counts
FROM analytics_history
WHERE DATE(timestamp) = '2025-11-20'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Insert November 23rd data (copy of Nov 20th)
-- ============================================================================
INSERT INTO analytics_history (timestamp, total_models, inference_provider_counts, model_provider_counts)
SELECT
  '2025-11-23T00:00:00Z'::timestamptz AS timestamp,
  total_models,
  inference_provider_counts,
  model_provider_counts
FROM analytics_history
WHERE DATE(timestamp) = '2025-11-20'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Verify the results
-- ============================================================================
-- Run this query to confirm the data was inserted correctly:
SELECT
  DATE(timestamp) as date,
  total_models,
  inference_provider_counts,
  model_provider_counts,
  created_at
FROM analytics_history
WHERE DATE(timestamp) BETWEEN '2025-11-20' AND '2025-11-23'
ORDER BY timestamp;
