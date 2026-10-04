import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.auth.local import LocalPasswordAuthProvider
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import CurrentUser, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
_provider = LocalPasswordAuthProvider()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = _provider.authenticate(db, email=body.email, password=body.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Ongeldige inloggegevens")

    user.last_login_at = dt.datetime.now(dt.timezone.utc)
    db.commit()

    token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role.value,
        is_platform_admin=user.is_platform_admin,
    )
    return TokenResponse(access_token=token)


@router.post("/api-token", response_model=TokenResponse)
def create_api_token(current_user: CurrentUser = Depends(get_current_user)) -> TokenResponse:
    """A non-expiring token for scripts/API clients — requires an already-valid
    session (login first in the app, then generate this from the API info
    popup) rather than a password, and carries the same claims/permissions
    as a normal login token, just without an `exp`.
    """
    token = create_access_token(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        role=current_user.role.value,
        is_platform_admin=current_user.is_platform_admin,
        expires=False,
    )
    return TokenResponse(access_token=token)
