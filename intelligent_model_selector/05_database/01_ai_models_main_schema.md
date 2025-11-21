# ai_models_main Schema

**Last Updated:** 2025-11-19
**Purpose:** Database schema and query patterns

---

## Table Schema

### ai_models_main

**Source:** Populated by ai-models-discoverer_v3 pipeline (daily updates)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | integer | NO | Primary key (auto-increment) |
| inference_provider | text | NO | groq, google, openrouter |
| model_provider | text | NO | Meta, Google, DeepSeek, etc. |
| human_readable_name | text | NO | Display name for UI |
| model_provider_country | text | YES | Provider company country |
| official_url | text | YES | Official model/provider URL |
| input_modalities | text | NO | Comma-separated: Text, Image, Audio, Video, PDF |
| output_modalities | text | NO | Comma-separated: Text, Image, Audio, Video, Text Embeddings |
| license_info_text | text | YES | License information text |
| license_info_url | text | YES | License documentation URL |
| license_name | text | YES | Standardized license (MIT, Apache, Llama-3.1, etc.) |
| license_url | text | YES | Official license terms URL |
| rate_limits | text | YES | API rate limit information |
| provider_api_access | text | YES | URL to get API keys |
| created_at | timestamp | NO | Record creation time |
| updated_at | timestamp | NO | Last update time |

---

## Common Queries

### Fetch All Available Models

```sql
SELECT *
FROM ai_models_main
ORDER BY updated_at DESC;
```

### Filter by Inference Provider

```sql
SELECT *
FROM ai_models_main
WHERE inference_provider = 'groq'
ORDER BY updated_at DESC;
```

### Filter by Modalities

```sql
SELECT *
FROM ai_models_main
WHERE input_modalities LIKE '%Text%'
  AND output_modalities LIKE '%Text%'
  AND output_modalities NOT LIKE '%Embeddings%'
ORDER BY updated_at DESC;
```

### Filter by License (Open Source)

```sql
SELECT *
FROM ai_models_main
WHERE license_name IN (
  'MIT', 'Apache-2.0', 'GPL-3.0',
  'Llama-2', 'Llama-3', 'Llama-3.1', 'Llama-3.2', 'Llama-3.3',
  'Gemma', 'CC-BY-4.0', 'CC-BY-SA-4.0'
)
ORDER BY updated_at DESC;
```

### Filter by Geography

```sql
SELECT *
FROM ai_models_main
WHERE model_provider_country = 'United States'
ORDER BY updated_at DESC;
```

---

## Supabase JavaScript Client

### Fetch All Models

```javascript
const { data, error } = await supabase
  .from('ai_models_main')
  .select('*')
  .order('updated_at', { ascending: false });
```

### Filter by Provider

```javascript
const { data, error } = await supabase
  .from('ai_models_main')
  .select('*')
  .eq('inference_provider', 'groq');
```

### Filter by Modalities

```javascript
const { data, error } = await supabase
  .from('ai_models_main')
  .select('*')
  .ilike('input_modalities', '%Text%')
  .ilike('output_modalities', '%Text%');
```

### Complex Query (Multiple Filters)

```javascript
const { data, error } = await supabase
  .from('ai_models_main')
  .select('*')
  .eq('inference_provider', 'groq')
  .ilike('input_modalities', '%Text%')
  .ilike('output_modalities', '%Text%')
  .in('license_name', ['Llama-3.1', 'Llama-3.3', 'MIT', 'Apache-2.0']);
```

---

## Data Examples

### Groq Model Example

```json
{
  "id": 123,
  "inference_provider": "groq",
  "model_provider": "Meta",
  "human_readable_name": "Llama 3.3 70B Versatile",
  "model_provider_country": "United States",
  "official_url": "https://groq.com",
  "input_modalities": "Text",
  "output_modalities": "Text",
  "license_name": "Llama-3.3",
  "license_url": "https://llama.meta.com/llama3_3/license",
  "rate_limits": "30 requests per minute",
  "created_at": "2025-01-15T...",
  "updated_at": "2025-11-19T..."
}
```

### Google Model Example

```json
{
  "id": 456,
  "inference_provider": "google",
  "model_provider": "Google",
  "human_readable_name": "Gemini 2.0 Flash",
  "model_provider_country": "United States",
  "input_modalities": "Text, Image",
  "output_modalities": "Text",
  "license_name": "Gemini",
  "rate_limits": "60 requests per minute",
  "created_at": "2025-01-10T...",
  "updated_at": "2025-11-19T..."
}
```

---

## Notes

**Update Frequency:** Daily (via GitHub Actions)

**RLS Policies:**
- Public read access (anon key)
- Write access restricted to pipeline_writer role

**Missing Fields:**
- pricing (all models are free)
- context_window (not captured by pipeline)

**Modality Format:**
- Comma-separated strings
- Use LIKE queries for matching
- Example: "Text, Image, Audio"

---

**Document Status:** ✅ Complete
**Document Owner:** Development Team
