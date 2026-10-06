# Implementation Plan: Foundation and UI Shell

**Branch**: `001-foundation-ui-shell` | **Date**: 2026-09-13 | **Spec**: [`spec.md`](file:///Users/sanjana/Documents/ai_p2/specs/001-foundation-ui-shell/spec.md)

**Input**: Feature specification from `specs/001-foundation-ui-shell/spec.md`

---

## Summary

This plan details the technical architecture and phase breakdown for **Specification 1: Foundation and UI Shell for the AI Surveillance Command Center**. The implementation establishes the Clean Architecture layers, single-page Streamlit application shell with 7 primary navigation views, custom dark command deck theme, dependency injection container, structured logging, YAML configuration management, SQLite database initialization with startup mock data seeding, and local demo media directory structures.

---

## Technical Context

**Language/Version**: Python 3.11.9  
**Primary Dependencies**: Streamlit 1.56.0, OpenCV 4.12.0, Plotly 6.0.0, PyYAML 6.0.2, Pydantic 2.12.4, Pytest 8.3.0  
**Storage**: SQLite 3 (native `sqlite3` driver)  
**Testing**: Pytest  
**Target Platform**: Local Workstation (macOS / Linux / Windows, 100% Offline)  
**Project Type**: Desktop Web Application (Streamlit Command Center)  
**Performance Goals**: Application startup without noticeable delay; responsive page navigation  
**Constraints**: 100% Offline execution; zero business logic in UI scripts; Clean Architecture; constitution supremacy  
**Scale/Scope**: 7 primary pages; 7 SQLite schema tables; Foundation service abstractions  

---

## Constitution Check

*GATE: Passed prior to Phase 0 research. Re-checked post Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **Modular Development** | PASSED | Decoupled UI, Application, Domain, Infrastructure, and Persistence layers. |
| **Separation of Concerns** | PASSED | Zero domain logic or raw SQL inside Streamlit UI scripts. |
| **Clean Architecture** | PASSED | Domain entities and interfaces independent of UI and DB adapters. |
| **Dependency Injection** | PASSED | Centralized DI Container managing service lifecycles. |
| **Centralized Config** | PASSED | Externalized YAML configuration (`config/system_config.yaml`). |
| **Operator UI & Dark Theme** | PASSED | Minimal navigation (7 pages), dark theme CSS, operator-focused layout. |
| **Unified Surveillance Deck** | PASSED | Single progressive workflow wizard on `pages/surveillance.py`. |
| **Offline Autonomy** | PASSED | Zero runtime internet dependencies; local SQLite & Plotly. |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-foundation-ui-shell/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Technical research & decisions (Phase 0)
├── data-model.md        # Relational entity schemas & seeding spec (Phase 1)
├── quickstart.md        # Runnable verification & test guide (Phase 1)
├── contracts/           # Interfaces & component contracts (Phase 1)
│   └── service_contracts.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
config/
└── system_config.yaml       # Centralized YAML configuration

data/
└── demo/                    # Pre-packaged demo assets directory
    ├── drone/
    │   ├── images/
    │   └── videos/
    └── cctv/
        ├── images/
        └── videos/

src/
├── core/
│   ├── config.py            # ConfigurationService
│   ├── logger.py            # Structured logging initializer
│   ├── exceptions.py        # Centralized exception handlers
│   ├── di_container.py      # Dependency Injection Container
│   └── database.py          # DatabaseService & SQLite initializer
├── domain/
│   ├── entities.py          # Pure Python entity models
│   └── interfaces.py        # Abstract service & repository contracts
├── infrastructure/
│   ├── database/
│   │   ├── models.py        # SQLite table definitions
│   │   └── repositories.py  # SQLite repositories & startup seeder
│   └── services/
│       └── mock_services.py # Placeholder core domain services
└── ui/
    ├── styles.py            # Dark command center CSS injection
    ├── components.py        # Reusable UI widgets (cards, badges, charts)
    └── pages/
        ├── dashboard.py     # 🏠 Dashboard
        ├── surveillance.py  # 📡 Surveillance (Unified 7-step deck)
        ├── analytics.py     # 📊 Analytics
        ├── history.py       # 📁 History
        ├── reports.py       # 📄 Reports
        ├── settings.py      # ⚙ Settings
        └── about.py         # ℹ About

app.py                       # Main Streamlit application entrypoint

tests/
├── unit/
│   ├── test_config.py
│   ├── test_di_container.py
│   └── test_database.py
├── integration/
│   ├── test_startup.py
│   └── test_db_seeding.py
└── ui/
    └── test_page_rendering.py
```

**Structure Decision**: Selected Single Project layout with `src/` modular layering separating Core, Domain, Infrastructure, and UI presentation components.

---

## Complexity Tracking

*No constitution violations or unjustified complexities. Clean Architecture and DI Container strictly enforced.*

---

## Generated Design Artifacts

1. [`research.md`](file:///Users/sanjana/Documents/ai_p2/specs/001-foundation-ui-shell/research.md) — Technical research & architecture decisions.
2. [`data-model.md`](file:///Users/sanjana/Documents/ai_p2/specs/001-foundation-ui-shell/data-model.md) — Relational entity schemas & startup seeding specification.
3. [`quickstart.md`](file:///Users/sanjana/Documents/ai_p2/specs/001-foundation-ui-shell/quickstart.md) — Runnable verification & test guide.
4. [`contracts/service_contracts.md`](file:///Users/sanjana/Documents/ai_p2/specs/001-foundation-ui-shell/contracts/service_contracts.md) — Abstract service contracts and component interfaces.
