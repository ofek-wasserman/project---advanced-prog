# Project Decisions (Source of Truth)

This file freezes technical decisions so the implementation stays consistent across the team.
If a rule affects correctness, it must appear here.

----------------------------------------
IDs and Types
----------------------------------------

- station_id: int (from stations.csv, never regenerated)
- vehicle_id: str (from vehicles.csv, never regenerated)
- user_id: int (generated incrementally by the system)
- ride_id: int (generated incrementally by the system)

IDs are never reused.

----------------------------------------
Deterministic Vehicle Selection
----------------------------------------

When starting a ride at the selected station:
- Choose the eligible vehicle with the smallest vehicle_id.

No randomness is allowed anywhere in the system.

----------------------------------------
Distance Calculation
----------------------------------------

- Use Euclidean distance on (latitude, longitude) for all "nearest station" logic.
- If tie occurs, choose station with smallest station_id.

----------------------------------------
Pricing
----------------------------------------

Phase 1:
- Fixed price of 15 ILS per ride.

Future phases:
- Additional pricing rules (e.g., degraded handling) will be implemented in Phase 2.

Pricing logic lives strictly in the service layer.

----------------------------------------
Error Mapping (Service → API)
----------------------------------------

400:
    Invalid input (schema/type/validation)

404:
    Entity not found (user/vehicle/station/ride missing)

409:
    Invalid state transition
    (e.g., user already has active ride,
     no eligible vehicles,
     destination station full)

Service layer raises domain/service errors.
API layer translates them into HTTP responses.

----------------------------------------
Persistence Strategy
----------------------------------------

Phase 1:
- Load initial state from CSV on startup.
- No saving of mutable runtime state.

Phase 2:
- Save/load mutable runtime state
  (vehicle status, degraded state, active rides if required).
- Restart behavior must not corrupt state.