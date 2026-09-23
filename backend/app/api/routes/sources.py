import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_platform_admin
from app.ingestion.tasks import run_ingestion_cycle
from app.db.session import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceOut, SourceUpdate, SourceIngestion

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list[Source]:
    # Sources are global/shared across every organization — any authenticated
    # user may see which feeds/advisories feed the platform.
    return list(db.scalars(select(Source)))


@router.post("", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
def create_source(
    body: SourceCreate, db: Session = Depends(get_db), _admin=Depends(require_platform_admin)
) -> Source:
    source = Source(
        name=body.name, type=body.type, config=body.config, poll_interval_seconds=body.poll_interval_seconds
    )

    source.get_favicon()

    db.add(source)
    db.commit()
    return source


@router.post("/{source_id}/ingest", status_code=status.HTTP_202_ACCEPTED)
def ingest_source(
    source_id: uuid.UUID,
    body: SourceIngestion,
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
):
    run_ingestion_cycle.delay(source_id=source_id, force=body.force)

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

    source.get_favicon()

    db.commit()
    return source

@router.delete("/{source_id}", status_code=status.HTTP_202_ACCEPTED)
def delete_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> None:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(404, "Bron niet gevonden")

    db.delete(source)
    db.commit()