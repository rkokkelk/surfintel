from app.enrichment.cve_extractor import CveExtractor
from app.models.item import Item


def test_extracts_and_dedupes_cve_ids():
    item = Item(
        title="CISA voegt CVE-2026-31337 toe aan KEV",
        extracted_text="Zie ook cve-2026-31337 en CVE-2026-29844 voor meer details.",
    )

    result = CveExtractor().run(item, prior_results={})

    assert result["cve_ids"] == ["CVE-2026-29844", "CVE-2026-31337"]


def test_match_fields_maps_to_cve_id_field():
    data = {"cve_ids": ["CVE-2026-31337"]}
    assert CveExtractor().match_fields(data) == {"cve_id": ["CVE-2026-31337"]}
