# ai_portfolio - Dependencies Documentation

**Last Updated**: 2025-11-10
**Purpose**: Consolidated dependency documentation across all three portfolio projects

---

## 📦 Project 1: askme

### Backend (Node.js Proxy)
**Location**: `askme-main/300_implementation/askme-backend/package.json`

**Runtime Requirements:**
- Node.js: >=18.0.0
- npm: >=9.0.0

**Production Dependencies:**
```json
express: ^4.18.2          # Web framework
cors: ^2.8.5              # CORS middleware
express-rate-limit: ^7.1.5 # Rate limiting
axios: ^1.6.2             # HTTP client
dotenv: ^16.3.1           # Environment variables
helmet: ^7.1.0            # Security headers
compression: ^1.7.4        # Response compression
fs-extra: ^11.2.0         # File system utilities
jszip: ^3.10.1            # ZIP file handling
```

**Development Dependencies:**
```json
nodemon: ^3.0.2           # Auto-restart server
jest: ^29.7.0             # Testing framework
eslint: ^8.54.0           # Linting
supertest: ^6.3.3         # HTTP testing
```

### Frontend (Kotlin CLI)
**Location**: `askme-main/300_implementation/askme-cli/`

**Runtime Requirements:**
- Java/OpenJDK: 17 or higher
- Gradle: Wrapper included
- Memory: 512MB RAM minimum
- Storage: 50MB free space

**Build System:**
- Gradle 8.x (via wrapper)
- Kotlin Multiplatform

**Key Dependencies** (managed via Gradle):
- Kotlin Standard Library
- Kotlin Coroutines
- Platform-specific dependencies for Linux/macOS/Windows

---

## 📦 Project 2: ai-models-discoverer_v3

### Python Pipeline
**Location**: `ai-models-discoverer_v3/openrouter_pipeline/requirements.txt`

**Runtime Requirements:**
- Python: 3.11+
- pip: Latest version

**Core HTTP and Web Scraping:**
```
requests>=2.32.0          # HTTP library
httpx>=0.28.0             # Async HTTP client
beautifulsoup4>=4.13.0    # HTML parsing
lxml>=6.0.0               # XML/HTML parser
```

**Data Processing:**
```
pandas>=2.3.0             # Data manipulation
numpy>=2.3.0              # Numerical computing
```

**Database and API:**
```
supabase>=2.18.0          # Supabase client
psycopg2-binary>=2.9.9    # PostgreSQL adapter
huggingface-hub>=0.20.0   # HuggingFace API
```

**Configuration and Environment:**
```
python-dotenv>=1.1.0      # Environment variables
```

**Validation and Typing:**
```
pydantic>=2.11.0          # Data validation
typing-extensions>=4.15.0  # Type hints
```

**Date and Time:**
```
python-dateutil>=2.9.0    # Date utilities
pytz>=2025.2              # Timezone handling
```

**Security and Encoding:**
```
PyJWT>=2.10.0             # JWT tokens
certifi>=2025.8.0         # SSL certificates
charset-normalizer>=3.4.0  # Character encoding
```

**HTTP Core:**
```
httpcore>=1.0.0           # HTTP protocol
h11>=0.16.0               # HTTP/1.1 protocol
anyio>=4.10.0             # Async I/O
idna>=3.10                # Internationalized domain names
urllib3>=2.5.0            # HTTP library
```

**Utilities:**
```
six>=1.17.0               # Python 2/3 compatibility
packaging>=25.0           # Package version handling
soupsieve>=2.8            # CSS selector library
websockets>=15.0.0        # WebSocket support
```

**Installation:**
```bash
pip install -r requirements.txt
# OR from root:
pip install -r openrouter_pipeline/requirements.txt
```

---

## 📦 Project 3: ai-land

### React Dashboard
**Location**: `ai-land-main/package.json`

**Runtime Requirements:**
- Node.js: >=18.0.0 (recommended)
- npm: >=9.0.0

**Core Framework:**
```json
react: ^18.3.1            # React library
react-dom: ^18.3.1        # React DOM renderer
vite: ^5.4.1              # Build tool
typescript: ^5.5.3        # TypeScript
```

**UI Components (Radix UI + shadcn/ui):**
```json
@radix-ui/react-* (27 components)  # Headless UI primitives
class-variance-authority: ^0.7.1   # CSS variants
clsx: ^2.1.1                        # Conditional classes
tailwind-merge: ^2.5.2              # Tailwind utilities
lucide-react: ^0.462.0              # Icon library
```

**Charts and Visualization:**
```json
chart.js: ^4.5.0                    # Chart library
react-chartjs-2: ^5.3.0             # React wrapper for Chart.js
chartjs-adapter-date-fns: ^3.0.0    # Date adapter
recharts: ^2.12.7                   # Alternative charts
date-fns: ^3.6.0                    # Date utilities
```

**State Management and Data:**
```json
@tanstack/react-query: ^5.56.2      # Server state
@supabase/supabase-js: ^2.57.2      # Supabase client
react-hook-form: ^7.53.0            # Form handling
@hookform/resolvers: ^3.9.0         # Form validation
zod: ^3.23.8                        # Schema validation
```

**Routing and Navigation:**
```json
react-router-dom: ^6.26.2           # Client-side routing
```

**Styling:**
```json
tailwindcss: ^3.4.11                # CSS framework
autoprefixer: ^10.4.20              # CSS prefixing
postcss: ^8.4.47                    # CSS processing
tailwindcss-animate: ^1.0.7         # Tailwind animations
@tailwindcss/typography: ^0.5.15    # Typography plugin
next-themes: ^0.3.0                 # Theme management
```

**Utilities:**
```json
jszip: ^3.10.1                      # ZIP file handling
input-otp: ^1.2.4                   # OTP input
embla-carousel-react: ^8.3.0        # Carousel
cmdk: ^1.0.0                        # Command menu
sonner: ^1.5.0                      # Toast notifications
vaul: ^0.9.3                        # Drawer component
react-resizable-panels: ^2.1.3      # Resizable layouts
react-day-picker: ^8.10.1           # Date picker
```

**Analytics and Monitoring:**
```json
@vercel/analytics: ^1.5.0           # Vercel Analytics
```

**Development Tools:**
```json
@vitejs/plugin-react-swc: ^3.5.0    # Vite React plugin
eslint: ^9.9.0                      # Linting
typescript-eslint: ^8.0.1           # TypeScript ESLint
gh-pages: ^6.3.0                    # GitHub Pages deployment
lovable-tagger: ^1.1.7              # Code tagging
```

---

## 🔗 External Services and APIs

### All Projects Use:

**Supabase (PostgreSQL)**
- Database: PostgreSQL via Supabase
- Authentication: Anon key for read-only access
- Row-level security (RLS) policies

**Environment Variables Required:**
```bash
# discoverer
OPENROUTER_API_KEY=xxx
HUGGINGFACE_API_KEY=xxx
SUPABASE_URL=xxx
SUPABASE_KEY=xxx

# ai-land
VITE_SUPABASE_URL=xxx
VITE_SUPABASE_ANON_KEY=xxx

# askme (backend)
GOOGLE_API_KEY=xxx
MISTRAL_API_KEY=xxx
LLAMA_API_KEY=xxx
```

### API Providers:

**AI Model Providers:**
- OpenRouter API
- Google Gemini API
- Mistral AI API
- Llama API
- Groq API
- Cohere API
- Together AI API
- HuggingFace Hub (metadata only)

---

## 📊 Dependency Summary

### Language Distribution:
- **JavaScript/TypeScript**: 2 projects (askme backend, ai-land)
- **Python**: 1 project (discoverer)
- **Kotlin/Java**: 1 project (askme CLI)

### Package Managers:
- **npm**: askme backend, ai-land
- **pip**: discoverer
- **Gradle**: askme CLI

### Total Dependencies:
- **askme backend**: 12 dependencies + 4 devDependencies
- **discoverer**: 45 Python packages
- **ai-land**: 71 dependencies + 13 devDependencies
- **Total**: ~140+ packages across all projects

### Common Patterns:
- **Database**: All use Supabase/PostgreSQL
- **Environment Config**: All use dotenv pattern
- **HTTP Clients**: axios (Node), requests/httpx (Python), built-in (Kotlin)
- **Testing**: jest (Node), none visible (Python), none visible (Kotlin)

---

## 🔒 Security Considerations

### Dependency Security:
- All use specific version ranges (^) for minor updates
- Security-focused packages: helmet, express-rate-limit, PyJWT
- SSL certificate handling: certifi

### Best Practices:
- Environment variables for sensitive data
- .gitignore excludes .env files
- Rate limiting on backend
- CORS configuration
- Security headers (Helmet.js)

---

## 📝 Installation Quick Reference

### askme (backend):
```bash
cd askme-main/300_implementation/askme-backend
npm install
```

### askme (CLI):
```bash
cd askme-main/300_implementation/askme-cli
chmod +x gradlew
./gradlew cliApp:installDist
```

### discoverer:
```bash
cd ai-models-discoverer_v3
python3 -m venv venv
source venv/bin/activate
pip install -r openrouter_pipeline/requirements.txt
```

### ai-land:
```bash
cd ai-land-main
npm install
```

---

## 🔄 Maintenance Notes

### Update Frequency:
- **Monthly**: Check for security updates
- **Quarterly**: Update minor versions
- **Annually**: Review major version upgrades

### Known Issues:
- None documented as of 2025-11-10

### Upcoming Changes:
- None planned

---

**Document Version**: 1.0
**Maintained by**: ai_portfolio
**Related**: See individual project README files for detailed setup instructions
**Repository**: https://github.com/vn6295337/ai_portfolio
