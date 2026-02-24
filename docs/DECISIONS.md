# Project Decisions (Source of Truth)

This file freezes technical decisions so the implementation stays consistent across the team.

## IDs and Types
- station_id: int (from stations.csv, never regenerated)
- vehicle_id: int (from vehicles.csv, never regenerated)
- user_id: int (generated incrementally by the system)
- ride_id: int (generated incrementally by the system)

## Deterministic Vehicle Selection
When starting a ride at the selected station:
- Choose the eligible vehicle with the smallest vehicle_id.

## Distance
- Use Euclidean distance on (latitude, longitude) for all "nearest station" logic.

## Pricing
- Phase 1: fixed price of 15 ILS per ride.
- If later rules make a ride free (e.g., degraded report), that is handled in Phase 2 tasks.

## Error Mapping (Service → API)
- 400: invalid input (schema/type/validation)
- 404: entity not found (user/vehicle/station/ride missing)
- 409: invalid state (e.g., user already has an active ride, no eligible vehicles, destination station full)

## Persistence Strategy
- Phase 1: load initial state from CSV on startup (no saving mutable state).
- Phase 2: save/load mutable runtime state (vehicle status/counters, degraded state, active rides if required).
