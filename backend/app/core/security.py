from __future__ import annotations

import datetime as dt

import bcrypt
import jwt
from authlib.integrations.starlette_client import OAuth
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Organization
from app.models.user import AppUser, UserRole
from app.schemas.auth import CurrentUser

oauth: OAuth = None


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


def create_access_token(user: CurrentUser, expires: bool=True) -> str:
    """`expires=False` omits the `exp` claim entirely for a long-lived API
    token — PyJWT's decode() only enforces expiry when `exp` is present, so
    leaving it out (not setting it far in the future) is what makes the
    token genuinely non-expiring rather than expiring in, say, 100 years.
    """
    now = dt.datetime.now(dt.UTC)
    payload = {
        "sub": str(user.id),
        "org_id": str(user.organization_id),
        "role": user.role.value,
        "is_platform_admin": user.is_platform_admin,
        "iat": now,
    }

    if expires:
        payload["exp"] = now + dt.timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

def oauth_enabled() -> bool:
    """ Determine whether OIDC OAUTH2 has been configured
    
    :return: Whether Oauth2 has been configured
    """
    return bool(settings.oidc_issuer)

def get_oauth() -> OAuth:
    """ Get Oauth object

    :return Oauth: object
    """
    global oauth

    if oauth:  # Singleton
        return oauth

    oauth = OAuth()
    oauth.register(
        name="idp",
        server_metadata_url=settings.oidc_issuer,
        client_id=settings.oidc_client_id,
        client_secret=settings.oidc_client_secret,
        client_kwargs={"scope": settings.oidc_scope, "code_challenge_method": "S256"},
    )

    return oauth
    
def pw_authenticate(db: Session, email: str, password: str) -> AppUser | None:
    """ Authenticate a user
    
    :param db: Database session
    :param email: Email of user
    :param password: Password of user
    :return: AppUser or None if non existent or invalid authentication"""
    user = db.scalar(select(AppUser).where(AppUser.email == email, AppUser.is_active.is_(True)))
    if user is None or user.password_hash is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def user_upsert(db: Session, user_info: dict) -> AppUser:
    """ Insert or update existing user based on OAUTH userinfo
    
    :param db: Database session
    :param user_info: OAUTH2 IDP userinfo
    """

    user = db.scalar(select(AppUser).where(AppUser.email == user_info['email']))

    if not user:

        org = db.query(Organization).filter_by(is_platform_operator=True).first()
        if org is None:
            org = Organization(name="SURF", slug="surf", is_platform_operator=True)
            db.add(org)
            db.flush()

        user = AppUser(
            organization_id=org.id,
            email=user_info['email'],
            name=user_info['name'],
            role=UserRole.admin
        )
        db.add(user)
        db.flush()

    user.last_login_at = dt.datetime.now(dt.UTC)
    db.commit()

    return user