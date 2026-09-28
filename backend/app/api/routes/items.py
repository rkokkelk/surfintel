import datetime as dt
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.media import screenshot_path
from app.db.session import get_db
from app.models.enrichment import ItemEnrichment
from app.models.item import Item, ItemStatus
from app.schemas.item import ItemDetailOut, ItemOut

router = APIRouter(prefix="/items", tags=["items"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ItemOut])
def list_items(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    limit: int = Query(50, le=200),
    q: str | None = Query(None, description="Zoekterm in titel, omschrijving of opgehaalde tekst"),
    source_id: uuid.UUID | None = None,
    cve_id: str | None = None,
    published_after: dt.datetime | None = None,
    published_before: dt.datetime | None = None,
) -> list[Item]:
    # The item feed is shared across every organization — no organization_id
    # filter here, unlike the org-owned tables (see app/api/deps.py).
    # Item.source is `lazy="joined"` (see app/models/item.py), so it's
    # eagerly loaded here without needing an explicit join/option.
    query = select(Item).where(Item.status == ItemStatus.enriched)

    if source_id:
        query = query.where(Item.source_id == source_id)

    if published_after:
        query = query.where(Item.published_at >= published_after)
    if published_before:
        query = query.where(Item.published_at <= published_before)

    if q:
        pattern = f"%{q}%"
        query = query.where(
            or_(
                Item.title.ilike(pattern),
                Item.description.ilike(pattern),
                Item.extracted_text.ilike(pattern),
            )
        )

    if cve_id:
        # cve_extractor's `cve_ids` is a JSON array (one item has at most one row
        # for this module — uq_item_module), so a substring match on its JSON
        # text is a plain containment check, no risk of duplicate item rows.
        query = query.join(ItemEnrichment, ItemEnrichment.item_id == Item.id).where(
            ItemEnrichment.module_name == "cve_extractor",
            ItemEnrichment.data["cve_ids"].as_string().ilike(f"%{cve_id}%"),
        )

    query = query.order_by(Item.published_at.desc()).limit(limit)
    items = list(db.scalars(query))
    _attach_enrichments(db, items)
    return items


@router.get("/{item_id}", response_model=ItemDetailOut)
def get_item(item_id: uuid.UUID, db: Session = Depends(get_db), _user=Depends(get_current_user)) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "Item niet gevonden")
    _attach_enrichments(db, [item])
    return item

@router.get("/{item_id}/screenshot")
def get_screenshot(item_id: uuid.UUID, _user=Depends(get_current_user)) -> FileResponse:
    path = screenshot_path(item_id)

    if not path.is_file():
        raise HTTPException(404, "No screenshot available")

    return FileResponse(path, media_type="image/png")


def _attach_enrichments(db: Session, items: list[Item]) -> None:
    """`enrichments` isn't a mapped relationship — item_enrichment rows are
    looked up on demand and set as a plain attribute so ItemOut.from_attributes
    can pick them up. Batched in one query rather than per item (N+1).
    """
    if not items:
        return
    item_ids = [item.id for item in items]
    rows = db.scalars(select(ItemEnrichment).where(ItemEnrichment.item_id.in_(item_ids))).all()

    by_item: dict[uuid.UUID, list[ItemEnrichment]] = {}
    for row in rows:
        # `data` is written by whatever enrichment module last ran — a module
        # mid-rewrite once stored a bare string here instead of a dict, which
        # took the *entire* /items list down with a 500 for every user (a
        # single malformed row shouldn't be able to do that). Drop it and
        # keep serving the rest; it'll be corrected next time enrichment
        # actually runs for that item.
        if not isinstance(row.data, dict):
            logger.warning(
                "Skipping malformed item_enrichment row %s (item=%s, module=%s): data is %s, not a dict",
                row.id, row.item_id, row.module_name, type(row.data).__name__,
            )
            continue
        by_item.setdefault(row.item_id, []).append(row)

    for item in items:
        item.enrichments = by_item.get(item.id, [])
