# Supabase RLS Security Implementation Checklist

## Phase 1: SQL Migration (v3 Tables)

- [x] Generate strong password for `pipeline_writer` role
  - Password: `3bJsgemf+KzZjThQW1PxVca5JihscrPYjUm/t22XyFs=`
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
- [ ] Save `pipeline_writer` connection string in `.env.local`:
  ```
  PIPELINE_SUPABASE_URL=postgresql://pipeline_writer:PASSWORD@db.xxx.supabase.co:5432/postgres
  ```
- [ ] Add `PIPELINE_SUPABASE_URL` to GitHub Actions secrets

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
- [ ] Create `.env.local` with `PIPELINE_SUPABASE_URL` (see `.env.local.example`)
- [ ] Add `PIPELINE_SUPABASE_URL` to GitHub Actions secrets

**Local Testing:**
- [ ] Test OpenRouter pipeline:
  - [ ] Run `T_refresh_supabase_working_version.py` locally
  - [ ] Verify data in `working_version_v3`
  - [ ] Run `U_deploy_to_ai_models_main.py` locally
  - [ ] Verify data in `ai_models_main_v3`
- [ ] Test Groq pipeline:
  - [ ] Run `I_refresh_supabase_working_version.py` locally
  - [ ] Verify data in `working_version_v3`
  - [ ] Run `J_deploy_to_ai_models_main.py` locally
  - [ ] Verify data in `ai_models_main_v3`
- [ ] Test Google pipeline:
  - [ ] Run `G_refresh_supabase_working_version.py` locally
  - [ ] Verify data in `working_version_v3`
  - [ ] Run `H_deploy_to_supabase_ai_models_main.py` locally
  - [ ] Verify data in `ai_models_main_v3`
- [ ] Test RLS policies:
  - [ ] Browser console: Try `SELECT * FROM ai_models_main_v3` with anon key → should succeed
  - [ ] Browser console: Try `INSERT INTO ai_models_main_v3` with anon key → should fail
  - [ ] Browser console: Try `SELECT * FROM working_version_v3` with anon key → should fail
- [ ] Test GitHub Actions with v3 tables

## Phase 5: Production Cutover

- [ ] Run SQL migration on production tables:
  ```sql
  -- Enable RLS
  ALTER TABLE ai_models_main ENABLE ROW LEVEL SECURITY;
  ALTER TABLE working_version ENABLE ROW LEVEL SECURITY;

  -- Public read for ai_models_main only
  CREATE POLICY "Public read" ON ai_models_main FOR SELECT TO anon USING (true);

  -- No policy for working_version (private)

  -- Grant pipeline_writer access
  GRANT SELECT, INSERT, UPDATE, DELETE ON ai_models_main TO pipeline_writer;
  GRANT SELECT, INSERT, UPDATE, DELETE ON working_version TO pipeline_writer;

  -- Full access policies
  CREATE POLICY "Pipeline full access main" ON ai_models_main FOR ALL TO pipeline_writer USING (true) WITH CHECK (true);
  CREATE POLICY "Pipeline full access working" ON working_version FOR ALL TO pipeline_writer USING (true) WITH CHECK (true);
  ```

- [ ] Revert all scripts to production table names:
  - [ ] OpenRouter T: `working_version_v3` → `working_version`
  - [ ] OpenRouter U: `working_version_v3` → `working_version`, `ai_models_main_v3` → `ai_models_main`
  - [ ] Groq I: `working_version_v3` → `working_version`
  - [ ] Groq J: `working_version_v3` → `working_version`, `ai_models_main_v3` → `ai_models_main`
  - [ ] Google G: `working_version_v3` → `working_version`
  - [ ] Google H: `working_version_v3` → `working_version`, `ai_models_main_v3` → `ai_models_main`

- [ ] Test production deployment:
  - [ ] Run one pipeline script locally with production tables
  - [ ] Verify RLS blocking anon writes to production
  - [ ] Run GitHub Actions workflow with production tables

## Phase 6: Validation & Cleanup

- [ ] Verify production security:
  - [ ] Confirm anon key can read `ai_models_main`
  - [ ] Confirm anon key cannot write to `ai_models_main`
  - [ ] Confirm anon key cannot read `working_version`
  - [ ] Confirm `pipeline_writer` can read/write both tables
- [ ] Drop v3 tables:
  ```sql
  DROP TABLE ai_models_main_v3;
  DROP TABLE working_version_v3;
  ```
- [ ] Remove `.bak` backup files from pipeline scripts
- [ ] Document the setup in project README

---

## Implementation Summary

### ✅ Completed (Phase 1-3):
1. **SQL Migration:** RLS enabled on v3 tables, `pipeline_writer` role created
2. **Code Rewrite:** All 6 scripts rewritten to use PostgreSQL + psycopg2
3. **Infrastructure:** `db_utils.py` created, psycopg2 installed
4. **CI/CD:** GitHub Actions workflows updated
5. **Security:** Separated credentials (public anon vs private pipeline_writer)

### ⚠️ Action Required:
1. **Create `.env.local`** with your Supabase project reference
2. **Add `PIPELINE_SUPABASE_URL`** to GitHub Actions secrets
3. **Test Phase 4** before production cutover

### 📊 Code Quality Improvements:
- **Reduced complexity:** -50% average code size
- **Better security:** Direct PostgreSQL with least-privilege role
- **Maintainability:** Shared `db_utils.py` eliminates duplication
- **Performance:** No HTTP API overhead, direct Postgres connection
