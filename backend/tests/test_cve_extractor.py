from app.enrichment.cve_extractor import CveExtractor, _apply_opencve_payload
from app.models.cve import Cve
from app.models.item import Item

# A real OpenCVE v2 `/cves/{id}` response (CVE-2024-3400, fetched during
# development) — trimmed to what _apply_opencve_payload actually reads, plus
# the reference-duplication OpenCVE is known to produce (same URL filed by
# multiple CNA sources).
OPENCVE_PAYLOAD = {
    "cve_id": "CVE-2024-3400",
    "title": "PAN-OS: Arbitrary File Creation Leads to OS Command Injection Vulnerability in GlobalProtect",
    "description": "A command injection as a result of arbitrary file creation vulnerability...",
    "metrics": {
        "kev": {"data": {"dueDate": "2024-04-19T00:00:00+00:00", "dateAdded": "2024-04-12T00:00:00+00:00"}, "provider": "cisa"},
        "epss": {"data": {"score": 0.99999}, "provider": "first"},
        "cvssV2_0": {"data": {}, "provider": None},
        "cvssV3_0": {"data": {}, "provider": None},
        "cvssV3_1": {"data": {"score": 10, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"}, "provider": "mitre"},
        "cvssV4_0": {"data": {}, "provider": None},
    },
    "weaknesses": ["CWE-20", "CWE-77"],
    "nvd_cpe_configurations": [
        {
            "nodes": [
                {
                    "cpeMatch": [
                        {"criteria": "cpe:2.3:o:paloaltonetworks:pan-os:10.2.0:-:*:*:*:*:*:*", "vulnerable": True},
                        {"criteria": "cpe:2.3:o:paloaltonetworks:pan-os:11.0.0:-:*:*:*:*:*:*", "vulnerable": True},
                    ]
                }
            ]
        }
    ],
    "references": [
        {"source": "psirt@paloaltonetworks.com", "tags": ["Vendor Advisory"], "url": "https://security.paloaltonetworks.com/CVE-2024-3400"},
        {"source": "af854a3a-2127-422b-91ae-364da2661108", "tags": ["Vendor Advisory"], "url": "https://security.paloaltonetworks.com/CVE-2024-3400"},
        {"source": "af854a3a-2127-422b-91ae-364da2661108", "tags": ["Exploit", "Third Party Advisory"], "url": "https://www.volexity.com/blog/x"},
    ],
}


def test_apply_opencve_payload_maps_real_response_shape():
    cve = Cve(cve_id="CVE-2024-3400")

    _apply_opencve_payload(cve, OPENCVE_PAYLOAD)

    assert cve.cvss_v3_score == 10
    assert cve.cvss_v3_vector == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
    assert cve.cvss_v4_score is None
    assert cve.epss_score == 0.99999
    assert cve.in_kev is True
    assert cve.kev_date_added == "2024-04-12T00:00:00+00:00"
    assert cve.weaknesses == ["CWE-20", "CWE-77"]
    assert cve.cpes == [
        "cpe:2.3:o:paloaltonetworks:pan-os:10.2.0:-:*:*:*:*:*:*",
        "cpe:2.3:o:paloaltonetworks:pan-os:11.0.0:-:*:*:*:*:*:*",
    ]


def test_apply_opencve_payload_dedupes_references_by_url():
    cve = Cve(cve_id="CVE-2024-3400")

    _apply_opencve_payload(cve, OPENCVE_PAYLOAD)

    # 3 raw references, 2 unique URLs — the duplicate's tags still merge in.
    assert len(cve.references) == 2
    advisory = next(r for r in cve.references if r["url"] == "https://security.paloaltonetworks.com/CVE-2024-3400")
    assert advisory["tags"] == ["Vendor Advisory"]


def test_apply_opencve_payload_without_kev_data():
    cve = Cve(cve_id="CVE-2026-1")
    payload = {**OPENCVE_PAYLOAD, "metrics": {**OPENCVE_PAYLOAD["metrics"], "kev": {"data": None, "provider": None}}}

    _apply_opencve_payload(cve, payload)

    assert cve.in_kev is False
    assert cve.kev_date_added is None


def test_extracts_and_dedupes_cve_ids():
    from app.enrichment.cve_extractor import _CVE_PATTERN

    item = Item(
        title="CISA voegt CVE-2026-31337 toe aan KEV",
        extracted_text="Zie ook cve-2026-31337 en CVE-2026-29844 voor meer details.",
    )

    found = sorted({m.upper() for m in _CVE_PATTERN.findall(" ".join([item.title, item.extracted_text]))})
    assert found == ["CVE-2026-29844", "CVE-2026-31337"]


def test_match_fields_maps_to_cve_id_field():
    data = {"cve_ids": ["CVE-2026-31337"]}
    assert CveExtractor().match_fields(data) == {"cve_id": ["CVE-2026-31337"]}
