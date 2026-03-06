from unittest.mock import Mock

from fastapi.testclient import TestClient


def test_nearest_station_returns_station(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    station = Mock()
    station.container_id = 7
    station.lat = 32.1
    station.lon = 34.8

    fleet_manager_mock.nearest_station_with_available_vehicle.return_value = station

    resp = client.get("/stations/nearest?lat=32.1&lon=34.8")

    assert resp.status_code == 200
    assert resp.json() == {
        "station_id": 7,
        "lat": 32.1,
        "lon": 34.8,
    }
    fleet_manager_mock.nearest_station_with_available_vehicle.assert_called_once_with((32.1, 34.8))


def test_nearest_station_returns_404_when_none_available(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    fleet_manager_mock.nearest_station_with_available_vehicle.return_value = None

    resp = client.get("/stations/nearest?lat=32.1&lon=34.8")

    assert resp.status_code == 404
    assert resp.json() == {"detail": "No station with available vehicle found."}
    fleet_manager_mock.nearest_station_with_available_vehicle.assert_called_once_with((32.1, 34.8))
