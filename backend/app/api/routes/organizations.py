from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin
from app.db.session import get_db
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationOut

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationOut])
def list_organizations(
    db: Session = Depends(get_db), _admin=Depends(require_platform_admin)
) -> list[Organization]:
    return list(db.scalars(select(Organization)))


@router.post("", response_model=OrganizationOut, status_code=201)
def create_organization(
    body: OrganizationCreate, db: Session = Depends(get_db), _admin=Depends(require_platform_admin)
) -> Organization:
    org = Organization(name=body.name, slug=body.slug)
    db.add(org)
    db.commit()
    return org
