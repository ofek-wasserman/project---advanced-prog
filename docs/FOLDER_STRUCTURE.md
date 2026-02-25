# Project Folder Structure (Source of Truth)

This document defines the agreed repository layout.
If the structure changes, update this file in the same PR.

---

## High-level layout

project/
├─ src/                          # Application source code
│  ├─ __init__.py
│  ├─ api/                       # FastAPI app, routers, schemas
│  ├─ services/                  # Business logic orchestration
│  ├─ domain/                    # Core domain entities and invariants
│  └─ data/                      # CSV loaders and persistence helpers
│
├─ tests/                        # All tests (mirrors src/ structure)
│  ├─ __init__.py
│  ├─ test_smoke.py              # Basic import/bootstrap sanity test
│  ├─ api/                       # API-level tests
│  ├─ services/                  # Service-layer tests
│  ├─ domain/                    # Domain model tests
│  └─ data/                      # Data/persistence tests
│
├─ data/                         # Initial CSV files (input only)
│  ├─ stations.csv
│  └─ vehicles.csv
│
├─ docs/                         # Project documentation
│  ├─ README.md
│  ├─ DECISIONS.md
│  ├─ WORKFLOW_SUMMARY.md
│  ├─ FOLDER_STRUCTURE.md
│  └─ KICKOFF_PLAN.md
│
├─ .github/
│  ├─ workflows/ci.yml           # CI: ruff + pytest + coverage report
│  └─ PULL_REQUEST_TEMPLATE.md
│
├─ changelog/
│  └─ CHANGELOG.md
│
├─ requirements.txt
├─ pyproject.toml
├─ .gitignore
└─ README.md

> Notes:
> - `tests/` is organized into subfolders to match the `src/` layers.
> - `data/` contains the real CSVs used to bootstrap the application.

---

## Layer responsibilities

### `src/domain/`
Pure domain logic:
- Entities (Vehicle, Station, Ride, User)
- Enums
- Invariants and validation rules  
No I/O, no FastAPI, no CSV access.

### `src/services/`
Business orchestration:
- FleetManager
- ActiveRidesRegistry
- Ride lifecycle logic
- Deterministic selection rules  
May use domain objects.
Does NOT know about HTTP/FastAPI.

### `src/api/`
FastAPI layer:
- App initialization
- Startup bootstrap
- Route definitions
- Request/response schemas
- HTTP error mapping  
Translates HTTP ↔ service calls.

### `src/data/`
Infrastructure layer:
- CSV loading
- Persistence helpers (Phase 2)
Does NOT contain business rules.

---

## Testing structure

The `tests/` directory mirrors `src/`.

### Domain tests (`tests/domain/`)
- Entity invariants
- State transitions
- Enum behavior

### Service tests (`tests/services/`)
- Ride lifecycle orchestration
- Deterministic vehicle selection
- Business rule validation

### Data tests (`tests/data/`)
- CSV parsing + validation
- Loader behavior
- Persistence snapshot load/save logic

### API tests (`tests/api/`)
- Request/response validation
- Error mapping (400 / 404 / 409)
- Endpoint behavior

### Smoke test (`tests/test_smoke.py`)
- Minimal sanity test that imports work and the project boots in CI.

---