from __future__ import annotations

import datetime as dt
import uuid

import bcrypt
import jwt

from app.core.config import settings


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


def create_access_token(
    *, user_id: uuid.UUID, organization_id: uuid.UUID, role: str, is_platform_admin: bool, expires: bool = True
) -> str:
    """`expires=False` omits the `exp` claim entirely for a long-lived API
    token — PyJWT's decode() only enforces expiry when `exp` is present, so
    leaving it out (not setting it far in the future) is what makes the
    token genuinely non-expiring rather than expiring in, say, 100 years.
    """
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user_id),
        "org_id": str(organization_id),
        "role": role,
        "is_platform_admin": is_platform_admin,
        "iat": now,
    }
    if expires:
        payload["exp"] = now + dt.timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
