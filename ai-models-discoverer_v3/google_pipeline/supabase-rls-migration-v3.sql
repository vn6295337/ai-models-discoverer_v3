-- Supabase RLS Security Migration - Phase 1 (v3 Tables)
-- Generated: 2025-10-02
-- Purpose: Enable RLS on test tables, create pipeline_writer role

-- Step 1: Enable RLS on v3 tables
ALTER TABLE ai_models_main_v3 ENABLE ROW LEVEL SECURITY;
ALTER TABLE working_version_v3 ENABLE ROW LEVEL SECURITY;

-- Step 2: Create public read policy for ai_models_main_v3 (anon key can SELECT)
CREATE POLICY "Public read v3" ON ai_models_main_v3
  FOR SELECT
  TO anon
  USING (true);

-- Step 3: No policy for working_version_v3 (private - anon has no access)

-- Step 4: Create pipeline_writer role
-- Password: 3bJsgemf+KzZjThQW1PxVca5JihscrPYjUm/t22XyFs=
CREATE ROLE pipeline_writer LOGIN PASSWORD '3bJsgemf+KzZjThQW1PxVca5JihscrPYjUm/t22XyFs=';
GRANT USAGE ON SCHEMA public TO pipeline_writer;

-- Step 5: Grant table permissions to pipeline_writer
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_models_main_v3 TO pipeline_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON working_version_v3 TO pipeline_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pipeline_writer;

-- Step 6: Create full access RLS policies for pipeline_writer
CREATE POLICY "Pipeline full access main v3" ON ai_models_main_v3
  FOR ALL
  TO pipeline_writer
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Pipeline full access working v3" ON working_version_v3
  FOR ALL
  TO pipeline_writer
  USING (true)
  WITH CHECK (true);

-- Verification queries (run these after migration):
-- SELECT rolname FROM pg_roles WHERE rolname = 'pipeline_writer';
-- SELECT schemaname, tablename, policyname, roles FROM pg_policies WHERE tablename IN ('ai_models_main_v3', 'working_version_v3');
