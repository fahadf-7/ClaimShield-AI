import hashlib
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.common import new_id
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.enums import InspectionStatus
from app.modules.auth.models import User
from app.modules.inspections.router import scoped_inspection
from app.modules.media.models import Media
from app.modules.media.schemas import MediaRead
from app.storage import get_storage

router = APIRouter(tags=["media"])
ALLOWED_FORMATS = {"JPEG": ("image/jpeg", "jpg"), "PNG": ("image/png", "png"), "WEBP": ("image/webp", "webp")}


def scoped_media(db: Session, media_id: str, organization_id: str) -> Media:
    item = db.scalar(select(Media).where(Media.id == media_id, Media.organization_id == organization_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return item


@router.post("/inspections/{inspection_id}/media", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
async def upload_media(
    inspection_id: str,
    viewpoint: str = Form(default="UNKNOWN"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Media:
    inspection = scoped_inspection(db, inspection_id, user.organization_id)
    if inspection.status != InspectionStatus.DRAFT.value:
        raise HTTPException(status_code=409, detail="Submitted inspection evidence is immutable")
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Image exceeds the upload size limit")
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        with Image.open(BytesIO(data)) as image:
            detected_format = image.format or ""
            width, height = image.size
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=422, detail="File is not a valid supported image") from exc
    if detected_format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=422, detail="Only JPEG, PNG, and WebP images are supported")
    if width < settings.min_image_width or height < settings.min_image_height:
        raise HTTPException(
            status_code=422,
            detail=f"Image must be at least {settings.min_image_width}×{settings.min_image_height}px",
        )
    media_type, extension = ALLOWED_FORMATS[detected_format]
    digest = hashlib.sha256(data).hexdigest()
    object_key = f"{user.organization_id}/{inspection.id}/originals/{uuid4()}.{extension}"
    item = Media(
        id=new_id(),
        organization_id=user.organization_id,
        inspection_id=inspection.id,
        object_key=object_key,
        original_filename=Path(file.filename or "upload").name[:255],
        media_type=media_type,
        size_bytes=len(data),
        width=width,
        height=height,
        viewpoint=viewpoint.strip().upper()[:40] or "UNKNOWN",
        sha256=digest,
        metadata_json={"detected_format": detected_format},
    )
    storage = get_storage()
    try:
        storage.put(object_key, data, media_type)
        db.add(item)
        record_audit(db, user, "MEDIA_UPLOADED", "media", item.id, {"inspection_id": inspection.id})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        storage.delete(object_key)
        raise HTTPException(status_code=409, detail="This exact image already exists in the inspection") from exc
    except Exception:
        db.rollback()
        storage.delete(object_key)
        raise
    db.refresh(item)
    return item


@router.get("/media/{media_id}", response_model=MediaRead)
def get_media(
    media_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Media:
    return scoped_media(db, media_id, user.organization_id)


@router.get("/media/{media_id}/download")
def download_media(
    media_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    item = scoped_media(db, media_id, user.organization_id)
    data = get_storage().get(item.object_key)
    safe_name = item.original_filename.replace('"', "")
    return Response(
        content=data,
        media_type=item.media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.get("/media/{media_id}/content")
def view_media(
    media_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    item = scoped_media(db, media_id, user.organization_id)
    return Response(
        content=get_storage().get(item.object_key),
        media_type=item.media_type,
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft_media(
    media_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    item = scoped_media(db, media_id, user.organization_id)
    inspection = scoped_inspection(db, item.inspection_id, user.organization_id)
    if inspection.status != InspectionStatus.DRAFT.value:
        raise HTTPException(status_code=409, detail="Submitted evidence cannot be deleted")
    get_storage().delete(item.object_key)
    record_audit(db, user, "MEDIA_DELETED", "media", item.id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
