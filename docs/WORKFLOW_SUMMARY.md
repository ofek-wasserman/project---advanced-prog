# Vehicle Sharing API — Team Workflow (Jira + GitHub)

This document is the **source of truth** for how we work as a team:
- how we create Jira stories,
- how we branch,
- how we open PRs,
- what “IN REVIEW” and “DONE” mean,
- and what is required to satisfy the course requirements.

---

## 1) Scope & Requirements (from the assignment)

### Must-have constraints
- **Python version: 3.12**.
- API implemented as **async REST API** (async endpoints).
- **All inputs validated** (request schemas + service-level validation).
- System must manage state: users, vehicles, stations, rides, degraded repo, maintenance/treatment.
- System must **support server restarts without corrupting dataset state** (persistence model documented).
- Collaboration quality is graded: **PRs, reviews, CI**, and Jira planning.
- Documentation deliverables include:
  - README with clear run instructions
  - API documentation (how to start the server)
  - Design PDF (class hierarchy, ride flow, vehicle types handling, patterns, team responsibilities)
  - Link to repository + link to Jira project (read access to course staff)

(See project instructions for full details.)  

---

## 2) Jira Process (Epics → Stories → PRs)

### 2.1 Epics (our current 5)
1. **SETUP & CI**
2. **DOMAIN MODEL**
3. **DATA LAYER**
4. **SERVICES**
5. **API LAYER**

> We may add additional epics later only if truly necessary, but we work with these 5 first.

### 2.2 Story rules (what a “good” story looks like)
Every story must have:
- clear **goal**
- **acceptance criteria** (what proves it’s done)
- **phase label**: `Phase01` or `Phase02`
- owner/assignee (if known)
- link to relevant decisions (see `docs/DECISIONS.md`)

### 2.3 Jira ↔ GitHub linking (mandatory)
**PR title must start with the Jira key**, e.g.:
- `KAN-38 Implement Ride and User Entities`
- `KAN-17 API: POST /ride/start`

This is required so reviewers and staff can see traceability.

---

## 3) Phases (Thin Slice first)

### Phase 01 — Thin Slice (minimum end-to-end system)
Goal: deliver a working vertical flow:
1) Load `stations.csv` + `vehicles.csv` into memory  
2) `POST /register`  
3) `POST /ride/start`  
4) `POST /ride/end` (charges 15 ILS per ride)  

Notes:
- Must apply eligibility rules and station capacity rules.
- Must keep consistent state (vehicles docked vs active ride).

### Phase 02 — Extended behaviors & robustness
Includes (as needed by requirements):
- degraded vehicle report flow (`/vehicle/report-degraded`)
- maintenance/treat flow (`/vehicle/treat`)
- more persistence (saving mutable state across restarts)
- richer tests: integration/API tests, coverage improvements
- concurrency/locking decisions (documented)

---

## 4) Branch Strategy

### Protected branch
- `main` is protected (production-ready).
- Nobody pushes directly to `main`.

### Branch per story
Create a branch per Jira story:

**Format**
- `feature/KAN-XX-short-description`
Examples:
- `feature/KAN-39-domain-unit-tests`
- `feature/KAN-17-ride-start-endpoint`
- `feature/KAN-32-persistence-save-load`

### Why this matters
The assignment explicitly checks:
- different participants pushed commits via PRs,
- every PR reviewed by a different participant,
- each PR linked to a Jira story.

---

## 5) Pull Requests (PR) Rules

### 5.1 When to open a PR
Open PR as soon as the story has a meaningful change (even if not final).
Use **Draft PR** if not ready for review yet.

### 5.2 PR checklist (must satisfy before merge)
A PR can be merged only when:
- ✅ CI checks are green (tests + lint if configured)
- ✅ At least **1 reviewer approval**
- ✅ PR title contains the Jira key (`KAN-XX`)
- ✅ Description explains what changed and how to verify

### 5.3 What “IN REVIEW” means
Move the Jira story to **IN REVIEW** only when:
- a PR is opened to `main`,
- reviewer(s) were requested,
- CI is running or already green.

### 5.4 What “DONE” means (important!)
Mark Jira story **DONE** only after:
- PR is **merged into `main`**
- CI is green on `main` after merge

If someone implemented something locally or on a branch but it’s not merged → **it is NOT DONE**.

---

## 6) CI (GitHub Actions)

### Required behavior
CI must run automatically on:
- every PR to `main`
- (optional but recommended) every push to feature branches

### Minimum CI jobs
- install dependencies
- run tests (`pytest`)
- (recommended) lint/format checks

### If CI fails
- Fix in the same branch, push again → CI reruns automatically.
- Do not merge with failing checks.

---

## 7) Definition of “Done” by Layer (acceptance criteria examples)

### DOMAIN MODEL
- Classes exist: Station, Vehicle (with subtypes), User, Ride, enums/status types.
- Invariants enforced:
  - vehicle is in exactly one state: docked / active ride / degraded repo
  - eligibility rules: available AND rides_since_last_treated <= 10

### DATA LAYER
- CSV loading works from `/data/stations.csv` and `/data/vehicles.csv`.
- Data mapping is correct to domain objects.
- Persistence decision documented (what is persisted, when, and limitations).

### SERVICES
- FleetManager orchestrates flows:
  - nearest station calculation
  - deterministic vehicle selection rule (documented)
  - station capacity enforcement on end ride
  - billing at end ride (15 ILS fixed)
- State tracked:
  - active rides
  - active users
  - station inventory
  - degraded repository

### API LAYER
- Endpoints are async:
  - POST /register
  - POST /ride/start
  - POST /ride/end
  - POST /vehicle/report-degraded
  - POST /vehicle/treat
  - GET /stations/nearest
  - GET /rides/active-users
- Errors follow convention:
  - 400 invalid input
  - 404 missing entity
  - 409 invalid/conflicting state

---

## 8) Documentation deliverables (what we must submit)

We must have:
- `README.md` with:
  - setup instructions
  - install requirements
  - how to run API
  - how to run tests
- API usage notes (can be in README or separate docs)
- Design PDF:
  - class hierarchy
  - ride flow
  - how vehicle types differ
  - design patterns used
  - team responsibilities
  - architecture diagram + how it evolved
- Public repo link (can switch to public before submission)
- Jira link + grant read access to course staff emails (per assignment)

---

## 9) Quick “How to work” (daily routine)

1. Pick a Jira story in the current epic (Phase01 first).
2. Create branch `feature/KAN-XX-...`
3. Implement + add/adjust tests as needed.
4. Open PR titled `KAN-XX ...`
5. Request reviewer
6. When approved and CI green → merge
7. Move Jira story to DONE only after merge

---

## 10) Important project decisions live here
- `docs/DECISIONS.md`
If there is any ambiguity (selection rule, persistence rule, error mapping, etc.),
we write it there before implementing.
