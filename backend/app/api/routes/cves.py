from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.cve import Cve, ItemCve
from app.models.item import Item
from app.schemas.cve import CveDetailOut, CveOut

router = APIRouter(prefix="/cves", tags=["cves"])


@router.get("", response_model=list[CveOut])
def list_cves(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    q: str | None = None,
    in_kev: bool | None = None,
    sort: Literal["recent", "cvss", "epss"] = "recent",
    limit: int = Query(50, le=200),
) -> list[Cve]:
    query = select(Cve)

    if q:
        pattern = f"%{q}%"
        query = query.where(or_(Cve.cve_id.ilike(pattern), Cve.title.ilike(pattern)))
    if in_kev is not None:
        query = query.where(Cve.in_kev == in_kev)

    if sort == "cvss":
        query = query.order_by(func.coalesce(Cve.cvss_v4_score, Cve.cvss_v3_score, 0).desc())
    elif sort == "epss":
        query = query.order_by(func.coalesce(Cve.epss_score, 0).desc())
    else:
        query = query.order_by(Cve.fetched_at.desc().nullslast())

    return list(db.scalars(query.limit(limit)))


@router.get("/{cve_id}", response_model=CveDetailOut)
def get_cve(cve_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)) -> Cve:
    cve = db.get(Cve, cve_id.upper())
    if cve is None:
        raise HTTPException(404, "CVE niet gevonden")

    # `items` isn't a mapped relationship — same batching-free pattern as
    # Item.enrichments in routes/items.py, set as a plain attribute so
    # CveDetailOut.from_attributes can pick it up.
    cve.items = list(
        db.scalars(
            select(Item)
            .join(ItemCve, ItemCve.item_id == Item.id)
            .where(ItemCve.cve_id == cve.cve_id)
            .order_by(Item.published_at.desc())
        )
    )
    return cve
