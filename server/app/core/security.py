"""Security dependencies for protected API routes."""

import secrets

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings
from app.core.dependencies import get_settings


def require_audit_api_key(
    x_audit_api_key: str | None = Header(default=None, alias="X-Audit-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    """Require the configured shared key before allowing audit access."""
    expected_key = settings.audit_api_key.strip()

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit access is not configured.",
        )

    if not x_audit_api_key or not secrets.compare_digest(
        x_audit_api_key, expected_key
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing audit API key.",
        )
