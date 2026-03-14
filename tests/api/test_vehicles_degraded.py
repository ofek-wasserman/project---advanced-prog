from unittest.mock import Mock

from fastapi.testclient import TestClient

from src.domain.exceptions import ConflictError, NotFoundError


def test_report_vehicle_degraded_returns_ok(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    fleet_manager_mock.report_vehicle_degraded.return_value = None

    resp = client.post(
        "/vehicle/report-degraded",
        json={"user_id": 1, "vehicle_id": "V001"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"result": "ok"}


def test_report_vehicle_degraded_invalid_input_returns_400(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    resp = client.post(
        "/vehicle/report-degraded",
        json={"user_id": "1", "vehicle_id": "V001"},
    )

    assert resp.status_code == 400


def test_report_vehicle_degraded_missing_entity_returns_404(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    fleet_manager_mock.report_vehicle_degraded.side_effect = NotFoundError("Vehicle not found")

    resp = client.post(
        "/vehicle/report-degraded",
        json={"user_id": 1, "vehicle_id": "MISSING"},
    )

    assert resp.status_code == 404
    assert resp.json() == {"detail": "Vehicle not found"}


def test_report_vehicle_degraded_conflicting_state_returns_409(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    fleet_manager_mock.report_vehicle_degraded.side_effect = ConflictError(
        "Vehicle already degraded"
    )

    resp = client.post(
        "/vehicle/report-degraded",
        json={"user_id": 1, "vehicle_id": "V001"},
    )

    assert resp.status_code == 409
    assert resp.json() == {"detail": "Vehicle already degraded"}
