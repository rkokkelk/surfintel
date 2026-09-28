"""Renders AlertRule.message_template against a match: {placeholder} tokens,
filled in from the item, its source, the rule, and the flattened match view
(app/alerting/match_view.py) — so every field a condition can match on
(vendor, cve_id, severity, ...) is also available to write into.

Used by both the real notification path (app/alerting/tasks.py) and the
rule "test" endpoint, so a preview always renders exactly like the real
message would.
"""

from __future__ import annotations

import datetime as dt

from app.alerting.match_view import MatchView
from app.models.alert import AlertRule
from app.models.item import Item
from app.models.source import Source

DEFAULT_TEMPLATE = "{title}\n{url}"


class _SafeDict(dict):
    """Leaves an unknown {placeholder} visible in the output instead of
    raising, so a typo in the template shows up as a literal token in the
    preview/notification rather than silently dropping the message.
    """

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def build_template_context(item: Item, source: Source, rule: AlertRule, view: MatchView) -> dict[str, str]:
    context: dict[str, str] = {
        "title": item.title or item.url,
        "url": item.url,
        "source": source.name,
        "rule_name": rule.name,
        "description": item.description or "",
        "published_at": item.published_at.strftime("%Y-%m-%d %H:%M") if item.published_at else "",
    }
    for field, values in view.items():
        if field == "keyword":
            continue
        context[field] = ", ".join(values)
    return context


def render_message(template: str | None, context: dict[str, str]) -> str:
    tpl = template.strip() if template and template.strip() else DEFAULT_TEMPLATE
    try:
        return tpl.format_map(_SafeDict(context))
    except (ValueError, IndexError):
        # e.g. a stray "{" from the user — fall back rather than 500ing / failing to notify.
        return DEFAULT_TEMPLATE.format_map(_SafeDict(context))
