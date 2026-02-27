import pytest

from src.domain.VehicleContainer import DegradedRepo, Station, VehicleContainer

# =====================================================
# Fixtures
# =====================================================

@pytest.fixture
def empty_container():
    return VehicleContainer(1, set(), "Empty Container")

@pytest.fixture
def container_with_vehicle():
    return VehicleContainer(2, {"V1"}, "Container with Vehicle")

@pytest.fixture
def test_station():
    return Station(
        container_id=3,
        _vehicle_ids={"V1"},
        name="Test Station",
        lat=30.0,
        lon=40.0,
        max_capacity=5,
    )

@pytest.fixture
def test_degraded_repo():
    return DegradedRepo(
        container_id=4,
        _vehicle_ids={"V1"},
        name="Test Degraded Repo",
    )


# =====================================================
# VehicleContainer Tests
# =====================================================

def test_add_vehicle(empty_container):
    empty_container.add_vehicle("V1")

    assert empty_container.contains_vehicle("V1")
    assert empty_container.count() == 1


def test_add_duplicate_vehicle_does_not_duplicate(container_with_vehicle):

    container_with_vehicle.add_vehicle("V1")

    assert container_with_vehicle.count() == 1  # set prevents duplication


def test_remove_vehicle(container_with_vehicle):
    container_with_vehicle.remove_vehicle("V1")

    assert not container_with_vehicle.contains_vehicle("V1")
    assert container_with_vehicle.count() == 0


def test_remove_vehicle_raises_key_error_if_missing(empty_container):
    with pytest.raises(KeyError):
        empty_container.remove_vehicle("V999")


def test_contains_vehicle_true(container_with_vehicle):
    assert container_with_vehicle.contains_vehicle("V1") is True


def test_contains_vehicle_false(container_with_vehicle):
    assert container_with_vehicle.contains_vehicle("V2") is False


def test_get_vehicle_ids_returns_internal_set(container_with_vehicle):
    container_with_vehicle.add_vehicle("V2")

    ids = container_with_vehicle.get_vehicle_ids()

    assert ids == {"V1", "V2"}


def test_count_returns_correct_number(container_with_vehicle):
    container_with_vehicle.add_vehicle("V2")
    container_with_vehicle.add_vehicle("V3")

    assert container_with_vehicle.count() == 3


def test_initial_state_values():
    container = VehicleContainer(10, {"A"}, "Main")

    assert container.container_id == 10
    assert container.name == "Main"
    assert container.count() == 1


# =====================================================
# Station Tests
# =====================================================

def test_station_inherits_container_behavior(test_station):
    station = test_station

    station.add_vehicle("V2")

    assert station.count() == 2
    assert station.contains_vehicle("V2")


def test_station_has_free_slot_true(test_station):
    assert test_station.has_free_slot() is True



def test_station_has_free_slot_false_when_full():
    station = Station(
        container_id=1,
        _vehicle_ids={"V1", "V2"},
        name="Station A",
        lat=32.0,
        lon=34.0,
        max_capacity=2,
    )

    assert station.has_free_slot() is False


def test_station_capacity_edge_case_equal_capacity():
    station = Station(
        container_id=1,
        _vehicle_ids={"V1", "V2", "V3"},
        name="Station A",
        lat=32.0,
        lon=34.0,
        max_capacity=3,
    )

    assert station.has_free_slot() is False


def test_station_coordinates_and_capacity_stored_correctly():
    station = Station(
        container_id=99,
        _vehicle_ids=set(),
        name="Central",
        lat=12.5,
        lon=45.8,
        max_capacity=10,
    )

    assert station.lat == 12.5
    assert station.lon == 45.8
    assert station.max_capacity == 10


# =====================================================
# DegradedRepo Tests
# =====================================================

def test_degraded_repo_behaves_like_container(test_degraded_repo):

    test_degraded_repo.add_vehicle("V2")

    assert test_degraded_repo.contains_vehicle("V2")
    assert test_degraded_repo.count() == 2


def test_degraded_repo_remove_vehicle(test_degraded_repo):
    test_degraded_repo.remove_vehicle("V1")

    assert test_degraded_repo.count() == 0

def test_degraded_repo_metadata():
    repo = DegradedRepo(
        container_id=50,
        _vehicle_ids={"X"},
        name="Maintenance",
    )

    assert repo.container_id == 50
    assert repo.name == "Maintenance"
    assert repo.count() == 1
