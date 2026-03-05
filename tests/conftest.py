from collections.abc import Iterator
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from src.api.dependencies import get_fleet_manager
from src.main import create_app


@pytest.fixture()
def fleet_manager_mock() -> Mock:
    fm = Mock()
    fm.register_user.return_value = 1
    fm.active_rides = Mock()
    fm.active_rides.active_user_ids.return_value = []
    return fm


@pytest.fixture()
def app(fleet_manager_mock: Mock) -> FastAPI:
    app = create_app()

    def override_get_fleet_manager(_: Request) -> Mock:
        return fleet_manager_mock

    app.dependency_overrides[get_fleet_manager] = override_get_fleet_manager
    return app


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
