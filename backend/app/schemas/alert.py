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


class AlertRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    status: AlertRuleStatus
    created_at: dt.datetime
    conditions: list[AlertConditionOut] = []
    channels: list[AlertChannelOut] = []
