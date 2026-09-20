"""Builds the flat object alert conditions are matched against. Every
enrichment module declares its own contribution via `match_fields()`
(app/enrichment/base.py) — list-valued fields are unioned across modules, so
adding a module never requires touching this file.

Note: `vendor`, `product` and `tag` are valid AlertField values (the schema
and UI support them) but no registered enrichment module currently populates
them — that needs a vendor/product extractor module (e.g. derived from the
cpe_extractor's output) before rules using those fields can match anything.
"""

from app.enrichment.base import EnrichmentModule
from app.models.item import Item
from app.models.source import Source

MatchView = dict[str, list[str]]


def build_match_view(
    item: Item,
    source: Source,
    modules: list[EnrichmentModule],
    enrichment_results: dict[str, dict],
) -> MatchView:
    view: MatchView = {"source": [source.name.lower()]}

    text = " ".join(filter(None, [item.title, item.extracted_text])).lower()
    view["keyword"] = [text]

    for module in modules:
        data = enrichment_results.get(module.name, {})
        for field, values in module.match_fields(data).items():
            existing = set(view.get(field, []))
            view[field] = sorted(existing | {v.lower() for v in values if v})

    return view
