"""
Health check endpoint.

Not part of the proposal's API spec — added per docs/Implementation_Roadmap.md
Milestone 0 to verify deployment wiring. Classified as a pure engineering
Design Enhancement in docs/Proposal_vs_Engineering_Additions.md (no
proposal linkage). Deliberately kept outside the /api/v1 prefix since it is
infrastructure, not a versioned business resource (see NFR-005 scope note
in docs/Requirement_Analysis.md).
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db

logger = logging.getLogger("app.health")

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    database_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check database connectivity failed")
        database_status = "unreachable"

    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "environment": settings.environment,
        "database": database_status,
    }
