# Parallel Rate Limits Table Update Implementation

## Overview

When pipelines update `working_version` table, they now also update `ims.30_rate_limits` table in parallel.

The rate limits table contains parsed rate limit data (rpm, rpd, tpm, tpd) extracted from the `rate_limits` text field in `working_version`. Since all source data comes from the same pipeline run, updating both tables together ensures consistency and eliminates the need for separate rate limits population scripts.

## Files Created

### `rate_limit_parser.py`
Parses rate limit text into structured data (rpm, rpd, tpm, tpd).

Supports 3 formats:
- **Google**: "15 requests/min, 1M tokens/min, 200 requests/day"
- **OpenRouter**: "20 requests/min 50/day"
- **Groq**: "RPM: 30, TPM: 15K, RPD: 14.4K, TPD: 500K"

Handles K/M suffixes: "15K" → 15000, "1M" → 1000000

Falls back to provider defaults when parsing fails:
- Groq: 30 rpm, 15000 tpm
- Google: 15 rpm
- OpenRouter: 20 rpm, 50 rpd

## Files Modified

### `db_utils.py`
Added 2 functions:

**`delete_rate_limits(conn, table_name, inference_provider)`**
- Deletes existing rate limits for one provider
- Table name format: `ims."30_rate_limits"` (quotes only around table name)

**`upsert_rate_limits(conn, table_name, rate_limit_records)`**
- Inserts or updates rate limits using `ON CONFLICT (human_readable_name)`
- Updates: rpm, rpd, tpm, tpd, raw_string, parseable, updated_at

### Refresh Scripts (T, G, I)
All 3 scripts modified identically:

**After successful `working_version` insert:**
1. Parse rate limits for all models
2. Delete existing provider rate limits from `ims.30_rate_limits`
3. Upsert new rate limit records

**Best-effort approach:**
- Parsing failures: log warning, use provider defaults
- Update failures: log warning, don't fail deployment
- `working_version` update always succeeds independently

### GitHub Actions (3 YAML files)
Updated messages:
- "Refresh Working Version + Rate Limits"
- "This will also update ims.30_rate_limits table"
- "✅ Rate limits table updated with parsed rate limits"

## How It Works

```
working_version insert succeeds
    ↓
Parse rate limits for all models (try)
    ↓
Delete existing provider rate limits (try)
    ↓
Upsert new rate limit records (try)
    ↓
Deployment succeeds (regardless of rate limits result)
```

## Troubleshooting

### Error 1: Column Name Mismatch
**Symptom**: Rate limits not updating, no error

**Cause**: Used `model_name` but table uses `human_readable_name`

**Fix**: Changed all occurrences to `human_readable_name` in:
- `db_utils.py` ON CONFLICT clause
- All refresh scripts dictionary key

### Error 2: SQL Syntax Error
**Symptom**:
```
trailing junk after numeric literal at or near ".30_rate_limits"
```

**Cause**: Table name starts with number, needs quotes

**Wrong fix**: `"ims.30_rate_limits"` (quoted entire identifier)

**Correct fix**: `ims."30_rate_limits"` (quotes only around table name)

**Rule**: For `schema.table` where table starts with digit: `schema."table"`

### Error 3: Permission Denied
**Symptom**:
```
permission denied for table 30_rate_limits
```

**Cause**: `pipeline_writer` role lacks permissions on `ims` schema and table

**Fix**: Run SQL commands:
```sql
-- Schema access
GRANT USAGE ON SCHEMA ims TO pipeline_writer;

-- Table access
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE ims."30_rate_limits" TO pipeline_writer;

-- Sequence access
GRANT USAGE, SELECT ON SEQUENCE ims.rate_limits_id_seq TO pipeline_writer;

-- Bypass RLS
ALTER ROLE pipeline_writer BYPASSRLS;
```

**Important**: `BYPASSRLS` skips Row Level Security but does NOT grant INSERT/UPDATE/DELETE. Standard GRANTs are required.

## Verification

Check logs for:
```
✅ Successfully inserted X models
📊 Rate limit records prepared: X
📊 Delete result: True
📊 Upsert result: True
✅ Updated X rate limit records
```

Query database:
```sql
SELECT COUNT(*) FROM ims."30_rate_limits" WHERE inference_provider = 'Groq';
```

## Technical Notes

- Rate limits update uses separate transaction from `working_version`
- Table uses `human_readable_name` as unique key
- Numeric table names require quotes: `ims."30_rate_limits"`
- Parser handles null/empty rate limits with provider fallbacks
- All operations logged with emoji markers for easy scanning
