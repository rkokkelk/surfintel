import datetime as dt

import uuid
import apprise
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.celery import app
from app.core.media import screenshot_path
from app.core.encryption import decrypt
from app.models.alert import AlertChannel, AlertMatch, AlertRule, NotificationStatus
from app.models.item import Item, ItemStatus

from app.alerting.match_view import MatchView, build_match_view
from app.enrichment.tasks import ENRICHMENT_MODULES
from app.models.alert import AlertCondition, AlertField, AlertMatch, AlertRule, AlertRuleStatus
from app.models.item import Item
from app.models.source import Source


def _condition_matches(condition: AlertCondition, view: MatchView) -> bool:
    wanted = {v.lower() for v in condition.values}

    if condition.field == AlertField.keyword:
        haystack = " ".join(view.get("keyword", []))
        return any(word in haystack for word in wanted)

    return bool(wanted & set(view.get(condition.field.value, [])))


@app.task
def notify(results: list[tuple[str, dict]], item_id: uuid.UUID, source_id: uuid.UUID) -> None:
    """Chord callback. A chord passes the header tasks' return values (a list in header
    order, each `(module_name, data)`) as the FIRST positional argument, ahead of the
    kwargs bound with `.s()`. So `results` has to come first here: with `item_id` first,
    that list lands in `item_id` and the `item_id=` kwarg then collides with it.
    """
    with app.conf['dbSession']() as db:
        item = db.get(Item, item_id)
        source = db.get(Source, source_id)

        # All enrichments are done at this point (that's what a chord's body means).
        # Commit first so the item shows up in the feed even if alerting fails below.
        item.status = ItemStatus.enriched
        db.commit()

        enrichment_results = dict(results)
        view = build_match_view(item, source, list(ENRICHMENT_MODULES.values()), enrichment_results)

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

        db.commit()  # the `with` only closes the session: uncommitted matches would be rolled back


def send_alert_notification(db: Session, rule: AlertRule, item: Item, match: AlertMatch) -> None:
    channels = db.scalars(
        select(AlertChannel).where(AlertChannel.alert_rule_id == rule.id, AlertChannel.enabled.is_(True))
    ).all()

    if not channels:
        match.notification_status = NotificationStatus.failed
        return

    notifier = apprise.Apprise()
    for channel in channels:
        notifier.add(decrypt(channel.apprise_url_encrypted))

    title = f"SurfIntel alert: {rule.name}"
    body = f"{item.title or item.url}\n{item.url}"

    # Only backends that render the page (Playwright) produce a screenshot. Apprise
    # refuses to send at all when an attachment can't be read, so attach only if it exists.
    screenshot = screenshot_path(item.id)
    sent = notifier.notify(title=title, body=body, attach=str(screenshot) if screenshot.is_file() else None)

    match.notified_at = dt.datetime.now(dt.timezone.utc)
    match.notification_status = NotificationStatus.sent if sent else NotificationStatus.failed
