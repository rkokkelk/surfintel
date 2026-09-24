import inspect
import uuid

from app.alerting.tasks import notify


def test_notify_accepts_chord_results_as_first_positional_argument():
    # A chord calls its callback as notify(<header results>, **kwargs bound with .s()>).
    # With item_id as the first parameter this raised
    # "TypeError: notify() got multiple values for argument 'item_id'".
    signature = notify.s(item_id=uuid.uuid4(), source_id=uuid.uuid4())
    header_results = [["cve_extractor", {"cve_ids": []}]]

    inspect.signature(notify.run).bind(header_results, **signature.kwargs)


def test_notify_accepts_empty_results_for_a_chord_without_header_tasks():
    # All enrichments switched off on a source: Celery runs the body with [].
    signature = notify.s(item_id=uuid.uuid4(), source_id=uuid.uuid4())

    inspect.signature(notify.run).bind([], **signature.kwargs)
