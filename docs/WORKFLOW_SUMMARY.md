# Project Workflow Summary

## Vehicle Sharing API - Team Workflow

### Branch Strategy

| Branch | Role | Owner | Start |
|--------|------|-------|-------|
| `main` | Protected - production ready | All | - |
| `feature/role1-repo-ci` | Repo / Process / CI Owner | **YOU** | ✅ NOW |
| `feature/role2-api` | API Owner (FastAPI) | TBD | ✅ NOW |
| `feature/role3-services` | Core Services (FleetManager) | TBD | ✅ NOW |
| `feature/role4-domain` | Domain Model (Vehicles/Stations) | TBD | ⏳ Next week |
| `feature/role5-data-persistence` | Data + Persistence (CSV/JSON) | TBD | ⏳ Next week |

---

## Workflow Rules

1. **Branch per task**: `feature/PROJ-XX-description`
2. **PR to main**: Requires CI green + 1 reviewer
3. **Commit messages**: Start with ticket ID: `PROJ-12: Add ride start logic`

---

## Thin Slice Milestone (First Goal)

```
CSV → Load → Register User → Start Ride → End Ride
```

1. Load `stations.csv` and `vehicles.csv` → in-memory state
2. `POST /users/register` → stores payment token, returns user_id
3. `POST /rides/start` → picks deterministic eligible vehicle, creates active ride
4. `POST /rides/{id}/end` → docks at nearest station, computes price

---

## Architecture Layers

```
┌─────────────────────────────────────┐
│           API Layer (FastAPI)       │  ← Role 2
├─────────────────────────────────────┤
│        Services Layer               │  ← Role 3
│  FleetManager, ActiveRidesRegistry  │
│  BillingService                     │
├─────────────────────────────────────┤
│         Domain Layer                │  ← Role 4
│  Vehicle, Station, Ride, User       │
│  Enums, Invariants                  │
├─────────────────────────────────────┤
│          Data Layer                 │  ← Role 5
│  CSV Loaders, Persistence           │
└─────────────────────────────────────┘
```

---

## CI Pipeline (Role 1 - YOUR TASK)

GitHub Actions on every PR:
- [ ] Install dependencies
- [ ] Run linting (ruff/black)
- [ ] Run tests (pytest)

---

## Next Steps

1. ✅ Create branches (done)
2. ⬜ Set up `.github/workflows/ci.yml`
3. ⬜ Create project skeleton (`src/`, `tests/`)
4. ⬜ Add smoke test
5. ⬜ Push to GitHub and verify CI is green
