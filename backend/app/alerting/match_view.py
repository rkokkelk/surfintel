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
from app.models.alert import AlertCondition, AlertField
from app.models.item import Item
from app.models.source import Source

MatchView = dict[str, list[str]]

# Fields matched by "actual value >= wanted threshold" instead of set
# membership — the condition's `values` holds a single minimum score (e.g.
# ["7"] for "CVSS >= 7"), not an OR-list, and the view's value is the item's
# max score across every CVE it mentions (computed in CveExtractor.run()).
THRESHOLD_FIELDS = {AlertField.cvss_score, AlertField.epss_score}


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


def condition_matches(condition: AlertCondition, view: MatchView) -> bool:
    """Shared by both the live alerting pipeline (app/alerting/tasks.py) and
    the rule "test" endpoint (app/api/routes/alerts.py), so a preview always
    reflects exactly what would fire for real.
    """
    if condition.field in THRESHOLD_FIELDS:
        try:
            threshold = float(condition.values[0])
        except (IndexError, ValueError):
            return False  # no/unparsable threshold configured — never matches, rather than raising
        actual = view.get(condition.field.value, [])
        try:
            return bool(actual) and float(actual[0]) >= threshold
        except ValueError:
            return False

    wanted = {v.lower() for v in condition.values}

    if condition.field == AlertField.keyword:
        haystack = " ".join(view.get("keyword", []))
        return any(word in haystack for word in wanted)

    return bool(wanted & set(view.get(condition.field.value, [])))
