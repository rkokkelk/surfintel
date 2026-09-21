import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_platform_admin
from app.db.session import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceOut, SourceUpdate

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

    if not source.favicon:
        source.get_favicon()

    db.add(source)
    db.commit()
    return source


@router.patch("/{source_id}", response_model=SourceOut)
def update_source(
    source_id: uuid.UUID,
    body: SourceUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> Source:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(404, "Bron niet gevonden")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    if not source.favicon:
        source.get_favicon()

    db.commit()
    return source
