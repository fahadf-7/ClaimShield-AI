from datetime import UTC, date, datetime

from sqlalchemy import select

from app.database import SessionLocal
from app.enums import ClaimStatus, OrganizationType, PolicyStatus, Role
from app.modules.auth.models import User
from app.modules.claims.models import Claim
from app.modules.organizations.models import Organization
from app.modules.policies.models import Policy
from app.modules.vehicles.models import Vehicle
from app.security import hash_password


def seed() -> None:
    db = SessionLocal()
    try:
        organization = db.scalar(select(Organization).where(Organization.name == "ClaimShield Demo Insurance"))
        if organization is None:
            organization = Organization(name="ClaimShield Demo Insurance", type=OrganizationType.INSURER.value)
            db.add(organization)
            db.flush()

        for name, email, role in (
            ("Amina Khan", "admin@claimshield.local", Role.ADMIN.value),
            ("Omar Siddiqui", "reviewer@claimshield.local", Role.REVIEWER.value),
            ("Sara Ahmed", "claimant@claimshield.local", Role.CLAIMANT.value),
        ):
            if db.scalar(select(User).where(User.email == email)) is None:
                db.add(
                    User(
                        organization_id=organization.id,
                        name=name,
                        email=email,
                        password_hash=hash_password("ClaimShield123!"),
                        role=role,
                    )
                )
        db.flush()

        vehicle = db.scalar(
            select(Vehicle).where(
                Vehicle.organization_id == organization.id,
                Vehicle.registration_number == "ICT-2046",
            )
        )
        if vehicle is None:
            vehicle = Vehicle(
                organization_id=organization.id,
                registration_number="ICT-2046",
                vin="1HGBH41JXMN109186",
                make="Honda",
                model="Civic",
                year=2022,
                color="Platinum White",
            )
            db.add(vehicle)
            db.flush()

        policy = db.scalar(
            select(Policy).where(
                Policy.organization_id == organization.id,
                Policy.policy_number == "POL-DEMO-2046",
            )
        )
        if policy is None:
            policy = Policy(
                organization_id=organization.id,
                vehicle_id=vehicle.id,
                policy_number="POL-DEMO-2046",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                status=PolicyStatus.ACTIVE.value,
            )
            db.add(policy)
            db.flush()

        if db.scalar(select(Claim).where(Claim.claim_number == "CLM-DEMO-1001")) is None:
            db.add(
                Claim(
                    organization_id=organization.id,
                    policy_id=policy.id,
                    claim_number="CLM-DEMO-1001",
                    incident_date=datetime(2026, 8, 28, 10, 30, tzinfo=UTC),
                    incident_location="Islamabad",
                    description="The vehicle was struck at low speed while waiting at a traffic signal.",
                    status=ClaimStatus.EVIDENCE_PENDING.value,
                )
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
