-- Enable pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Create database function to collect analytics data
CREATE OR REPLACE FUNCTION public.collect_daily_analytics()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_total_models INTEGER;
  v_inference_providers JSONB;
  v_model_providers JSONB;
BEGIN
  -- Count total models
  SELECT COUNT(*)
  INTO v_total_models
  FROM public.ai_models_main;

  -- Calculate inference provider counts
  SELECT jsonb_object_agg(
    COALESCE(inference_provider, 'Unknown'),
    count
  )
  INTO v_inference_providers
  FROM (
    SELECT
      inference_provider,
      COUNT(*) as count
    FROM public.ai_models_main
    GROUP BY inference_provider
  ) subq;

  -- Calculate model provider counts
  SELECT jsonb_object_agg(
    COALESCE(model_provider, 'Unknown'),
    count
  )
  INTO v_model_providers
  FROM (
    SELECT
      model_provider,
      COUNT(*) as count
    FROM public.ai_models_main
    GROUP BY model_provider
  ) subq;

  -- Save snapshot using existing RPC function
  PERFORM public.insert_analytics_snapshot(
    v_total_models,
    v_inference_providers,
    v_model_providers
  );

  RAISE NOTICE 'Analytics snapshot collected: % models', v_total_models;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.collect_daily_analytics() TO postgres;

-- Schedule daily execution at 11:59 PM UTC
SELECT cron.schedule(
  'daily-analytics-collection',
  '59 23 * * *',
  'SELECT public.collect_daily_analytics();'
);
