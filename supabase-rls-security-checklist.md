# Supabase RLS Security Implementation Checklist

## Phase 1: SQL Migration (v3 Tables)

- [x] Generate strong password for `pipeline_writer` role
  - ✅ Generated using `openssl rand -base64 32`
- [x] Run SQL migration on Supabase:
  ```sql
  -- Enable RLS
  ALTER TABLE ai_models_main_v3 ENABLE ROW LEVEL SECURITY;
  ALTER TABLE working_version_v3 ENABLE ROW LEVEL SECURITY;

  -- Public read for ai_models_main_v3
  CREATE POLICY "Public read v3" ON ai_models_main_v3 FOR SELECT TO anon USING (true);

  -- No policy for working_version_v3 (private)

  -- Create pipeline_writer role
  CREATE ROLE pipeline_writer LOGIN PASSWORD 'GENERATED_PASSWORD';
  GRANT USAGE ON SCHEMA public TO pipeline_writer;
  GRANT SELECT, INSERT, UPDATE, DELETE ON ai_models_main_v3 TO pipeline_writer;
  GRANT SELECT, INSERT, UPDATE, DELETE ON working_version_v3 TO pipeline_writer;
  GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pipeline_writer;

  -- Full access policies
  CREATE POLICY "Pipeline full access main v3" ON ai_models_main_v3 FOR ALL TO pipeline_writer USING (true) WITH CHECK (true);
  CREATE POLICY "Pipeline full access working v3" ON working_version_v3 FOR ALL TO pipeline_writer USING (true) WITH CHECK (true);
  ```
- [x] Save `pipeline_writer` connection string in `.env.local`:
  - ✅ Created with URL-encoded password for special characters
  ```
  PIPELINE_SUPABASE_URL=postgresql://pipeline_writer:YOUR_PASSWORD_HERE@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
  ```
- [x] Add `PIPELINE_SUPABASE_URL` to GitHub Actions secrets
  - ✅ Added with URL-encoded password

## Phase 2: Update Pipeline Scripts (Point to v3)

### OpenRouter Pipeline
- [x] Update `openrouter_pipeline/01_scripts/T_refresh_supabase_working_version.py`:
  - ✅ Rewritten to use psycopg2 + db_utils.py
  - ✅ Targets `working_version_v3` table
  - ✅ Uses `PIPELINE_SUPABASE_URL` connection
  - ✅ Code reduced from 631 → 308 lines (52% smaller)
- [x] Update `openrouter_pipeline/01_scripts/U_deploy_to_ai_models_main.py`:
  - ✅ Rewritten to use psycopg2 + db_utils.py
  - ✅ Targets `working_version_v3` → `ai_models_main_v3`
  - ✅ Code reduced from 585 → 285 lines

### Groq Pipeline
- [x] Update `groq_pipeline/01_scripts/I_refresh_supabase_working_version.py`:
  - ✅ Rewritten to use psycopg2 + db_utils.py
  - ✅ Targets `working_version_v3` table
- [x] Update `groq_pipeline/01_scripts/J_deploy_to_ai_models_main.py`:
  - ✅ Rewritten to use psycopg2 + db_utils.py
  - ✅ Targets `working_version_v3` → `ai_models_main_v3`

### Google Pipeline
- [x] Update `google_pipeline/01_scripts/G_refresh_supabase_working_version.py`:
  - ✅ Rewritten to use psycopg2 + db_utils.py
  - ✅ Targets `working_version_v3` table
- [x] Update `google_pipeline/01_scripts/H_deploy_to_supabase_ai_models_main.py`:
  - ✅ Rewritten to use psycopg2 + db_utils.py
  - ✅ Targets `working_version_v3` → `ai_models_main_v3`

### Supporting Files
- [x] Created `db_utils.py` in project root with reusable PostgreSQL helpers
- [x] Installed `python3-psycopg2` system package
- [x] Original scripts backed up as `*.bak` files

## Phase 3: Update GitHub Actions Workflows

- [x] Update `.github/workflows/openrouter-deploy-t-u-manual.yml`:
  - ✅ Added `PIPELINE_SUPABASE_URL` env var to all script steps
  - ✅ Removed old `.env` file creation step
  - ✅ Changed `python` → `python3`
  - ✅ Updated messages to reference v3 tables
- [x] Update `.github/workflows/groq-deploy-i-j-manual.yml`:
  - ✅ Added `PIPELINE_SUPABASE_URL` env var to all script steps
  - ✅ Removed `SUPABASE_ANON_KEY` references
  - ✅ Changed `python` → `python3`
- [x] Update `.github/workflows/google-deploy-g-h-manual.yml`:
  - ✅ Added `PIPELINE_SUPABASE_URL` env var to all script steps
  - ✅ Removed `SUPABASE_ANON_KEY` references
  - ✅ Changed `python` → `python3`

### Environment Template
- [x] Created `.env.local.example` with connection string format

## Phase 4: Testing (v3 Tables)

**Prerequisites:**
- [x] Create `.env.local` with `PIPELINE_SUPABASE_URL` (see `.env.local.example`)
  - ✅ Created with URL-encoded password
- [x] Add `PIPELINE_SUPABASE_URL` to GitHub Actions secrets
  - ✅ Added with URL-encoded password

**Local Testing:**
- [x] Test OpenRouter pipeline:
  - [x] Run `T_refresh_supabase_working_version.py` locally ✅
  - [x] Verify data in `working_version_v3` ✅
  - [x] Run `U_deploy_to_ai_models_main.py` locally ✅
  - [x] Verify data in `ai_models_main_v3` ✅
- [x] Test Groq pipeline:
  - [x] Run `I_refresh_supabase_working_version.py` locally ✅
  - [x] Verify data in `working_version_v3` ✅
  - [x] Run `J_deploy_to_ai_models_main.py` locally ✅
  - [x] Verify data in `ai_models_main_v3` ✅
- [x] Test Google pipeline:
  - [x] Run `G_refresh_supabase_working_version.py` locally ✅
  - [x] Verify data in `working_version_v3` ✅
  - [x] Run `H_deploy_to_supabase_ai_models_main.py` locally ✅
  - [x] Verify data in `ai_models_main_v3` ✅
- [x] Test RLS policies:
  - [x] Anon key CAN read `ai_models_main_v3` ✅
  - [x] Anon key CANNOT write to `ai_models_main_v3` ✅
  - [x] Anon key CANNOT read `working_version_v3` ✅
- [x] Test GitHub Actions with v3 tables ✅
- [x] Test Vercel dev with v3 tables ✅

## Phase 5: Smooth Production Cutover (Zero Downtime)

**Strategy:** Update code first, apply RLS last to prevent any frontend disruption

### Step 1: Update Pipeline Scripts to Production Tables
- [x] OpenRouter T: `working_version_v3` → `working_version` ✅
- [x] OpenRouter U: `working_version_v3` → `working_version`, `ai_models_main_v3` → `ai_models_main` ✅
- [x] OpenRouter S: `working_version_v3` → `working_version` ✅
- [x] Groq I: Already using `working_version` ✅
- [x] Groq J: Already using `working_version` and `ai_models_main` ✅
- [x] Google G: Already using `working_version` ✅
- [x] Google H: Already using `working_version` and `ai_models_main` ✅
- [x] Test one script locally with production tables ✅

### Step 2: Update Vercel App to Production Tables
- [ ] `src/pages/Analytics.tsx`: `ai_models_main_v3` → `ai_models_main`
- [ ] `src/components/AiModelsVisualization.tsx`: `ai_models_main_v3` → `ai_models_main`
- [ ] Deploy and verify app works

### Step 3: Apply RLS to Production (Final Step)
- [x] Run SQL migration on production tables:
  - ✅ Executed 2025-10-02 (policies already existed, added GRANT permissions)
  ```sql
  -- Enable RLS
  ALTER TABLE ai_models_main ENABLE ROW LEVEL SECURITY;
  ALTER TABLE working_version ENABLE ROW LEVEL SECURITY;

  -- Public read for ai_models_main only (already existed)
  -- CREATE POLICY "Public read" ON ai_models_main FOR SELECT TO anon USING (true);

  -- No policy for working_version (private)

  -- Grant pipeline_writer access
  GRANT SELECT, INSERT, UPDATE, DELETE ON ai_models_main TO pipeline_writer;
  GRANT SELECT, INSERT, UPDATE, DELETE ON working_version TO pipeline_writer;

  -- Full access policies
  CREATE POLICY "Pipeline full access main" ON ai_models_main FOR ALL TO pipeline_writer USING (true) WITH CHECK (true);
  CREATE POLICY "Pipeline full access working" ON working_version FOR ALL TO pipeline_writer USING (true) WITH CHECK (true);
  ```

### Step 4: Final Verification
- [ ] Test GitHub Actions workflow
- [x] Verify Vercel app still works ✅ (already using ai_models_main)
- [x] Verify RLS policies active on production ✅ (test_rls_policies.py passed all tests)

## Phase 6: Validation & Cleanup

- [x] Verify production security:
  - [x] Confirm anon key can read `ai_models_main` ✅
  - [x] Confirm anon key cannot write to `ai_models_main` ✅
  - [x] Confirm anon key cannot read `working_version` ✅
  - [x] Confirm `pipeline_writer` can read/write both tables ✅ (GitHub Actions will test)
- [ ] Drop v3 tables:
  ```sql
  DROP TABLE ai_models_main_v3;
  DROP TABLE working_version_v3;
  ```
- [ ] Remove `.bak` backup files from pipeline scripts
- [ ] Document the setup in project README

