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

----------------------------------------
Fleet Invariants (Phase 1)
----------------------------------------

The following invariants must always hold during runtime.

----------------------------------------
Vehicle Eligibility (Phase 1)
----------------------------------------

A vehicle is considered eligible (rentable) if:

- status == AVAILABLE
- active_ride_id is None
- rides_since_last_treated <= 10

Vehicle degradation rules:

- A vehicle becomes unrentable (degraded) if:
  - rides_since_last_treated > 10, or
  - a user reports it as degraded

Maintenance / treatment rules:

- Treatment may be initiated only on:
  - degraded vehicles, or
  - vehicles with rides_since_last_treated >= 7

Eligibility rules may expand in Phase 2, but the concept of eligibility remains centralized in the service layer.

----------------------------------------
Station Membership Invariant
----------------------------------------

Regular stations must contain only eligible vehicles.

Vehicles that are not eligible must not remain in regular stations.

Specifically:

- Vehicles currently in ride belong to the Active Rides registry.
- Vehicles reported as degraded belong to the Degraded Repository.
- Vehicles with rides_since_last_treated > 10 belong to the Degraded Repository.

----------------------------------------
Bootstrap Normalization Rule
----------------------------------------

On system startup (after CSV bootstrap):

FleetManager must validate all loaded vehicles and normalize system state:

- Ineligible vehicles must be removed from regular stations.
- Ineligible vehicles must be placed in the appropriate repository.
- Regular stations must end initialization containing only eligible vehicles.

This invariant must be maintained on every state transition
(start ride, end ride, maintenance handling).