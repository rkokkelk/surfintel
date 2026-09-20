from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_platform_admin
from app.db.session import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceOut

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list[Source]:
    # Sources are global/shared across every organization — any authenticated
    # user may see which feeds/advisories feed the platform.
    return list(db.scalars(select(Source)))


@router.post("", response_model=SourceOut, status_code=201)
def create_source(
    body: SourceCreate, db: Session = Depends(get_db), _admin=Depends(require_platform_admin)
) -> Source:
    source = Source(
        name=body.name, type=body.type, config=body.config, poll_interval_seconds=body.poll_interval_seconds
    )
    db.add(source)
    db.commit()
    return source
