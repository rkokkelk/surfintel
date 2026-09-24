from unittest.mock import MagicMock

from app.enrichment.pipeline import run_enrichment_for_item
from app.models.item import Item
from app.models.source import Source, SourceType


def _run(**toggles):
    source = Source(name="s", type=SourceType.rss, config={}, **toggles)
    # No CVE ids in the text, so kev_checker never has a reason to hit the network.
    item = Item(title="Nieuws over een patch", extracted_text="Geen identifiers hier.")
    item.source = source

    db = MagicMock()
    db.scalar.return_value = None  # no existing item_enrichment rows

    results = run_enrichment_for_item(db, item)
    stored = {call.args[0].module_name for call in db.add.call_args_list}
    return results, stored


def test_all_modules_run_when_all_toggles_on():
    results, stored = _run(enrich_cve=True, enrich_cpe=True, enrich_kev=True, enrich_ai=True)

    expected = {"cve_extractor", "cpe_extractor", "kev_checker", "ai_categorizer"}
    assert set(results) == expected
    assert stored == expected


def test_disabled_modules_are_skipped_and_not_stored():
    results, stored = _run(enrich_cve=True, enrich_cpe=False, enrich_kev=False, enrich_ai=True)

    assert set(results) == {"cve_extractor", "ai_categorizer"}
    assert stored == {"cve_extractor", "ai_categorizer"}


def test_all_toggles_off_runs_nothing():
    results, stored = _run(enrich_cve=False, enrich_cpe=False, enrich_kev=False, enrich_ai=False)

    assert results == {}
    assert stored == set()
