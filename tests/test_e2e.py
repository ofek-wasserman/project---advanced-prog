
from fastapi.testclient import TestClient

from src.main import app


def test_phase1_user_flow():
    """
    Phase 1 end-to-end integration test.

    Flow:
    Register user → Start ride → End ride
    """

    # Use context manager so FastAPI startup events run
    with TestClient(app) as client:

        # -------------------------
        # 1. Register User
        # -------------------------
        register_response = client.post(
            "/register",
            json={
                "payment_token": "test_token_123"
            }
        )

        assert register_response.status_code == 201

        register_data = register_response.json()
        assert "user_id" in register_data

        user_id = register_data["user_id"]

        # -------------------------
        # 2. Start Ride
        # -------------------------
        start_response = client.post(
            "/ride/start",
            json={
                "user_id": user_id,
                "lat": 32.0853,
                "lon": 34.7818
            }
        )

        assert start_response.status_code == 200

        start_data = start_response.json()

        assert "ride_id" in start_data
        assert "vehicle_id" in start_data
        assert "vehicle_type" in start_data
        assert "start_station_id" in start_data

        ride_id = start_data["ride_id"]

        # -------------------------
        # 3. End Ride
        # -------------------------
        end_response = client.post(
            "/ride/end",
            json={
                "ride_id": ride_id,
                "lat": 32.0853,
                "lon": 34.7818
            }
        )

        assert end_response.status_code == 200

        end_data = end_response.json()

        assert "payment_charged" in end_data
        assert "end_station_id" in end_data

        # -------------------------
        # 4. Price Validation
        # -------------------------
        assert end_data["payment_charged"] == 15.0
