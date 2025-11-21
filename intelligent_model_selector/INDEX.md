# Intelligent Model Selector - Documentation Index

**Organized by topic, serial numbered, zero overlaps (MECE).**

---

## Navigation

**Start here:** [README.md](README.md) - Project overview, architecture, quick start

**Then choose your path:**
- [Project Planning](#00-project-planning) - Charter, goals, checklists
- [Getting Started](#01-getting-started) - Setup and installation
- [Architecture](#03-architecture) - System design and algorithms
- [Database](#05-database) - Schema and queries
- [Testing](#06-testing) - Testing strategies
- [Operations](#08-operations) - Configuration and troubleshooting

---

## 00. Project Planning
*Project vision, goals, tracking, and development checklists*

- **00_project/01_clarifications.md** - Key decisions and Q&A
- **00_project/02_project_charter.md** - Mission, goals, success metrics
- **00_project/04_dev_checklist.md** - Atomic task checklist with phases

---

## 01. Getting Started
*Installation, setup, and onboarding guides*

- **01_getting_started/02_setup_guide.md** - Environment setup and configuration

---

## 03. Architecture
*System design, data flows, and algorithms*

- **03_architecture/01_system_architecture.md** - Architecture overview, selection algorithm, caching strategy

---

## 05. Database
*Database schemas, queries, and data models*

- **05_database/01_ai_models_main_schema.md** - ai_models_main table schema and query patterns

---

## 06. Testing
*Testing strategies, guides, and best practices*

- **06_testing/01_testing_strategy.md** - Unit, integration, and performance testing approach

---

## 08. Operations
*Configuration, deployment, monitoring, and troubleshooting*

- **08_operations/01_configuration_reference.md** - Environment variables and configuration options

---

## Quick Reference

| Task | Document |
|------|----------|
| Understand project goals | 00_project/02_project_charter.md |
| Set up development environment | 01_getting_started/02_setup_guide.md |
| Understand selection algorithm | 03_architecture/01_system_architecture.md |
| Query ai_models_main table | 05_database/01_ai_models_main_schema.md |
| Write tests | 06_testing/01_testing_strategy.md |
| Configure service | 08_operations/01_configuration_reference.md |
| Track development progress | 00_project/04_dev_checklist.md |

---

## File Organization

```
intelligent_model_selector/
├── 00_project/              # Project planning & tracking
├── 01_getting_started/      # Setup guides
├── 03_architecture/         # System design
├── 05_database/             # Database documentation
├── 06_testing/              # Testing guides
├── 08_operations/           # Configuration & ops
├── selector-service/        # Backend service code
│   ├── src/
│   │   ├── config/          # Configuration modules
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Utility functions
│   │   └── __tests__/       # Test files
│   ├── .env.example         # Environment template
│   ├── package.json         # NPM configuration
│   └── README.md            # Service-specific docs
├── INDEX.md                 # This file
├── README.md                # Project overview
├── CLAUDE.md                # AI assistant guide
└── LICENSE                  # MIT License
```

---

## Naming Convention

**Documentation files:**
- Format: `##_descriptive_name.md` (serial numbered, snake_case)
- Root files: `UPPERCASE.md` (README, INDEX, CLAUDE)

**Code files:**
- JavaScript: `camelCase.js` (utilities) or `PascalCase.js` (classes/components)
- Config: `lowercase.extension` or `.dotfile`

**Folders:**
- Documentation: `##_lowercase_underscores/` (00-08 prefix)
- Code: `kebab-case/` (e.g., selector-service/)
- Source modules: `lowercase/` or `kebab-case/` (inside src/)
- Tests: `__tests__/` (co-located with source)

---

## MECE Compliance

✅ Each folder covers distinct topic area
✅ No documentation overlap between folders
✅ All aspects of project are documented
✅ Clear navigation path for any task
