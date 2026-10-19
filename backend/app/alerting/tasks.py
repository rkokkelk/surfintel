import datetime as dt
import uuid

import apprise
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.alerting.match_view import build_match_view, condition_matches
from app.alerting.templating import build_template_context, render_message
from app.celery import app
from app.core.encryption import decrypt
from app.core.media import screenshot_path
from app.core.singleton_task import UuidSafeSingleton
from app.enrichment.tasks import ENRICHMENT_MODULES
from app.models.alert import (
    AlertChannel,
    AlertCondition,
    AlertMatch,
    AlertRule,
    AlertRuleStatus,
    NotificationStatus,
)
from app.models.enrichment import ItemEnrichment
from app.models.item import Item, ItemStatus
from app.models.source import Source


@app.task(base=UuidSafeSingleton)
def match_alert_items(rule_id: uuid.UUID, limit: int=25) -> list[Item]:
    """ Identify existing items which are matched by alert rule
     
    :param rule_id: UUID of rule
    :param limit: amount of matches to look through before stopping
    :returns: List of matched Items
    """
    with app.conf['dbSession']() as db:
        result: list[Item] = []

        rule = db.get(AlertRule, rule_id)
        conditions = db.scalars(select(AlertCondition).where(AlertCondition.alert_rule_id == rule.id)).all()
        items = db.execute(
            select(Item)
            .where(Item.status == ItemStatus.enriched)
            .order_by(Item.published_at.desc().nullslast(), Item.last_checked_at.desc())
        ).yield_per(100)

        modules = list(ENRICHMENT_MODULES.values())

        for item in items:
            item = item[0]
            rows = db.scalars(select(ItemEnrichment).where(ItemEnrichment.item_id == item.id)).all()
            enrichment_results = {row.module_name: row.data for row in rows if isinstance(row.data, dict)}
            view = build_match_view(item, item.source, modules, enrichment_results)

            if not all(condition_matches(c, view) for c in conditions):
                continue

            result.append(item.id)

            if limit != 0 and len(result) >= limit:
                break

        return result

@app.task(base=UuidSafeSingleton)
def store_match_alert_items(items: list[uuid.UUID], rule_id: uuid.UUID):
    """ Store all identified alert item matches 
    :param items: List of identified items
    :param rule_id: Rule that has been identified
    """
    with app.conf['dbSession']() as db:
        rule = db.get(AlertRule, rule_id)
        items = db.scalars(
            select(Item)
            .where(Item.id.in_(items))
        )

        for item in items:
            _store_alert_match(db, item, rule)

        db.commit()


@app.task(base=UuidSafeSingleton)
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
            if not conditions or not all(condition_matches(c, view) for c in conditions):
                continue

            (new, match) = _store_alert_match(db, item, rule)

            if new:
                send_alert_notification(db, rule, item, match, view, source)

        db.commit()  # the `with` only closes the session: uncommitted matches would be rolled back


def send_alert_notification(
    db: Session, rule: AlertRule, item: Item, match: AlertMatch, view: dict, source: Source
) -> None:
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
    body = render_message(rule.message_template, build_template_context(item, source, rule, view))

    # Only backends that render the page (Playwright) produce a screenshot. Apprise
    # refuses to send at all when an attachment can't be read, so attach only if it exists.
    screenshot = screenshot_path(item.id)
    sent = notifier.notify(title=title, body=body, attach=str(screenshot) if screenshot.is_file() else None)

    match.notified_at = dt.datetime.now(dt.UTC)
    match.notification_status = NotificationStatus.sent if sent else NotificationStatus.failed


def _store_alert_match(db: Session, item: Item, rule: AlertRule) -> tuple[bool, AlertMatch]:
    """ Store a single alert match
    :param db: DB session
    :param item: Item to store match with
    :param rule: Rule to store match with
    :return: Tuple (bool whether match is new, AlertMatch)
    """
    already_matched = db.scalar(
        select(AlertMatch).where(AlertMatch.alert_rule_id == rule.id, AlertMatch.item_id == item.id)
    )
    if already_matched:
        return (False, already_matched)

    match = AlertMatch(alert_rule_id=rule.id, item_id=item.id, matched_at=dt.datetime.now(dt.UTC))
    db.add(match)
    db.flush()

    return (True, match)