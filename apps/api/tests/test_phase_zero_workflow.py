from datetime import UTC, datetime
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from tests.conftest import auth_headers


def image_bytes(width: int = 800, height: int = 600) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(218, 232, 240)).save(buffer, format="JPEG")
    return buffer.getvalue()


def create_vehicle_policy_claim(client: TestClient, headers: dict[str, str]) -> tuple[dict, dict, dict]:
    vehicle = client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={
            "registration_number": "ICT-2046",
            "vin": "1HGBH41JXMN109186",
            "make": "Honda",
            "model": "Civic",
            "year": 2022,
            "color": "White",
        },
    )
    assert vehicle.status_code == 201, vehicle.text
    policy = client.post(
        "/api/v1/policies",
        headers=headers,
        json={
            "vehicle_id": vehicle.json()["id"],
            "policy_number": "POL-2046",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "status": "ACTIVE",
        },
    )
    assert policy.status_code == 201, policy.text
    claim = client.post(
        "/api/v1/claims",
        headers=headers,
        json={
            "policy_id": policy.json()["id"],
            "claim_number": "CLM-2046",
            "incident_date": datetime(2026, 8, 30, 12, 0, tzinfo=UTC).isoformat(),
            "incident_location": "Islamabad",
            "description": "The vehicle was struck while stopped at a traffic signal.",
            "status": "EVIDENCE_PENDING",
        },
    )
    assert claim.status_code == 201, claim.text
    return vehicle.json(), policy.json(), claim.json()


def test_complete_phase_zero_workflow(client: TestClient, seeded_users):
    headers = auth_headers(client, "admin@test.local")
    vehicle, policy, claim = create_vehicle_policy_claim(client, headers)

    inspection = client.post(
        "/api/v1/inspections",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "policy_id": policy["id"],
            "claim_id": claim["id"],
            "type": "CLAIM",
        },
    )
    assert inspection.status_code == 201, inspection.text

    media = client.post(
        f"/api/v1/inspections/{inspection.json()['id']}/media",
        headers=headers,
        data={"viewpoint": "FRONT_LEFT"},
        files={"file": ("vehicle.jpg", image_bytes(), "image/jpeg")},
    )
    assert media.status_code == 201, media.text
    assert media.json()["width"] == 800

    duplicate = client.post(
        f"/api/v1/inspections/{inspection.json()['id']}/media",
        headers=headers,
        data={"viewpoint": "FRONT_LEFT"},
        files={"file": ("same-image.jpg", image_bytes(), "image/jpeg")},
    )
    assert duplicate.status_code == 409

    other_headers = auth_headers(client, "other@test.local")
    private_media = client.get(f"/api/v1/media/{media.json()['id']}/download", headers=other_headers)
    assert private_media.status_code == 404

    submitted = client.post(
        f"/api/v1/inspections/{inspection.json()['id']}/submit",
        headers={**headers, "Idempotency-Key": "phase-zero-submit"},
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["status"] == "READY"
    assert submitted.json()["jobs"][0]["state"] == "SUCCEEDED"
    assert submitted.json()["jobs"][0]["result"]["media_count"] == 1

    repeated = client.post(
        f"/api/v1/inspections/{inspection.json()['id']}/submit",
        headers={**headers, "Idempotency-Key": "phase-zero-submit"},
    )
    assert repeated.status_code == 200
    assert len(repeated.json()["jobs"]) == 1

    replacement = client.post(
        f"/api/v1/inspections/{inspection.json()['id']}/media",
        headers=headers,
        data={"viewpoint": "REAR"},
        files={"file": ("replacement.jpg", image_bytes(), "image/jpeg")},
    )
    assert replacement.status_code == 409

    history = client.get(f"/api/v1/vehicles/{vehicle['id']}/history", headers=headers)
    assert history.status_code == 200
    assert history.json()["claims"][0]["claim_number"] == "CLM-2046"
    assert history.json()["inspections"][0]["status"] == "READY"


def test_upload_validation_and_empty_submission(client: TestClient, seeded_users):
    headers = auth_headers(client, "admin@test.local")
    vehicle, policy, _ = create_vehicle_policy_claim(client, headers)
    inspection = client.post(
        "/api/v1/inspections",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "policy_id": policy["id"],
            "type": "POLICY_INCEPTION",
        },
    ).json()
    empty = client.post(f"/api/v1/inspections/{inspection['id']}/submit", headers=headers)
    assert empty.status_code == 422

    too_small = client.post(
        f"/api/v1/inspections/{inspection['id']}/media",
        headers=headers,
        data={"viewpoint": "FRONT"},
        files={"file": ("small.jpg", image_bytes(100, 100), "image/jpeg")},
    )
    assert too_small.status_code == 422

    invalid = client.post(
        f"/api/v1/inspections/{inspection['id']}/media",
        headers=headers,
        data={"viewpoint": "FRONT"},
        files={"file": ("fake.jpg", b"not-an-image", "image/jpeg")},
    )
    assert invalid.status_code == 422

    oversized = client.post(
        f"/api/v1/inspections/{inspection['id']}/media",
        headers=headers,
        data={"viewpoint": "FRONT"},
        files={"file": ("oversized.jpg", b"0" * (15 * 1024 * 1024 + 1), "image/jpeg")},
    )
    assert oversized.status_code == 413
