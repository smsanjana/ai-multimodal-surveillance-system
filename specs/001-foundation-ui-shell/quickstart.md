# Quickstart & Validation Guide: Foundation and UI Shell

**Feature Identifier**: `specs/001-foundation-ui-shell`  
**Created**: 2026-09-13  
**Status**: Completed  
**Governing Documents**: Compliant with `.specify/memory/constitution.md` and `.specify/memory/architecture.md`

---

## 1. Prerequisites & Environment Setup

Ensure Python 3.10+ and project virtual environment are active:

```bash
cd /Users/sanjana/Documents/ai_p2
source venv/bin/activate
pip install streamlit opencv-python plotly pytest pyyaml pydantic
```

---

## 2. Running Automated Tests

Run the full automated pytest suite verifying foundation initialization, database creation, seeding, DI container resolution, and UI rendering:

```bash
pytest tests/ -v
```

### Expected Test Output
- `tests/unit/test_config.py::test_config_loading PASSED`
- `tests/unit/test_di_container.py::test_di_resolution PASSED`
- `tests/unit/test_database.py::test_sqlite_tables_and_seeding PASSED`
- `tests/integration/test_startup.py::test_foundation_startup PASSED`
- `tests/ui/test_page_rendering.py::test_all_7_pages_render PASSED`

---

## 3. Launching the Application Shell

Launch the Streamlit Surveillance Command Center application:

```bash
streamlit run app.py
```

---

## 4. Manual Verification Checklist

### Scenario 1: Navigation Verification
1. Observe sidebar navigation containing strictly 7 items: 🏠 Dashboard, 📡 Surveillance, 📊 Analytics, 📁 History, 📄 Reports, ⚙ Settings, ℹ About.
2. Click through each sidebar item; verify the main viewport renders the selected page without error.

### Scenario 2: Executive Dashboard
1. Verify 6 status metric cards display values (Current Threat, Active Alerts, Today's Analyses, Avg Confidence, Avg Processing Time, Model Status).
2. Confirm 3 Plotly charts (Threat Trend, Detection Trend, Threat Distribution) render.
3. Click "Complete Demonstration" Quick Action; verify application contextually opens the Surveillance page.

### Scenario 3: Unified Surveillance Wizard
1. On 📡 Surveillance, select Step 1 (Built-in Demo), Step 2 (Drone), Step 3 (Image).
2. Select Scenario "Highway Perimeter Patrol" in Step 4.
3. Click "Run Analysis" (Step 5).
4. Verify structured results panels (Step 6) display placeholders for Original Input, Annotated Output, Object Table, Threat Score (MEDIUM), XAI Reason, and Action Buttons (Save / Report).

### Scenario 4: History & Analytics
1. Navigate to 📁 History; verify table displays seeded baseline analysis records.
2. Filter table by Platform (`DRONE`) or Threat Level (`HIGH`).
3. Navigate to 📊 Analytics; confirm visual summaries render from SQLite seeded records.
