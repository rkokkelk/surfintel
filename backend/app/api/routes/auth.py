import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.schemas.auth import CurrentUser, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def login_oauth2(request: Request) -> RedirectResponse:
    oauth = security.get_oauth()
    redirect_uri = str(request.url_for("auth"))
    return await oauth.idp.authorize_redirect(request, redirect_uri)

@router.post("/login", response_model=TokenResponse)
def login_pw(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = security.pw_authenticate(db, email=body.email, password=body.password)

    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Ongeldige inloggegevens")

    user.last_login_at = dt.datetime.now(dt.UTC)
    db.commit()

    token = security.create_access_token(user=user)
    return TokenResponse(access_token=token)


@router.get("/authorize")
async def auth(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    """OAuth2 callback endpoint. After successful authentication with the provider,
    this creates a JWT access token and redirects to the frontend callback URL
    with the token in the URL hash fragment (for SPA security).
    """
    oauth = security.get_oauth()
    token = await oauth.idp.authorize_access_token(request)

    user_info = token.get("userinfo", {})
    current_user = security.user_upsert(db, user_info)
    access_token = security.create_access_token(user=current_user)

    # TODO: whether returning a JWT toket in a GET request is not the best way to do this
    return RedirectResponse(url=f"{settings.cors_origins[0]}/auth/callback#access_token={access_token}")


@router.post("/api-token", response_model=TokenResponse)
def create_api_token(current_user: CurrentUser = Depends(get_current_user)) -> TokenResponse:
    """A non-expiring token for scripts/API clients — requires an already-valid
    session (login first in the app, then generate this from the API info
    popup) rather than a password, and carries the same claims/permissions
    as a normal login token, just without an `exp`.
    """
    token = security.create_access_token(user=current_user, expires=False)
    return TokenResponse(access_token=token)
