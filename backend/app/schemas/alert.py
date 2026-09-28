import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.alert import AlertField, AlertRuleStatus


class AlertConditionIn(BaseModel):
    field: AlertField
    values: list[str]


class AlertConditionOut(AlertConditionIn):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class AlertChannelIn(BaseModel):
    label: str
    apprise_url: str


class AlertChannelUpdateIn(BaseModel):
    """`id` present + `apprise_url` omitted = keep that channel's existing
    (encrypted, never round-tripped to the client) secret unchanged; `id`
    absent = a new channel, which does require an apprise_url.
    """

    id: uuid.UUID | None = None
    label: str
    apprise_url: str | None = None
    enabled: bool = True


class AlertChannelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    apprise_url_masked: str
    enabled: bool


class AlertRuleCreate(BaseModel):
    name: str
    conditions: list[AlertConditionIn]
    channels: list[AlertChannelIn]
    message_template: str | None = None


class AlertRuleUpdate(BaseModel):
    name: str
    status: AlertRuleStatus
    conditions: list[AlertConditionIn]
    channels: list[AlertChannelUpdateIn]
    message_template: str | None = None


class AlertRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    status: AlertRuleStatus
    created_at: dt.datetime
    conditions: list[AlertConditionOut] = []
    channels: list[AlertChannelOut] = []
    message_template: str | None = None


class AlertRuleTestRequest(BaseModel):
    """Optional overrides let the UI preview unsaved edits (draft conditions
    and/or a draft template) without first persisting them.
    """

    conditions: list[AlertConditionIn] | None = None
    message_template: str | None = None


class AlertTestMatchOut(BaseModel):
    item_id: uuid.UUID
    title: str | None
    url: str
    source_name: str
    published_at: dt.datetime | None
    message_preview: str
