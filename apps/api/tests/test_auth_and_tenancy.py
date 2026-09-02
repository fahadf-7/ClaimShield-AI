from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_login_and_current_user(client: TestClient, seeded_users):
    headers = auth_headers(client, "admin@test.local")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"


def test_health_and_readiness(client: TestClient, seeded_users):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").json()["status"] == "ready"


def test_invalid_login_is_rejected(client: TestClient, seeded_users):
    response = client.post(
        "/api/v1/auth/login", json={"email": "admin@test.local", "password": "incorrect"}
    )
    assert response.status_code == 401


def test_claimant_cannot_create_vehicle(client: TestClient, seeded_users):
    headers = auth_headers(client, "claimant@test.local")
    response = client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={
            "registration_number": "ABC-123",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "color": "White",
        },
    )
    assert response.status_code == 403


def test_vehicle_is_hidden_from_other_organization(client: TestClient, seeded_users):
    admin = auth_headers(client, "admin@test.local")
    other = auth_headers(client, "other@test.local")
    created = client.post(
        "/api/v1/vehicles",
        headers=admin,
        json={
            "registration_number": "ICT-123",
            "make": "Honda",
            "model": "Civic",
            "year": 2021,
            "color": "Blue",
        },
    )
    assert created.status_code == 201
    response = client.get(f"/api/v1/vehicles/{created.json()['id']}", headers=other)
    assert response.status_code == 404
