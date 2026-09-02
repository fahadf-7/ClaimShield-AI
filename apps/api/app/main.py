from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.modules.auth.router import router as auth_router
from app.modules.claims.router import router as claims_router
from app.modules.inspections.router import router as inspections_router
from app.modules.jobs.router import router as jobs_router
from app.modules.media.router import router as media_router
from app.modules.policies.router import router as policies_router
from app.modules.reviews.router import router as reviews_router
from app.modules.vehicles.router import router as vehicles_router

app = FastAPI(
    title="ClaimShield AI API",
    version="0.1.0",
    description="Phase 0 foundation API. No AI claim conclusions are produced.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "0", "service": settings.app_name}


@app.get("/ready", tags=["system"])
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        if not settings.celery_task_always_eager:
            Redis.from_url(settings.redis_url, socket_connect_timeout=2).ping()
        return {"status": "ready", "database": "ok", "queue": "eager" if settings.celery_task_always_eager else "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="A required service is unavailable") from exc


for router in (
    auth_router,
    vehicles_router,
    policies_router,
    claims_router,
    inspections_router,
    media_router,
    jobs_router,
    reviews_router,
):
    app.include_router(router, prefix="/api/v1")
