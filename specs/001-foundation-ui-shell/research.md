# Technical Research & Decisions: Foundation and UI Shell

**Feature Identifier**: `specs/001-foundation-ui-shell`  
**Created**: 2026-09-13  
**Status**: Completed  
**Governing Documents**: Compliant with `.specify/memory/constitution.md` and `.specify/memory/architecture.md`

---

## 1. Streamlit Application Shell & Sidebar Navigation Architecture

### Decision
Use a single-page Streamlit application structure controlled by `app.py` and a central stateful sidebar router.

### Rationale
- Standardizing navigation within `app.py` avoids multipage page auto-discovery issues in Streamlit and guarantees that top-level navigation contains strictly the 7 required pages: 🏠 Dashboard, 📡 Surveillance, 📊 Analytics, 📁 History, 📄 Reports, ⚙ Settings, ℹ About.
- Allows session state preservation across navigation switches.

### Alternatives Considered
- **Native Streamlit Multipage (`pages/` auto-loading)**: Rejected because auto-naming and file sorting restrict custom sidebar rendering and make global DI container injection less clean.

---

## 2. Dependency Injection (DI) Container & Service Lifetime Management

### Decision
Implement a custom Python `DIContainer` singleton module (`src/core/di_container.py`) managing service instantiation, configuration injection, and database repository dependencies.

### Rationale
- Strictly aligns with `constitution.md` (Section 2) and `architecture.md` (Section 22).
- Enables zero business logic inside Streamlit pages and facilitates unit testing with mock services.

### Alternatives Considered
- **`dependency-injector` Third-Party Package**: Rejected to keep core architecture simple, zero-external-overhead, and 100% transparent.

---

## 3. SQLite Database Initialization & Startup Seeding Strategy

### Decision
Use Python's native `sqlite3` driver wrapped in a `DatabaseService` (`src/core/database.py`) and repository pattern (`src/infrastructure/database/repositories.py`). Upon application startup, `DatabaseService` creates all schema tables (`analyses`, `detections`, `threat_assessments`, `alerts`, `reports`, `restricted_zones`, `settings`) and automatically seeds baseline realistic mock records if the database is empty.

### Rationale
- Directly implements the accepted clarification decision for Specification 1.
- Guarantees consistent data presentation across Dashboard, Analytics, History, and Settings pages without requiring live AI models.

### Alternatives Considered
- **SQLAlchemy ORM**: Deferred for initial shell to minimize startup latency and keep SQLite queries straightforward; repository interfaces preserve future ORM migration capability.

---

## 4. Custom Dark Command Center CSS Theme

### Decision
Inject custom dark-mode CSS (`src/ui/styles.py`) at startup targeting Streamlit container elements, sidebar, metric cards, threat badges, and tables.

### Color Palette
- Background: Dark Charcoal (`#0E1117` / `#161B22`)
- Surface / Cards: Deep Navy (`#1F2937` / `#2D3748`)
- Text / Headers: High Contrast White & Silver (`#F9FAFB` / `#E5E7EB`)
- Accents / Threat Badges:
  - 🟢 Low Threat: `#10B981` (Emerald Green)
  - 🟡 Medium Threat: `#F59E0B` (Amber Yellow)
  - 🟠 High Threat: `#F97316` (Orange)
  - 🔴 Critical Threat: `#EF4444` (Bright Red)

### Rationale
- Fulfills `constitution.md` (Section 4) and `architecture.md` (Section 5) requirements for an operator-focused dark surveillance command deck.

---

## 5. Reusable Plotly Chart Components

### Decision
Build a Plotly chart factory (`src/ui/components.py`) rendering dark-themed interactive graphs for Threat Trends, Vehicle/Object Distribution, and System Latency.

### Rationale
- Plotly renders natively in Streamlit (`st.plotly_chart`), supports custom dark templates, and works 100% offline.
