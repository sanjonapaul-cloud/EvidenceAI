"""Audit trail API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.audit.store import AuditStore
from app.core.dependencies import get_audit_store
from app.core.security import require_audit_api_key

router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
    dependencies=[Depends(require_audit_api_key)],
)


@router.get("/events")
def list_audit_events(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    event_type: str | None = Query(default=None, min_length=1),
    audit_store: AuditStore = Depends(get_audit_store),
):
    """Return paginated audit events without sensitive content."""
    try:
        return audit_store.list_events(
            limit=limit,
            offset=offset,
            event_type=event_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc