from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from tests.conftest import auth_headers
from tests.test_phase_zero_workflow import create_vehicle_policy_claim


def phase_one_fixture_bytes() -> bytes:
    image = Image.new("RGB", (1000, 700), (224, 232, 238))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((230, 150, 770, 405), radius=42, fill=(20, 155, 105))
    draw.rounded_rectangle((110, 405, 890, 620), radius=35, fill=(25, 95, 210))
    draw.ellipse((315, 475, 455, 575), fill=(220, 35, 55))
    draw.line((540, 455, 745, 555), fill=(245, 125, 25), width=18)
    draw.line((430, 225, 565, 345), fill=(125, 45, 185), width=14)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def create_ready_inspection(client: TestClient, headers: dict[str, str]) -> str:
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
    assert inspection.status_code == 201
    inspection_id = inspection.json()["id"]
    upload = client.post(
        f"/api/v1/inspections/{inspection_id}/media",
        headers=headers,
        data={"viewpoint": "FRONT"},
        files={"file": ("phase-one-fixture.png", phase_one_fixture_bytes(), "image/png")},
    )
    assert upload.status_code == 201, upload.text
    submit = client.post(
        f"/api/v1/inspections/{inspection_id}/submit",
        headers={**headers, "Idempotency-Key": "phase-one-foundation"},
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == "READY"
    return inspection_id


def test_phase_one_analysis_artifacts_corrections_and_versions(client: TestClient, seeded_users):
    admin = auth_headers(client, "admin@test.local")
    inspection_id = create_ready_inspection(client, admin)
    started = client.post(
        f"/api/v1/inspections/{inspection_id}/analysis",
        headers={**admin, "Idempotency-Key": "phase-one-run-1"},
    )
    assert started.status_code == 202, started.text
    run_id = started.json()["run"]["id"]

    result = client.get(f"/api/v1/analysis/{run_id}", headers=admin)
    assert result.status_code == 200, result.text
    payload = result.json()
    assert payload["run"]["state"] == "SUCCEEDED"
    assert payload["run"]["version"] == 1
    assert {item["class_name"] for item in payload["parts"]} == {"HOOD", "FRONT_BUMPER"}
    assert {item["class_name"] for item in payload["damages"]} == {"CRACK", "DENT", "SCRATCH"}
    assert all(item["coverage"] is not None for item in payload["damages"])
    assert len(payload["models"]) == 2
    assert all(len(item["weights_checksum"]) == 64 for item in payload["models"])

    overlay = next(item for item in payload["artifacts"] if item["artifact_type"] == "COMBINED_OVERLAY")
    artifact = client.get(f"/api/v1/analysis/artifacts/{overlay['id']}", headers=admin)
    assert artifact.status_code == 200
    assert artifact.headers["content-type"] == "image/png"
    other = auth_headers(client, "other@test.local")
    assert client.get(f"/api/v1/analysis/{run_id}", headers=other).status_code == 404
    assert client.get(f"/api/v1/analysis/artifacts/{overlay['id']}", headers=other).status_code == 404

    finding = next(item for item in payload["damages"] if item["class_name"] == "DENT")
    correction = client.post(
        f"/api/v1/analysis/findings/DAMAGE/{finding['id']}/corrections",
        headers=admin,
        json={
            "action": "CORRECT",
            "corrected_class": "SCRATCH",
            "corrected_part_detection_id": finding["vehicle_part_detection_id"],
            "corrected_severity": "MINOR",
            "notes": "Synthetic reviewer correction for the fixed evaluation flow.",
        },
    )
    assert correction.status_code == 201, correction.text
    assert correction.json()["version"] == 1
    history = client.get(
        f"/api/v1/analysis/findings/DAMAGE/{finding['id']}/corrections", headers=admin
    )
    assert history.status_code == 200
    assert history.json()[0]["corrected_class"] == "SCRATCH"
    updated = client.get(f"/api/v1/analysis/{run_id}", headers=admin).json()
    assert next(item for item in updated["damages"] if item["id"] == finding["id"])["class_name"] == "DENT"
    assert updated["corrections"][0]["corrected_class"] == "SCRATCH"

    second = client.post(
        f"/api/v1/inspections/{inspection_id}/analysis",
        headers={**admin, "Idempotency-Key": "phase-one-run-2"},
    )
    assert second.status_code == 202
    assert second.json()["run"]["version"] == 2
    repeated = client.post(
        f"/api/v1/inspections/{inspection_id}/analysis",
        headers={**admin, "Idempotency-Key": "phase-one-run-2"},
    )
    assert repeated.status_code == 202
    assert repeated.json()["run"]["id"] == second.json()["run"]["id"]


def test_analysis_requires_ready_inspection_and_reviewer_role(client: TestClient, seeded_users):
    admin = auth_headers(client, "admin@test.local")
    vehicle, policy, claim = create_vehicle_policy_claim(client, admin)
    draft = client.post(
        "/api/v1/inspections",
        headers=admin,
        json={"vehicle_id": vehicle["id"], "policy_id": policy["id"], "claim_id": claim["id"], "type": "CLAIM"},
    ).json()
    assert client.post(f"/api/v1/inspections/{draft['id']}/analysis", headers=admin).status_code == 409

    upload = client.post(
        f"/api/v1/inspections/{draft['id']}/media",
        headers=admin,
        data={"viewpoint": "FRONT"},
        files={"file": ("phase-one-fixture.png", phase_one_fixture_bytes(), "image/png")},
    )
    assert upload.status_code == 201
    submit = client.post(
        f"/api/v1/inspections/{draft['id']}/submit",
        headers={**admin, "Idempotency-Key": "phase-one-role-foundation"},
    )
    assert submit.status_code == 200
    ready_id = draft["id"]
    claimant = auth_headers(client, "claimant@test.local")
    assert client.post(f"/api/v1/inspections/{ready_id}/analysis", headers=claimant).status_code == 403


def test_analysis_start_is_idempotent_while_run_is_queued(
    client: TestClient, seeded_users, monkeypatch
):
    admin = auth_headers(client, "admin@test.local")
    inspection_id = create_ready_inspection(client, admin)
    monkeypatch.setattr("app.modules.analysis.router.damage_analysis.delay", lambda _job_id: None)

    first = client.post(
        f"/api/v1/inspections/{inspection_id}/analysis",
        headers={**admin, "Idempotency-Key": "queued-analysis"},
    )
    repeated = client.post(
        f"/api/v1/inspections/{inspection_id}/analysis",
        headers={**admin, "Idempotency-Key": "queued-analysis"},
    )
    conflicting = client.post(
        f"/api/v1/inspections/{inspection_id}/analysis",
        headers={**admin, "Idempotency-Key": "different-analysis"},
    )

    assert first.status_code == 202
    assert repeated.status_code == 202
    assert repeated.json()["run"]["id"] == first.json()["run"]["id"]
    assert conflicting.status_code == 409
    assert conflicting.json()["detail"] == "An analysis run is already active"
