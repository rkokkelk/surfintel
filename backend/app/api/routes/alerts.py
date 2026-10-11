import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from feedgen.feed import FeedGenerator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.alerting.match_view import build_match_view, condition_matches
from app.alerting.templating import build_template_context, render_message
from app.api.deps import get_current_user, require_admin, scoped_to_org
from app.core.encryption import decrypt, encrypt, mask
from app.db.session import get_db
from app.enrichment.tasks import ENRICHMENT_MODULES
from app.models.alert import AlertChannel, AlertCondition, AlertMatch, AlertRule, AlertRuleStatus
from app.models.enrichment import ItemEnrichment
from app.models.item import Item, ItemStatus
from app.models.source import Source
from app.schemas.alert import (
    AlertChannelOut,
    AlertConditionOut,
    AlertDashboardDayCount,
    AlertDashboardItemOut,
    AlertDashboardOut,
    AlertDashboardSourceCount,
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

# The TV dashboard: how many of the most recent real matches (AlertMatch rows,
# written by the live app/alerting/tasks.py:notify() path — not a re-scan) to
# show, how far back the two charts look, and how many distinct sources the
# pie chart seats before folding the tail into "Overig" (see the dataviz
# skill's series-count ladder — past ~7-8 a categorical palette stops helping).
DASHBOARD_ITEM_LIMIT = 25
DASHBOARD_WINDOW_DAYS = 14
DASHBOARD_SOURCE_CAP = 7
DASHBOARD_DESCRIPTION_MAX_CHARS = 320


def _truncate_description(text: str | None) -> str | None:
    """Caps a description to roughly one paragraph, breaking on a word
    boundary rather than mid-word. The TV dashboard has no room (or reader
    time) for more.
    """
    if text is None or len(text) <= DASHBOARD_DESCRIPTION_MAX_CHARS:
        return text
    cut = text[:DASHBOARD_DESCRIPTION_MAX_CHARS].rsplit(" ", 1)[0]
    return cut + "…"


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
    """ Completely delete the Alert specified by rule_id.
    """
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


@router.get("/{rule_id}/dashboard", response_model=AlertDashboardOut)
def get_alert_dashboard(
    rule_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> AlertDashboardOut:
    """Feeds the big-screen/TV view: the most recent real matches for this
    rule (from AlertMatch — the live-fired history, not a re-scan) plus two
    aggregates for its charts. Any authenticated org member can view this
    (not admin-only like the edit/test endpoints) — it's meant to run
    unattended on a shared screen.
    """
    rule = db.scalar(scoped_to_org(select(AlertRule), AlertRule, current_user).where(AlertRule.id == rule_id))
    if rule is None:
        raise HTTPException(404, "Alert-regel niet gevonden")

    display_rows = db.execute(
        select(AlertMatch, Item, Source)
        .join(Item, Item.id == AlertMatch.item_id)
        .join(Source, Source.id == Item.source_id)
        .where(AlertMatch.alert_rule_id == rule.id)
        .order_by(AlertMatch.matched_at.desc())
        .limit(DASHBOARD_ITEM_LIMIT)
    ).all()

    items_out = [
        AlertDashboardItemOut(
            item_id=item.id,
            title=item.title,
            description=_truncate_description(item.description),
            published_at=item.published_at,
            matched_at=match.matched_at,
            source_name=source.name,
            source_favicon=source.favicon,
        )
        for match, item, source in display_rows
    ]

    # Separate, wider (but unlimited-count) window for the two charts, so a
    # rule that fires rarely still shows its real last-25 items above even
    # when none of them fall inside the chart window.
    window_start = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DASHBOARD_WINDOW_DAYS)
    window_rows = db.execute(
        select(AlertMatch.matched_at, Source.name, Source.favicon)
        .select_from(AlertMatch)
        .join(Item, Item.id == AlertMatch.item_id)
        .join(Source, Source.id == Item.source_id)
        .where(AlertMatch.alert_rule_id == rule.id, AlertMatch.matched_at >= window_start)
    ).all()

    today = dt.datetime.now(dt.timezone.utc).date()
    day_counts: dict[dt.date, int] = {today - dt.timedelta(days=offset): 0 for offset in range(DASHBOARD_WINDOW_DAYS)}
    source_tally: dict[str, dict] = {}
    for matched_at, source_name, source_favicon in window_rows:
        day = matched_at.date()
        if day in day_counts:
            day_counts[day] += 1
        entry = source_tally.setdefault(source_name, {"favicon": source_favicon, "count": 0})
        entry["count"] += 1

    daily_counts = [AlertDashboardDayCount(date=day, count=count) for day, count in sorted(day_counts.items())]

    ranked = sorted(source_tally.items(), key=lambda kv: kv[1]["count"], reverse=True)
    source_counts = [
        AlertDashboardSourceCount(source_name=name, source_favicon=data["favicon"], count=data["count"])
        for name, data in ranked[:DASHBOARD_SOURCE_CAP]
    ]
    rest_count = sum(data["count"] for _, data in ranked[DASHBOARD_SOURCE_CAP:])
    if rest_count:
        source_counts.append(AlertDashboardSourceCount(source_name="Overig", source_favicon=None, count=rest_count))

    return AlertDashboardOut(
        rule_id=rule.id,
        rule_name=rule.name,
        items=items_out,
        daily_counts=daily_counts,
        source_counts=source_counts,
    )


@router.post("/{rule_id}/pause", response_model=AlertRuleOut)
def pause_alert_rule(
    rule_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)
) -> AlertRuleOut:
    rule = db.scalar(scoped_to_org(select(AlertRule), AlertRule, current_user).where(AlertRule.id == rule_id))
    if rule is None:
        raise HTTPException(404, "Alert-regel niet gevonden")

    rule.status = AlertRuleStatus.paused
    rule.updated_at = dt.datetime.now(dt.UTC)
    db.commit()
    return _to_out(db, rule)


@router.get("/{rule_id}/rss", response_class=Response)
def get_rss_feed(
    rule_id: uuid.UUID, request: Request, db: Session = Depends(get_db)
) -> AlertRuleOut:
    """ Generate an RSS feed for the given alert
    """
    rule: AlertRule = db.get(AlertRule, rule_id)

    if rule is None:
        raise HTTPException(404, "Alert-regel niet gevonden")

    fg = FeedGenerator()
    fg.title('SURFintel Alert')
    fg.link( href=str(request.url), rel='alternate' )
    fg.subtitle(rule.name)
    fg.language('en')

    matched_items = db.scalars(select(Item).join(AlertMatch, AlertMatch.item_id == Item.id).where(AlertMatch.alert_rule_id == rule.id).limit(25))

    for item in matched_items:
        fe = fg.add_entry()
        fe.id(str(item.id))
        fe.title(item.title)
        fe.link(href=item.url)

    return Response(content=fg.rss_str(), media_type="text/xml")