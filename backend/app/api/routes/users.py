from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin, scoped_to_org
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import AppUser
from app.schemas.auth import CurrentUser
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)) -> list[AppUser]:
    query = scoped_to_org(select(AppUser), AppUser, current_user)
    return list(db.scalars(query))


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)
) -> AppUser:
    user = AppUser(
        organization_id=current_user.organization_id,
        email=body.email,
        name=body.name,
        role=body.role,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    return user
