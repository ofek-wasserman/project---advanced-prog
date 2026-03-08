from unittest.mock import Mock

from fastapi.testclient import TestClient

from src.domain.exceptions import ConflictError, InvalidInputError, NotFoundError


def test_register_user_returns_400_for_invalid_input(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    fleet_manager_mock.register_user.side_effect = InvalidInputError(
        "Invalid payment token."
    )

    resp = client.post("/register", json={"payment_token": "tok_123"})

    assert resp.status_code == 400
    assert resp.json() == {"detail": "Invalid payment token."}


def test_register_user_returns_409_for_conflict(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    fleet_manager_mock.register_user.side_effect = ConflictError(
        "Payment token already registered."
    )

    resp = client.post("/register", json={"payment_token": "tok_123"})

    assert resp.status_code == 409
    assert resp.json() == {"detail": "Payment token already registered."}


def test_nearest_station_returns_404_for_not_found(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    fleet_manager_mock.nearest_station_with_available_vehicle.side_effect = NotFoundError(
        "No station with available vehicle found."
    )

    resp = client.get("/stations/nearest?lat=32.1&lon=34.8")

    assert resp.status_code == 404
    assert resp.json() == {"detail": "No station with available vehicle found."}
