import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin, scoped_to_org
from app.core.encryption import decrypt, encrypt, mask
from app.db.session import get_db
from app.models.alert import AlertChannel, AlertCondition, AlertRule, AlertRuleStatus
from app.schemas.alert import AlertChannelOut, AlertConditionOut, AlertRuleCreate, AlertRuleOut
from app.schemas.auth import CurrentUser

router = APIRouter(prefix="/alerts", tags=["alerts"])


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
    rule = AlertRule(organization_id=current_user.organization_id, created_by=current_user.id, name=body.name)
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
