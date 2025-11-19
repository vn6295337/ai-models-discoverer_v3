
**Organized by topic, serial numbered, zero overlaps (MECE).**

---

## Navigation

**Start here:** README.md

**Then choose path:**
- [Getting Started](#getting-started) - New users
- [Development](#development) - Developers
- [Architecture](#architecture) - System design
- [API](#api) - Endpoint reference
- [Database](#database) - Data model
- [Testing](#testing) - Test guides
- [Deployment](#deployment) - Build & release
- [Operations](#operations) - Config & troubleshooting
- [Project](#project) - Planning, charter, status

---

## Getting Started
*User installation and quick start*

- **01_getting_started/02_install_guide.md** - Install APK, first run, features
- **01_getting_started/03_quick_build_checklist.md** - 30-min build checklist

---

## Development
*Setup, contribution, code style*

- **02_development/01_contributing.md** - Setup, git workflow, PR checklist

---

## Architecture
*System design, data flows*

- **03_architecture/01_system_architecture.md** - System layers, data flows, routing

---

## API
*Endpoint reference, examples*

- **04_api/01_api_endpoints.md** - Endpoints, request/response, examples

---

## Database
*Schema, tables, lifecycle*

- **05_database/01_database_schema.md** - Tables, columns, indexes, relations

---

## Testing
*Test guides for all phases*

- **06_testing/01_e2e_testing_guide.md** - 15 E2E scenarios
- **06_testing/02_stress_testing_guide.md** - 10 stress tests
- **06_testing/03_security_testing_guide.md** - 10 security tests
- **06_testing/04_accessibility_testing_guide.md** - 12 accessibility tests

---

## Deployment
*Backend & APK build, release*

- **07_deployment/01_backend_deployment.md** - Backend deployment to Render
- **07_deployment/02_apk_build_steps_detailed.md** - Detailed build steps
- **07_deployment/03_apk_release_guide.md** - GitHub release, version control

---

## Operations
*Configuration, troubleshooting*

- **08_operations/01_configuration_reference.md** - Environment variables, rates
- **08_operations/02_troubleshooting_guide.md** - Installation, runtime, offline issues

---

## Project
*Planning, decision rationale, and status*

- **00_project/01_clarifications.md** - Design decision Q&A and reasoning (decision log)
- **00_project/02_project_charter.md** - Project mission, goals, risk assessment, success metrics
- **00_project/04_dev_checklist.md** - Development checklist with atomic tasks by phase
- **README.md** - Project overview, privacy, features
- **LICENSE** - MIT license

---

## Quick References

| Task | Document |
|------|----------|
| Understand "why" decisions | 00_project/01_clarifications.md |
| Review project goals | 00_project/02_project_charter.md |
| Check development progress | 00_project/04_dev_checklist.md |
| Install app | 01_getting_started/02_install_guide.md |
| Set up dev | 02_development/01_contributing.md |
| Understand system | 03_architecture/01_system_architecture.md |
| Call API | 04_api/01_api_endpoints.md |
| View database | 05_database/01_database_schema.md |
| Test app | 06_testing/* |
| Deploy backend | 07_deployment/01_backend_deployment.md |
| Build APK | 07_deployment/02_apk_build_steps_detailed.md |
| Configure | 08_operations/01_configuration_reference.md |
| Fix issues | 08_operations/02_troubleshooting_guide.md |

---

## File Organization

```
askme_v2/
├── INDEX.md                              (this file - documentation index & navigation)
├── README.md                             (project overview)
├── LICENSE                               (MIT license)
│
├── 00_project/                           (project planning & tracking)
│   ├── 01_clarifications.md              (design decision Q&A)
│   ├── 02_project_charter.md             (project goals & planning)
│   └── 04_dev_checklist.md               (development checklist by phase)
│
├── 01_getting_started/
│   ├── 02_install_guide.md
│   └── 03_quick_build_checklist.md
│
├── 02_development/
│   └── 01_contributing.md
│
├── 03_architecture/
│   └── 01_system_architecture.md
│
├── 04_api/
│   └── 01_api_endpoints.md
│
├── 05_database/
│   └── 01_database_schema.md
│
├── 06_testing/
│   ├── 01_e2e_testing_guide.md
│   ├── 02_stress_testing_guide.md
│   ├── 03_security_testing_guide.md
│   └── 04_accessibility_testing_guide.md
│
├── 07_deployment/
│   ├── 01_backend_deployment.md
│   ├── 02_apk_build_steps_detailed.md
│   └── 03_apk_release_guide.md
│
└── 08_operations/
    ├── 01_configuration_reference.md
    └── 02_troubleshooting_guide.md
```

---

## Naming Convention

- **Lowercase** with underscores (no spaces or hyphens)
- **Serial numbering** by logical reading order within each folder
- **Clear names** describing content
- **Folder structure:** 00_project (planning), 01-08 (topic-based implementation guides)
- **Root level:** README.md, LICENSE only (project overview and license)

---

## MECE Compliance

✅ No overlaps (each topic once)
✅ Complete coverage (no gaps)
✅ Lean (no fluff)
✅ Organized (clear hierarchy)
✅ Navigable (this index)

