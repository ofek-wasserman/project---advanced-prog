from datetime import datetime, timedelta

import pytest

from src.domain.ride import Ride


@pytest.fixture
def create_valid_ride():
    return Ride(
        ride_id=1,
        user_id=10,
        vehicle_id="V100",
        start_time=datetime(2026, 1, 1, 12, 0, 0),
        start_station_id=5,
    )


# ---------------------------
# Constructor Invariants
# ---------------------------

def test_ride_creation_valid(create_valid_ride):

    assert create_valid_ride.is_active() is True
    assert create_valid_ride.end_time is None
    assert create_valid_ride.end_station_id is None
    assert create_valid_ride.reported_degraded is False
    assert create_valid_ride.price is None


def test_ride_id_must_be_positive():
    with pytest.raises(ValueError):
        Ride(
            ride_id=0,
            user_id=1,
            vehicle_id="V1",
            start_time=datetime.now(),
            start_station_id=1,
        )


def test_user_id_must_be_positive():
    with pytest.raises(ValueError):
        Ride(
            ride_id=1,
            user_id=0,
            vehicle_id="V1",
            start_time=datetime.now(),
            start_station_id=1,
        )


def test_vehicle_id_must_not_be_empty():
    with pytest.raises(ValueError):
        Ride(
            ride_id=1,
            user_id=1,
            vehicle_id="",
            start_time=datetime.now(),
            start_station_id=1,
        )


def test_start_station_must_be_positive():
    with pytest.raises(ValueError):
        Ride(
            ride_id=1,
            user_id=1,
            vehicle_id="V1",
            start_time=datetime.now(),
            start_station_id=0,
        )


# --------------------------
# is_active
# --------------------------

def test_is_active_before_end(create_valid_ride):
    assert create_valid_ride.is_active() is True


def test_is_active_after_end(create_valid_ride):
    create_valid_ride.end(end_station_id=3, end_time=datetime(2026, 1, 1, 12, 10, 0))
    assert create_valid_ride.is_active() is False


# --------------------------
# end()
# --------------------------

def test_end_happy_path(create_valid_ride):
    end_time = datetime(2026, 1, 1, 12, 10, 0)
    create_valid_ride.end(end_station_id=3, end_time=end_time)

    assert create_valid_ride.end_station_id == 3
    assert create_valid_ride.end_time == end_time
    assert create_valid_ride.is_active() is False


def test_end_sets_duration_correctly(create_valid_ride):
    end_time = datetime(2026, 1, 1, 12, 10, 0)
    create_valid_ride.end(end_station_id=3, end_time=end_time)

    assert create_valid_ride.duration_seconds() == 600


def test_cannot_end_twice(create_valid_ride):
    create_valid_ride.end(end_station_id=3, end_time=datetime(2026, 1, 1, 12, 5, 0))

    with pytest.raises(ValueError):
        create_valid_ride.end(end_station_id=4, end_time=datetime(2026, 1, 1, 12, 10, 0))


def test_end_station_must_be_positive(create_valid_ride):
    with pytest.raises(ValueError):
        create_valid_ride.end(end_station_id=0, end_time=datetime(2026, 1, 1, 12, 10, 0))


def test_end_time_must_be_after_start(create_valid_ride):
    with pytest.raises(ValueError):
        create_valid_ride.end(end_station_id=3, end_time=datetime(2026, 1, 1, 12, 0, 0))

    with pytest.raises(ValueError):
        create_valid_ride.end(end_station_id=3, end_time=create_valid_ride.start_time - timedelta(seconds=1))


# --------------------------
# duration_seconds
# --------------------------

def test_duration_raises_if_active(create_valid_ride):
    with pytest.raises(ValueError):
        create_valid_ride.duration_seconds()


def test_duration_returns_integer(create_valid_ride):
    create_valid_ride.end(3, create_valid_ride.start_time + timedelta(seconds=61))

    assert isinstance(create_valid_ride.duration_seconds(), int)
    assert create_valid_ride.duration_seconds() == 61


# --------------------------
# report_degraded
# --------------------------

def test_report_degraded_sets_flag(create_valid_ride):
    create_valid_ride.report_degraded()

    assert create_valid_ride.reported_degraded is True


def test_report_degraded_can_be_called_multiple_times(create_valid_ride):
    create_valid_ride.report_degraded()
    create_valid_ride.report_degraded()

    assert create_valid_ride.reported_degraded is True


# --------------------------
# Price field behavior
# --------------------------

def test_price_is_none_initially(create_valid_ride):
    assert create_valid_ride.price is None
