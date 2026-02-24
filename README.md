# Vehicle Sharing API — Advanced Programming Final Project

Backend system for a vehicle-sharing service, implemented according to the official course requirements.

## Tech Stack
- Python 3.12
- FastAPI
- Pytest
- GitHub Actions (CI)
- Jira for planning and traceability

## Repository Structure
- src/        → application code
- tests/      → test suite
- data/       → input CSV files (stations, vehicles)
- docs/       → documentation
- .github/    → CI configuration

## Local Setup

Create virtual environment:
    python3.12 -m venv .venv
    source .venv/bin/activate

Install dependencies:
    python -m pip install -r requirements.txt

Run tests:
    python -m pytest -q

Run server:
    uvicorn src.main:app --reload

## Architecture

Layered architecture:

API Layer
→ FastAPI routes and HTTP handling

Services Layer
→ Business logic (ride lifecycle, deterministic selection, pricing)

Domain Layer
→ Entities and invariants (Vehicle, Station, Ride, User)

Data Layer
→ CSV loading and persistence utilities

## Thin Slice (Phase 1)

End-to-end working flow:
1. Load stations.csv and vehicles.csv
2. Register user
3. Start ride (deterministic vehicle selection)
4. End ride (deterministic docking + price calculation)

## Workflow

Branch per Jira ticket:
    feature/KAN-XX-description

PR to main requires:
- 1 approval
- CI passing
- branch up to date

Definition of IN REVIEW:
- PR opened
- CI running or green

Definition of DONE:
- PR merged to main
- CI green on main