from unittest.mock import Mock

from starlette.testclient import TestClient


def test_register_returns_200_and_user_id(client: TestClient, fleet_manager_mock: Mock) -> None:
    resp = client.post("/register", json={"payment_token": "tok_123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "user_id" in body
    assert isinstance(body["user_id"], int)

    # your endpoint calls register_user(req.payment_token) positionally
    fleet_manager_mock.register_user.assert_called_once_with("tok_123")


def test_register_strict_types_rejects_non_string_token(client: TestClient, fleet_manager_mock: Mock) -> None:
    resp = client.post("/register", json={"payment_token": 123})
    assert resp.status_code == 400
    fleet_manager_mock.register_user.assert_not_called()


def test_register_extra_fields_forbidden(client: TestClient, fleet_manager_mock: Mock) -> None:
    resp = client.post("/register", json={"payment_token": "tok", "extra": "nope"})
    assert resp.status_code == 400
    fleet_manager_mock.register_user.assert_not_called()


def test_register_missing_payment_token_returns_400(client: TestClient, fleet_manager_mock: Mock) -> None:
    resp = client.post("/register", json={})
    assert resp.status_code == 400
    fleet_manager_mock.register_user.assert_not_called()


def test_register_duplicate_token_returns_400(client: TestClient, fleet_manager_mock: Mock) -> None:
    fleet_manager_mock.register_user.side_effect = [1, ValueError("duplicate token")]
    try:
        r1 = client.post("/register", json={"payment_token": "dup"})
        assert r1.status_code == 200

        r2 = client.post("/register", json={"payment_token": "dup"})
        assert r2.status_code == 400
    finally:
        fleet_manager_mock.register_user.side_effect = None
