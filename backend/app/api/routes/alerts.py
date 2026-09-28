import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.alerting.match_view import build_match_view, condition_matches
from app.alerting.templating import build_template_context, render_message
from app.api.deps import require_admin, scoped_to_org
from app.core.encryption import decrypt, encrypt, mask
from app.db.session import get_db
from app.enrichment.tasks import ENRICHMENT_MODULES
from app.models.alert import AlertChannel, AlertCondition, AlertMatch, AlertRule, AlertRuleStatus
from app.models.enrichment import ItemEnrichment
from app.models.item import Item, ItemStatus
from app.schemas.alert import (
    AlertChannelOut,
    AlertConditionOut,
    AlertRuleCreate,
    AlertRuleOut,
    AlertRuleTestRequest,
    AlertRuleUpdate,
    AlertTestMatchOut,
)
from app.schemas.auth import CurrentUser

router = APIRouter(prefix="/alerts", tags=["alerts"])

# How many of the most recently seen enriched items the "test" endpoint scans
# looking for the 10 most recent hits — a cap so an org with a huge backlog
# and a very narrow rule doesn't turn a preview into a full table scan.
TEST_SCAN_LIMIT = 500
TEST_RESULT_LIMIT = 10


def _to_out(db: Session, rule: AlertRule) -> AlertRuleOut:
    conditions = db.scalars(select(AlertCondition).where(AlertCondition.alert_rule_id == rule.id)).all()
    channels = db.scalars(select(AlertChannel).where(AlertChannel.alert_rule_id == rule.id)).all()

    return AlertRuleOut(
        id=rule.id,
        organization_id=rule.organization_id,
        name=rule.name,
        status=rule.status,
        created_at=rule.created_at,
        conditions=[AlertConditionOut.model_validate(c) for c in conditions],
        channels=[
            AlertChannelOut(
                id=c.id, label=c.label, apprise_url_masked=mask(decrypt(c.apprise_url_encrypted)), enabled=c.enabled
            )
            for c in channels
        ],
        message_template=rule.message_template,
    )


@router.get("", response_model=list[AlertRuleOut])
def list_alert_rules(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)
) -> list[AlertRuleOut]:
    rules = db.scalars(scoped_to_org(select(AlertRule), AlertRule, current_user)).all()
    return [_to_out(db, rule) for rule in rules]


@router.post("", response_model=AlertRuleOut, status_code=201)
def create_alert_rule(
    body: AlertRuleCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)
) -> AlertRuleOut:
    rule = AlertRule(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        name=body.name,
        message_template=body.message_template,
    )
    db.add(rule)
    db.flush()

    for condition in body.conditions:
        db.add(AlertCondition(alert_rule_id=rule.id, field=condition.field, values=condition.values))

    for channel in body.channels:
        db.add(
            AlertChannel(
                alert_rule_id=rule.id,
                label=channel.label,
                apprise_url_encrypted=encrypt(channel.apprise_url),
            )
        )

    db.commit()
    return _to_out(db, rule)


@router.put("/{rule_id}", response_model=AlertRuleOut)
def update_alert_rule(
    rule_id: uuid.UUID,
    body: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
) -> AlertRuleOut:
    rule = db.scalar(scoped_to_org(select(AlertRule), AlertRule, current_user).where(AlertRule.id == rule_id))
    if rule is None:
        raise HTTPException(404, "Alert-regel niet gevonden")

    rule.name = body.name
    rule.status = body.status
    rule.message_template = body.message_template
    rule.updated_at = dt.datetime.now(dt.timezone.utc)

    db.execute(delete(AlertCondition).where(AlertCondition.alert_rule_id == rule.id))
    for condition in body.conditions:
        db.add(AlertCondition(alert_rule_id=rule.id, field=condition.field, values=condition.values))

    existing_channels = {
        c.id: c for c in db.scalars(select(AlertChannel).where(AlertChannel.alert_rule_id == rule.id)).all()
    }
    keep_ids: set[uuid.UUID] = set()
    for channel in body.channels:
        if channel.id is not None and channel.id in existing_channels:
            row = existing_channels[channel.id]
            row.label = channel.label
            row.enabled = channel.enabled
            if channel.apprise_url:
                row.apprise_url_encrypted = encrypt(channel.apprise_url)
            keep_ids.add(channel.id)
        else:
            if not channel.apprise_url:
                raise HTTPException(422, "Nieuw notificatiekanaal vereist een Apprise-URL")
            db.add(
                AlertChannel(
                    alert_rule_id=rule.id,
                    label=channel.label,
                    apprise_url_encrypted=encrypt(channel.apprise_url),
                    enabled=channel.enabled,
                )
            )

    for channel_id, row in existing_channels.items():
        if channel_id not in keep_ids:
            db.delete(row)

    db.commit()
    return _to_out(db, rule)


@router.delete("/{rule_id}", status_code=204)
def delete_alert_rule(
    rule_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)
) -> None:
    rule = db.scalar(scoped_to_org(select(AlertRule), AlertRule, current_user).where(AlertRule.id == rule_id))
    if rule is None:
        raise HTTPException(404, "Alert-regel niet gevonden")

    db.execute(delete(AlertMatch).where(AlertMatch.alert_rule_id == rule.id))
    db.execute(delete(AlertChannel).where(AlertChannel.alert_rule_id == rule.id))
    db.execute(delete(AlertCondition).where(AlertCondition.alert_rule_id == rule.id))
    db.delete(rule)
    db.commit()


@router.post("/{rule_id}/test", response_model=list[AlertTestMatchOut])
def test_alert_rule(
    rule_id: uuid.UUID,
    body: AlertRuleTestRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
) -> list[AlertTestMatchOut]:
    """Evaluates the rule (or, if given, a draft set of conditions/template
    that hasn't been saved yet) against the most recently seen items, purely
    for preview — this never writes AlertMatch rows or sends notifications.
    """
    rule = db.scalar(scoped_to_org(select(AlertRule), AlertRule, current_user).where(AlertRule.id == rule_id))
    if rule is None:
        raise HTTPException(404, "Alert-regel niet gevonden")

    if body.conditions is not None:
        conditions = [AlertCondition(field=c.field, values=c.values) for c in body.conditions]
    else:
        conditions = db.scalars(select(AlertCondition).where(AlertCondition.alert_rule_id == rule.id)).all()
    if not conditions:
        return []

    template = body.message_template if body.message_template is not None else rule.message_template
    modules = list(ENRICHMENT_MODULES.values())

    items = db.scalars(
        select(Item)
        .where(Item.status == ItemStatus.enriched)
        .order_by(Item.published_at.desc().nullslast(), Item.last_checked_at.desc())
        .limit(TEST_SCAN_LIMIT)
    ).all()

    results: list[AlertTestMatchOut] = []
    for item in items:
        if len(results) >= TEST_RESULT_LIMIT:
            break

        rows = db.scalars(select(ItemEnrichment).where(ItemEnrichment.item_id == item.id)).all()
        enrichment_results = {row.module_name: row.data for row in rows if isinstance(row.data, dict)}
        view = build_match_view(item, item.source, modules, enrichment_results)

        if not all(condition_matches(c, view) for c in conditions):
            continue

        context = build_template_context(item, item.source, rule, view)
        results.append(
            AlertTestMatchOut(
                item_id=item.id,
                title=item.title,
                url=item.url,
                source_name=item.source.name,
                published_at=item.published_at,
                message_preview=render_message(template, context),
            )
        )

    return results


@router.post("/{rule_id}/pause", response_model=AlertRuleOut)
def pause_alert_rule(
    rule_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)
) -> AlertRuleOut:
    rule = db.scalar(scoped_to_org(select(AlertRule), AlertRule, current_user).where(AlertRule.id == rule_id))
    if rule is None:
        raise HTTPException(404, "Alert-regel niet gevonden")

    rule.status = AlertRuleStatus.paused
    rule.updated_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    return _to_out(db, rule)
