# AI Models Discovery Dashboard

An interactive React dashboard that visualizes AI models from multiple providers, helping developers discover and compare available models for their projects.

## 🏗️ System Architecture

  This repository is part of a 3-tier AI Intelligence System:

  ```
  ┌─────────────────────────────────────────────────────────────────┐
  │                  AI INTELLIGENCE SYSTEM                         │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                 │
  │  [1] Discovery Pipeline  →  [2] Dashboard  →  [3] API Gateway   │
  │                                                                 │
  │      ai-models-           ai-land             askme-cli         │
  │      discoverer_v3                                              │
  │                                                                 │
  │  • 8-stage automation    • Real-time viz     • Smart routing    │
  │  • Daily updates         • 75+ models        • Multi-provider   │
  │  • Zero manual work      • Decision support  • Secure access    │
  └─────────────────────────────────────────────────────────────────┘
  ```

  **🔗 Related Repositories:**
  - **[ai-models-discoverer_v3](https://github.com/vn6295337/ai-models-discoverer_v3)** - Automated discovery pipeline 
  - **[ai-land](https://github.com/vn6295337/ai-land)** - Decision intelligence dashboard *(you are 
  here)*
  - **[askme-cli](https://github.com/vn6295337/askme)** - Unified API gateway

  **📊 Data Flow:**
  Discovery Pipeline → Supabase (`ai_models_main` table) → Dashboard + API Gateway

## Features

- **Multi-Provider Support**: Aggregates models from 7+ AI providers
- **Interactive Visualizations**: Bar charts with provider and task type breakdowns
- **Real-time Updates**: Auto-refreshes every 5 minutes
- **Responsive Design**: Works on desktop and mobile devices
- **Task Type Filtering**: Groups small categories for cleaner visualization

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/vn6295337/llm-status-beacon.git
   cd llm-status-beacon
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

4. **Run development server**
   ```bash
   npm run dev
   ```

## Environment Variables

Create a `.env` file with the following variables:

```env
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Technology Stack

- **Frontend**: React 18, TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS, shadcn/ui
- **Charts**: Chart.js with react-chartjs-2
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Compatible with Vercel, Netlify, GitHub Pages

## Data Sources

This dashboard displays publicly available AI model information aggregated from:
- HuggingFace Hub
- OpenRouter
- Google AI
- Cohere
- Groq
- Mistral
- Together AI

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Legal Disclaimer

This dashboard is provided for educational and research purposes only. All model information remains property of respective creators and providers. See the dashboard footer for complete legal disclaimers and attribution requirements.