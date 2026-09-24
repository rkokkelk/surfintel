import uuid

from app.enrichment.tasks import get_enrichments_tasks
from app.models.item import Item
from app.models.source import Source, SourceType


def _module_keys(**toggles) -> set[str]:
    source = Source(name="s", type=SourceType.rss, config={}, **toggles)
    item = Item(id=uuid.uuid4())

    # each header signature is run_enrichment_for_item.s(item_id, <toggle key>)
    return {sig.args[1] for sig in get_enrichments_tasks(item, source)}


def test_all_modules_run_when_all_toggles_on():
    keys = _module_keys(enrich_cve=True, enrich_cpe=True, enrich_kev=True, enrich_ai=True)

    assert keys == {"enrich_cve", "enrich_cpe", "enrich_kev", "enrich_ai"}


def test_disabled_modules_are_left_out_of_the_chord_header():
    keys = _module_keys(enrich_cve=True, enrich_cpe=False, enrich_kev=False, enrich_ai=True)

    assert keys == {"enrich_cve", "enrich_ai"}


def test_all_toggles_off_gives_an_empty_header():
    assert _module_keys(enrich_cve=False, enrich_cpe=False, enrich_kev=False, enrich_ai=False) == set()
