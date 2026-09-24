from app.alerting.tasks import _condition_matches
from app.models.alert import AlertCondition, AlertField


def _condition(field: AlertField, values: list[str]) -> AlertCondition:
    return AlertCondition(field=field, values=values)


def test_list_field_matches_on_intersection():
    view = {"severity": ["kritiek"], "vendor": ["ivanti"]}
    condition = _condition(AlertField.severity, ["kritiek", "hoog"])

    assert _condition_matches(condition, view) is True


def test_list_field_no_match_when_disjoint():
    view = {"severity": ["midden"]}
    condition = _condition(AlertField.severity, ["kritiek", "hoog"])

    assert _condition_matches(condition, view) is False


def test_keyword_field_matches_on_substring():
    view = {"keyword": ["cisa waarschuwt voor een kritieke ivanti-kwetsbaarheid"]}
    condition = _condition(AlertField.keyword, ["ivanti"])

    assert _condition_matches(condition, view) is True
