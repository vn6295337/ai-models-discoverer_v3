# Utils Directory

## key_client.py

Secure API key management client for accessing provider APIs through Supabase Edge Functions.

### Features
- Secure API key retrieval for Google, OpenRouter, and Groq providers
- Usage logging for rate limit tracking
- Environment variable configuration support
- Comprehensive error handling

### Environment Variables
- `SUPABASE_FUNCTIONS_URL` - Base URL for Supabase functions (optional)
- `SUPABASE_ANON_KEY` - Supabase anonymous key (optional, has fallback)
- `INTERNAL_API_KEY` - Internal API key for authenticated requests

### Usage
```python
from utils.key_client import get_api_key, log_usage

# Get API key
api_key = get_api_key('google')

# Log usage for rate limiting
log_usage('google', 'rpm', 1)
```

### Supported Providers
- `google` - Google AI/Gemini APIs
- `openrouter` - OpenRouter API
- `groq` - Groq API

### Rate Limit Types
- `rpm` - Requests per minute
- `rpd` - Requests per day
- `tpm` - Tokens per minute
- `tpd` - Tokens per day
- `ash` - API calls per hour
- `asd` - API calls per day