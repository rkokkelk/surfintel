import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enrichment import ItemEnrichment
from app.models.item import Item, ItemStatus
from app.schemas.item import ItemDetailOut, ItemOut

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=list[ItemOut])
def list_items(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
    limit: int = Query(50, le=200),
    category: str | None = None,
) -> list[Item]:
    # The item feed is shared across every organization — no organization_id
    # filter here, unlike the org-owned tables (see app/api/deps.py).
    query = select(Item).where(Item.status == ItemStatus.enriched)

    if category:
        query = query.join(ItemEnrichment, ItemEnrichment.item_id == Item.id).where(
            ItemEnrichment.module_name == "ai_categorizer",
            ItemEnrichment.data["category"].as_string() == category,
        )

    query = query.order_by(Item.created_at.desc()).limit(limit)
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
        by_item.setdefault(row.item_id, []).append(row)

    for item in items:
        item.enrichments = by_item.get(item.id, [])
