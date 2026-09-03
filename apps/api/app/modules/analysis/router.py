from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.common import new_id
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import AnalysisState, DamageSeverity, FindingType, JobState, Role
from app.modules.analysis.models import (
    AnalysisRun,
    DamageDetection,
    DerivedArtifact,
    FindingCorrection,
    ModelVersion,
    VehiclePartDetection,
)
from app.modules.analysis.schemas import (
    AnalysisResultRead,
    AnalysisRunSummary,
    AnalysisStartRead,
    ArtifactRead,
    DamageDetectionRead,
    FindingCorrectionCreate,
    FindingCorrectionRead,
    ModelVersionRead,
    PartDetectionRead,
)
from app.modules.analysis.taxonomy import DAMAGE_TAXONOMY, PART_TAXONOMY
from app.modules.auth.models import User
from app.modules.inspections.router import scoped_inspection
from app.modules.jobs.models import AnalysisJob
from app.modules.media.models import Media
from app.storage import get_storage
from app.worker import damage_analysis

router = APIRouter(tags=["analysis"])


def scoped_run(db: Session, run_id: str, organization_id: str) -> AnalysisRun:
    run = db.scalar(
        select(AnalysisRun).where(
            AnalysisRun.id == run_id,
            AnalysisRun.organization_id == organization_id,
        )
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return run


@router.post(
    "/inspections/{inspection_id}/analysis",
    response_model=AnalysisStartRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_analysis(
    inspection_id: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN.value, Role.REVIEWER.value)),
) -> AnalysisStartRead:
    inspection = scoped_inspection(db, inspection_id, user.organization_id)
    if inspection.status != "READY":
        raise HTTPException(status_code=409, detail="Inspection must be READY before analysis")
    request_key = idempotency_key or f"analysis:{inspection.id}:{uuid4()}"
    existing_job = db.scalar(
        select(AnalysisJob).where(
            AnalysisJob.organization_id == user.organization_id,
            AnalysisJob.inspection_id == inspection.id,
            AnalysisJob.idempotency_key == request_key,
        )
    )
    if existing_job is not None:
        existing_run = db.scalar(select(AnalysisRun).where(AnalysisRun.job_id == existing_job.id))
        if existing_run is None:
            raise HTTPException(status_code=409, detail="Analysis request is not available")
        return AnalysisStartRead(run=AnalysisRunSummary.model_validate(existing_run), job_id=existing_job.id)
    active = db.scalar(
        select(AnalysisRun).where(
            AnalysisRun.inspection_id == inspection.id,
            AnalysisRun.organization_id == user.organization_id,
            AnalysisRun.state.in_([AnalysisState.QUEUED.value, AnalysisState.RUNNING.value]),
        )
    )
    if active is not None:
        raise HTTPException(status_code=409, detail="An analysis run is already active")
    version = (
        int(
            db.scalar(
                select(func.coalesce(func.max(AnalysisRun.version), 0)).where(
                    AnalysisRun.inspection_id == inspection.id,
                    AnalysisRun.organization_id == user.organization_id,
                )
            )
            or 0
        )
        + 1
    )
    job = AnalysisJob(
        id=new_id(),
        organization_id=user.organization_id,
        inspection_id=inspection.id,
        claim_id=inspection.claim_id,
        type="DAMAGE_ANALYSIS",
        state=JobState.QUEUED.value,
        correlation_id=str(uuid4()),
        idempotency_key=request_key,
    )
    db.add(job)
    db.flush()
    run = AnalysisRun(
        id=new_id(),
        organization_id=user.organization_id,
        inspection_id=inspection.id,
        job_id=job.id,
        version=version,
        state=AnalysisState.QUEUED.value,
        pipeline_version=settings.analysis_pipeline_version,
        threshold_version=settings.analysis_threshold_version,
    )
    db.add(run)
    record_audit(
        db,
        user,
        "DAMAGE_ANALYSIS_STARTED",
        "analysis_run",
        run.id,
        {"inspection_id": inspection.id, "version": version},
    )
    db.commit()
    damage_analysis.delay(job.id)
    db.expire_all()
    return AnalysisStartRead(run=AnalysisRunSummary.model_validate(run), job_id=job.id)


@router.get(
    "/inspections/{inspection_id}/analysis",
    response_model=list[AnalysisRunSummary],
)
def list_analysis_runs(
    inspection_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AnalysisRun]:
    scoped_inspection(db, inspection_id, user.organization_id)
    return list(
        db.scalars(
            select(AnalysisRun)
            .where(
                AnalysisRun.inspection_id == inspection_id,
                AnalysisRun.organization_id == user.organization_id,
            )
            .order_by(AnalysisRun.version.desc())
        )
    )


@router.get("/analysis/{run_id}", response_model=AnalysisResultRead)
def get_analysis_result(
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisResultRead:
    run = scoped_run(db, run_id, user.organization_id)
    parts = list(
        db.scalars(
            select(VehiclePartDetection).where(
                VehiclePartDetection.analysis_run_id == run.id,
                VehiclePartDetection.organization_id == user.organization_id,
            )
        )
    )
    damages = list(
        db.scalars(
            select(DamageDetection).where(
                DamageDetection.analysis_run_id == run.id,
                DamageDetection.organization_id == user.organization_id,
            )
        )
    )
    artifacts = list(
        db.scalars(
            select(DerivedArtifact).where(
                DerivedArtifact.analysis_run_id == run.id,
                DerivedArtifact.organization_id == user.organization_id,
            )
        )
    )
    corrections = list(
        db.scalars(
            select(FindingCorrection)
            .where(
                FindingCorrection.analysis_run_id == run.id,
                FindingCorrection.organization_id == user.organization_id,
            )
            .order_by(FindingCorrection.created_at)
        )
    )
    model_ids = {item for item in (run.part_model_version_id, run.damage_model_version_id) if item}
    models = list(db.scalars(select(ModelVersion).where(ModelVersion.id.in_(model_ids)))) if model_ids else []
    media_ids = (
        {item.media_id for item in artifacts} | {item.media_id for item in parts} | {item.media_id for item in damages}
    )
    media_items = (
        list(
            db.scalars(
                select(Media).where(
                    Media.id.in_(media_ids),
                    Media.organization_id == user.organization_id,
                )
            )
        )
        if media_ids
        else []
    )
    return AnalysisResultRead(
        run=AnalysisRunSummary.model_validate(run),
        models=[ModelVersionRead.model_validate(item) for item in models],
        artifacts=[ArtifactRead.model_validate(item) for item in artifacts],
        parts=[PartDetectionRead.model_validate(item) for item in parts],
        damages=[DamageDetectionRead.model_validate(item) for item in damages],
        corrections=[FindingCorrectionRead.model_validate(item) for item in corrections],
        media=[
            {
                "id": item.id,
                "filename": item.original_filename,
                "viewpoint": item.viewpoint,
                "width": item.width,
                "height": item.height,
                "original_url": f"/media/{item.id}/content",
            }
            for item in media_items
        ],
        taxonomy={"parts": list(PART_TAXONOMY), "damages": list(DAMAGE_TAXONOMY)},
    )


@router.get("/analysis/artifacts/{artifact_id}")
def get_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    artifact = db.scalar(
        select(DerivedArtifact).where(
            DerivedArtifact.id == artifact_id,
            DerivedArtifact.organization_id == user.organization_id,
        )
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return Response(
        content=get_storage().get(artifact.object_key),
        media_type=artifact.content_type,
        headers={"Cache-Control": "private, max-age=300"},
    )


def _scoped_finding(
    db: Session,
    finding_type: str,
    finding_id: str,
    organization_id: str,
) -> VehiclePartDetection | DamageDetection:
    model = VehiclePartDetection if finding_type == FindingType.PART.value else DamageDetection
    finding = db.scalar(select(model).where(model.id == finding_id, model.organization_id == organization_id))
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.post(
    "/analysis/findings/{finding_type}/{finding_id}/corrections",
    response_model=FindingCorrectionRead,
    status_code=status.HTTP_201_CREATED,
)
def correct_finding(
    finding_type: FindingType,
    finding_id: str,
    payload: FindingCorrectionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN.value, Role.REVIEWER.value)),
) -> FindingCorrection:
    finding = _scoped_finding(db, finding_type.value, finding_id, user.organization_id)
    if payload.corrected_class:
        taxonomy = PART_TAXONOMY if finding_type == FindingType.PART else DAMAGE_TAXONOMY
        if payload.corrected_class not in taxonomy:
            raise HTTPException(status_code=422, detail="Corrected class is outside the taxonomy")
    if payload.corrected_severity and payload.corrected_severity not in {item.value for item in DamageSeverity}:
        raise HTTPException(status_code=422, detail="Invalid corrected severity")
    if finding_type == FindingType.PART and (payload.corrected_part_detection_id or payload.corrected_severity):
        raise HTTPException(status_code=422, detail="Part findings cannot change part assignment or severity")
    if payload.corrected_part_detection_id:
        part = _scoped_finding(db, FindingType.PART.value, payload.corrected_part_detection_id, user.organization_id)
        if part.analysis_run_id != finding.analysis_run_id or part.media_id != finding.media_id:
            raise HTTPException(status_code=422, detail="Corrected part must belong to the same run and image")
    version = (
        int(
            db.scalar(
                select(func.coalesce(func.max(FindingCorrection.version), 0)).where(
                    FindingCorrection.finding_type == finding_type.value,
                    FindingCorrection.finding_id == finding.id,
                    FindingCorrection.organization_id == user.organization_id,
                )
            )
            or 0
        )
        + 1
    )
    correction = FindingCorrection(
        id=new_id(),
        organization_id=user.organization_id,
        analysis_run_id=finding.analysis_run_id,
        finding_type=finding_type.value,
        finding_id=finding.id,
        reviewer_id=user.id,
        action=payload.action,
        corrected_class=payload.corrected_class,
        corrected_part_detection_id=payload.corrected_part_detection_id,
        corrected_severity=payload.corrected_severity,
        notes=payload.notes.strip(),
        version=version,
    )
    db.add(correction)
    record_audit(
        db,
        user,
        "ANALYSIS_FINDING_REVIEWED",
        "finding_correction",
        correction.id,
        {"finding_type": finding_type.value, "finding_id": finding.id, "action": payload.action},
    )
    db.commit()
    db.refresh(correction)
    return correction


@router.get(
    "/analysis/findings/{finding_type}/{finding_id}/corrections",
    response_model=list[FindingCorrectionRead],
)
def correction_history(
    finding_type: FindingType,
    finding_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[FindingCorrection]:
    _scoped_finding(db, finding_type.value, finding_id, user.organization_id)
    return list(
        db.scalars(
            select(FindingCorrection)
            .where(
                FindingCorrection.finding_type == finding_type.value,
                FindingCorrection.finding_id == finding_id,
                FindingCorrection.organization_id == user.organization_id,
            )
            .order_by(FindingCorrection.version)
        )
    )
