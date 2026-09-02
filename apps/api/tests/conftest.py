import os
import shutil
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_claimshield.db"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["LOCAL_STORAGE_PATH"] = "./test-storage"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-thirty-two-characters"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.modules.auth.models import User
from app.modules.organizations.models import Organization
from app.security import hash_password


@pytest.fixture(scope="session", autouse=True)
def database_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    Path("test_claimshield.db").unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def clean_data():
    with SessionLocal() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    yield
    shutil.rmtree("test-storage", ignore_errors=True)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def seeded_users():
    with SessionLocal() as db:
        org = Organization(name="Test Insurer", type="INSURER")
        other_org = Organization(name="Other Insurer", type="INSURER")
        db.add_all([org, other_org])
        db.flush()
        users = {
            "admin": User(
                organization_id=org.id,
                name="Admin User",
                email="admin@test.local",
                password_hash=hash_password("Password123!"),
                role="ADMIN",
            ),
            "reviewer": User(
                organization_id=org.id,
                name="Reviewer User",
                email="reviewer@test.local",
                password_hash=hash_password("Password123!"),
                role="REVIEWER",
            ),
            "claimant": User(
                organization_id=org.id,
                name="Claimant User",
                email="claimant@test.local",
                password_hash=hash_password("Password123!"),
                role="CLAIMANT",
            ),
            "other": User(
                organization_id=other_org.id,
                name="Other Admin",
                email="other@test.local",
                password_hash=hash_password("Password123!"),
                role="ADMIN",
            ),
        }
        db.add_all(users.values())
        db.commit()
        return {key: user.id for key, user in users.items()}


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Password123!"}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
