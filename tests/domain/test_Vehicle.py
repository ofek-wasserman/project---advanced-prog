from datetime import date

import pytest

from src.domain.enums import VehicleLocation, VehicleStatus
from src.domain.exceptions import ConflictError
from src.domain.Vehicle import Bicycle, EBike, Scooter

# =====================================================
# Fixtures (Reusable Mock Instances)
# =====================================================

@pytest.fixture
def available_bicycle():
    return Bicycle(
        vehicle_id="B1",
        status=VehicleStatus.AVAILABLE,
        rides_since_last_treated=5,
        last_treated_date=date(2026, 1, 1),
        station_id=1,
        active_ride_id=None,
    )

@pytest.fixture
def available_ebike():
    return EBike(
        vehicle_id="E1",
        status=VehicleStatus.AVAILABLE,
        rides_since_last_treated=10,
        last_treated_date=date(2026, 1, 1),
        station_id=1,
        active_ride_id=None,
        charge_pct=80,
    )


@pytest.fixture
def available_scooter():
    return Scooter(
        vehicle_id="S1",
        status=VehicleStatus.AVAILABLE,
        rides_since_last_treated=3,
        last_treated_date=date(2026, 1, 1),
        station_id=1,
        active_ride_id=None,
        charge_pct=50,
    )


# =========================
# BICYCLE TESTS
# =========================

def test_bicycle_is_eligible_happy_path(available_bicycle):
    assert available_bicycle.is_eligible() is True

def test_bicycle_add_ride_count(available_bicycle):
    available_bicycle.add_ride_count()
    assert available_bicycle.rides_since_last_treated == 6

def test_bicycle_not_eligible_if_too_many_rides(available_bicycle):
    available_bicycle.rides_since_last_treated = 11
    assert available_bicycle.is_eligible() is False

def test_bicycle_can_initiate_treatment_when_threshold_reached(available_bicycle):
    available_bicycle.rides_since_last_treated = 7
    assert available_bicycle.can_initiate_treatment() is True

def test_bicycle_can_initiate_treatment_when_degraded(available_bicycle):
    available_bicycle.status = VehicleStatus.DEGRADED
    assert available_bicycle.can_initiate_treatment() is True

def test_bicycle_cannot_initiate_treatment_when_threshold_not_met(available_bicycle):
    available_bicycle.rides_since_last_treated = 5
    assert available_bicycle.can_initiate_treatment() is False

def test_bicycle_cannot_initiate_treatment_when_not_degraded(available_bicycle):
    available_bicycle.status = VehicleStatus.AVAILABLE
    assert available_bicycle.can_initiate_treatment() is False

def test_bicycle_reset_after_apply_treatment(available_bicycle):
    available_bicycle.rides_since_last_treated = 12
    available_bicycle.status = VehicleStatus.DEGRADED

    available_bicycle.apply_treatment(date(2026, 1, 1))

    assert available_bicycle.rides_since_last_treated == 0
    assert available_bicycle.status == VehicleStatus.AVAILABLE

def test_bicycle_dock_to_station(available_bicycle):
    available_bicycle.dock_to_station(station_id=2)

    assert available_bicycle.station_id == 2
    assert available_bicycle.active_ride_id is None
    assert available_bicycle.location == VehicleLocation.DOCKED

def test_bicycle_checkout_to_ride(available_bicycle):
    available_bicycle.checkout_to_ride(ride_id=101)

    assert available_bicycle.station_id is None
    assert available_bicycle.active_ride_id == 101
    assert available_bicycle.location == VehicleLocation.IN_RIDE

def test_bicycle_move_to_repo(available_bicycle):
    available_bicycle.move_to_repo()

    assert available_bicycle.station_id is None
    assert available_bicycle.active_ride_id is None
    assert available_bicycle.location == VehicleLocation.IN_REPO

def test_bicycle_not_eligible_when_active_ride_id_set(available_bicycle):
    available_bicycle.active_ride_id = 999
    assert available_bicycle.is_eligible() is False

def test_mark_degraded_sets_status(available_bicycle):
    available_bicycle.mark_degraded()
    assert available_bicycle.status == VehicleStatus.DEGRADED

def test_mark_degraded_twice_raises_conflict(available_bicycle):
    available_bicycle.mark_degraded()
    with pytest.raises(ConflictError):
        available_bicycle.mark_degraded()


# =========================
# ELECTRIC VEHICLE (EBIKE) TESTS
# =========================

def test_ebike_is_eligible_happy_path(available_ebike):
    assert available_ebike.is_eligible() is True


def test_ebike_not_eligible_if_too_many_rides(available_ebike):
    available_ebike.rides_since_last_treated = 11
    assert available_ebike.is_eligible() is False


def test_ebike_consume_charge(available_ebike):
    available_ebike.consume_charge(distance=15)
    assert available_ebike.charge_pct == 65


def test_ebike_charge_never_negative(available_ebike):
    available_ebike.consume_charge(distance=90)
    assert available_ebike.charge_pct == 0


def test_ebike_recharge(available_ebike):
    available_ebike.recharge()
    assert available_ebike.charge_pct == 100


def test_ebike_not_eligible_when_active_ride_id_set(available_ebike):
    available_ebike.active_ride_id = 999
    assert available_ebike.is_eligible() is False


# =========================
# SCOOTER TESTS
# =========================

def test_scooter_is_eligible(available_scooter):
    assert available_scooter.is_eligible() is True


def test_scooter_not_eligible_if_too_many_rides(available_scooter):
    available_scooter.rides_since_last_treated = 11
    assert available_scooter.is_eligible() is False


def test_scooter_not_eligible_when_active_ride_id_set(available_scooter):
    available_scooter.active_ride_id = 999
    assert available_scooter.is_eligible() is False

