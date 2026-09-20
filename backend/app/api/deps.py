"""Authentication and tenant-scoping dependencies.

Tenant isolation is enforced at the application layer (an MVP choice over
Postgres row-level-security): every query against an organization-owned
table MUST go through `scoped_to_org` below rather than filtering by
organization_id ad hoc in each route — that is the one place a missing
filter would be caught in review.
"""

from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.schemas.auth import CurrentUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Ongeldig of verlopen token"
        ) from exc

    return CurrentUser(
        id=uuid.UUID(payload["sub"]),
        organization_id=uuid.UUID(payload["org_id"]),
        role=payload["role"],
        is_platform_admin=payload["is_platform_admin"],
    )


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != "admin" and not current_user.is_platform_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Alleen beheerders mogen dit.")
    return current_user


def require_platform_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not current_user.is_platform_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Alleen platformbeheerders mogen dit.")
    return current_user


def scoped_to_org(query: Select, model, current_user: CurrentUser) -> Select:
    """Add the organization_id filter every query against an org-owned table
    must have. Platform admins do not bypass this here — a platform-wide view
    is a deliberate, separate route (see routes/organizations.py), never an
    implicit side effect of a flag.
    """
    return query.where(model.organization_id == current_user.organization_id)


def get_session(db: Session = Depends(get_db)) -> Session:
    return db
