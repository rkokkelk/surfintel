"""Alert evaluation: after enrichment finishes for an item, check every
active alert_rule and notify the ones that match. Runs synchronously,
in-process, right after enrichment — consistent with the enrichment
pipeline's own MVP simplification (see docs/architecture.md); moving this to
a job queue later only means calling evaluate_alerts_for_item from a worker
instead of inline.
"""

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.alerting.match_view import MatchView, build_match_view
from app.alerting.notifier import send_alert_notification
from app.enrichment.pipeline import ENRICHMENT_MODULES
from app.models.alert import AlertCondition, AlertField, AlertMatch, AlertRule, AlertRuleStatus
from app.models.item import Item
from app.models.source import Source


def _condition_matches(condition: AlertCondition, view: MatchView) -> bool:
    wanted = {v.lower() for v in condition.values}

    if condition.field == AlertField.keyword:
        haystack = " ".join(view.get("keyword", []))
        return any(word in haystack for word in wanted)

    return bool(wanted & set(view.get(condition.field.value, [])))


def evaluate_alerts_for_item(db: Session, item: Item, source: Source, enrichment_results: dict[str, dict]) -> None:
    view = build_match_view(item, source, ENRICHMENT_MODULES, enrichment_results)

    active_rules = db.scalars(select(AlertRule).where(AlertRule.status == AlertRuleStatus.active)).all()

    for rule in active_rules:
        conditions = db.scalars(select(AlertCondition).where(AlertCondition.alert_rule_id == rule.id)).all()
        if not conditions or not all(_condition_matches(c, view) for c in conditions):
            continue

        already_matched = db.scalar(
            select(AlertMatch).where(AlertMatch.alert_rule_id == rule.id, AlertMatch.item_id == item.id)
        )
        if already_matched:
            continue

        match = AlertMatch(alert_rule_id=rule.id, item_id=item.id, matched_at=dt.datetime.now(dt.timezone.utc))
        db.add(match)
        db.flush()

        send_alert_notification(db, rule, item, match)
