# ai_portfolio

Portfolio demonstrating end-to-end AI system capabilities: automated data pipelines, multi-provider integration, and real-time visualization.

---

## 🎯 Portfolio Overview

This portfolio showcases three interconnected projects that form a complete AI infrastructure:

```
Data Discovery → Enrichment Pipeline → Visualization & Access
```

### The Projects

#### 🤖 [askme](https://github.com/vn6295337/askme)
**Zero-config CLI for instant AI queries across providers**

A privacy-focused command-line tool that connects to multiple LLM providers (Google Gemini, Mistral, Llama) through a secure backend proxy. No API keys required locally.

- **Tech Stack**: Kotlin (CLI), Node.js (proxy), Gradle
- **Key Features**: Zero-config, multi-provider, cross-platform
- **Portfolio Value**: Security-conscious architecture, CLI expertise

[View Repository →](https://github.com/vn6295337/askme)

---

#### 📊 [ai-models-discoverer](https://github.com/vn6295337/ai-models-discoverer_v3)
**Automated multi-pipeline for discovering and enriching AI model metadata**

Production-grade data pipeline system that fetches, enriches, and deploys AI model metadata from 7+ providers. Features a comprehensive 19-step OpenRouter pipeline with automated daily runs via GitHub Actions.

- **Tech Stack**: Python, GitHub Actions, Supabase (PostgreSQL)
- **Key Features**: 19-step pipeline, multi-source license extraction, daily automation
- **Portfolio Value**: Data engineering, ETL pipelines, automation expertise

**Metrics**: 400+ models tracked | 7+ providers | 95%+ license coverage

[View Repository →](https://github.com/vn6295337/ai-models-discoverer_v3)

---

#### 📈 [ai-land](https://github.com/vn6295337/ai-land)
**Real-time dashboard visualizing 400+ AI models across 7+ providers**

Interactive React dashboard that visualizes AI model availability and capabilities with real-time updates every 5 minutes. Features dark/light themes and responsive design.

- **Tech Stack**: React 18, TypeScript, Chart.js, Vite, Supabase
- **Key Features**: Interactive charts, real-time updates, responsive design
- **Portfolio Value**: Frontend development, data visualization, UX design

[Live Demo →](https://vn6295337.github.io/ai-land/) | [View Repository →](https://github.com/vn6295337/ai-land)

---

## 🔄 System Integration

```
┌──────────────────────────────────────────────────────────┐
│                    ai_portfolio                           │
│   End-to-End AI Model Discovery & Visualization         │
└──────────────────────────────────────────────────────────┘
                         │
     ┌───────────────────┼───────────────────┐
     │                   │                   │
┌────▼─────┐      ┌──────▼──────┐     ┌─────▼─────┐
│ askme    │      │ discoverer  │     │ ai-land   │
│ CLI      │      │ Pipeline    │     │ Dashboard │
└──────────┘      └─────────────┘     └───────────┘
     │                   │                   │
CLI Access         Data Pipeline       Visualization
Layer              Backend             Frontend
```

### Data Flow
1. **ai-models-discoverer** fetches model metadata from 7+ providers
2. **19-step enrichment pipeline** processes licenses, modalities, pricing
3. **Deploys to Supabase** database
4. **ai-land dashboard** visualizes data in real-time
5. **askme CLI** provides command-line access to AI models

---

## 💼 Technical Capabilities Demonstrated

### Backend & Data Engineering
- ✅ ETL pipeline design (19-step orchestration)
- ✅ Multi-source data aggregation
- ✅ GitHub Actions automation
- ✅ PostgreSQL/Supabase database deployment
- ✅ Python data processing

### Frontend & Visualization
- ✅ React 18 + TypeScript
- ✅ Real-time data visualization (Chart.js)
- ✅ Responsive design (Tailwind CSS)
- ✅ State management
- ✅ Performance optimization

### Architecture & Security
- ✅ Proxy pattern for API key management
- ✅ Row-level security (RLS) policies
- ✅ Multi-tier architecture
- ✅ System integration design
- ✅ Cross-platform compatibility

### DevOps & Automation
- ✅ GitHub Actions workflows
- ✅ Automated deployments (Vercel, GitHub Pages)
- ✅ Build systems (Gradle, Vite, npm)
- ✅ Environment configuration
- ✅ Version control best practices

---

## 📫 Contact

**Looking for AI Transformation expertise?** Let's connect.

- **GitHub**: [@vn6295337](https://github.com/vn6295337)
- **LinkedIn**: [Your LinkedIn Profile]
- **Email**: [Your Email]

---

## 📊 Portfolio Stats

- **3 Production Projects** - All live and functional
- **400+ AI Models** - Tracked and visualized
- **7+ Providers** - OpenRouter, Google, Groq, HuggingFace, Cohere, Mistral, Together
- **Daily Automation** - GitHub Actions pipelines
- **Multi-Language** - Python, TypeScript, Kotlin, Node.js

---

## ⭐ Star These Projects

If you find this portfolio valuable, please consider starring the repositories:

- ⭐ [askme](https://github.com/vn6295337/askme)
- ⭐ [ai-models-discoverer](https://github.com/vn6295337/ai-models-discoverer_v3)
- ⭐ [ai-land](https://github.com/vn6295337/ai-land)

---

## 📝 License

All projects are released under the MIT License.

---

## 🚀 What's Next?

This portfolio is actively maintained and evolving. Future enhancements:
- Performance optimization for ai-land dashboard
- Additional provider integrations
- Enhanced visualization features
- API documentation

---

*Portfolio last updated: 2025-11-10*
