import datetime as dt

import apprise
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import decrypt
from app.models.alert import AlertChannel, AlertMatch, AlertRule, NotificationStatus
from app.models.item import Item


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

    sent = notifier.notify(title=title, body=body)

    match.notified_at = dt.datetime.now(dt.timezone.utc)
    match.notification_status = NotificationStatus.sent if sent else NotificationStatus.failed
