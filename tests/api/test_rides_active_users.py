from unittest.mock import Mock

from fastapi.testclient import TestClient


def test_active_users_returns_empty_list(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    fleet_manager_mock.active_user_ids.return_value = []

    resp = client.get("/rides/active-users")

    assert resp.status_code == 200
    assert resp.json() == {"active_user_ids": []}


def test_active_users_returns_active_user_ids(
    client: TestClient,
    fleet_manager_mock: Mock,
) -> None:
    fleet_manager_mock.active_user_ids.return_value = [1, 2]

    resp = client.get("/rides/active-users")

    assert resp.status_code == 200
    assert resp.json() == {"active_user_ids": [1, 2]}
