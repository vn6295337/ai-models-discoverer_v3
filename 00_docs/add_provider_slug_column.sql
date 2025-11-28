-- Migration: Add provider_slug column to working_version table
-- Date: 2025-11-27
-- Purpose: Store provider-specific model identifiers (API slugs)

-- Add provider_slug column (nullable for backward compatibility)
ALTER TABLE public.working_version
ADD COLUMN IF NOT EXISTS provider_slug TEXT;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_working_version_provider_slug
ON public.working_version(provider_slug);

-- Add comment
COMMENT ON COLUMN public.working_version.provider_slug IS
'Provider-specific model identifier: Google (name), OpenRouter (canonical_slug), Groq (model_id)';
