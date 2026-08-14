import pytest
from fastapi.testclient import TestClient

from backend.config import AppSettings, CorsSettings
from backend.main import create_app


DEVELOPMENT_SETTINGS = AppSettings(
    environment="development",
    cors=CorsSettings(
        allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_local_network_origins=True,
    ),
)


def preflight(client: TestClient, origin: str):
    return client.options(
        "/api/sessions",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.100:3000",
        "http://10.186.74.121:3000",
        "http://172.20.10.5:3000",
    ],
)
def test_development_preflight_allows_configured_and_private_origins(origin):
    with TestClient(create_app(DEVELOPMENT_SETTINGS)) as client:
        response = preflight(client, origin)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize(
    "origin",
    [
        "http://example.com:3000",
        "http://172.15.10.5:3000",
        "http://172.32.10.5:3000",
        "http://192.169.1.5:3000",
        "https://192.168.1.5:3000",
        "http://192.168.1.5:3001",
    ],
)
def test_lan_regex_does_not_allow_public_wrong_scheme_or_wrong_port(origin):
    with TestClient(create_app(DEVELOPMENT_SETTINGS)) as client:
        response = preflight(client, origin)
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_production_does_not_automatically_allow_lan_origin():
    production = AppSettings(
        environment="production",
        cors=CorsSettings(
            allowed_origins=["https://coach.example.edu"],
            allow_local_network_origins=False,
        ),
    )
    with TestClient(create_app(production)) as client:
        response = preflight(client, "http://192.168.1.100:3000")
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_allowed_lan_origin_can_create_mock_guided_session():
    origin = "http://10.186.74.121:3000"
    with TestClient(create_app(DEVELOPMENT_SETTINGS)) as client:
        response = client.post(
            "/api/sessions",
            headers={"Origin": origin, "Content-Type": "application/json"},
            json={"mode": "guided", "case_code": "SAMPLE-CASE-01"},
        )
    assert response.status_code == 201
    assert response.headers["access-control-allow-origin"] == origin
    assert response.json()["active_skill"] == "five_forces"
