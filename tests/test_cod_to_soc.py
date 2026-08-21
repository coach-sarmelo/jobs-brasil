import json
import os
import re

COD_ESTRUTURA_PATH = os.path.join(os.path.dirname(__file__), "../scripts/reference/cod_estrutura.json")
COD_TO_SOC_PATH = os.path.join(os.path.dirname(__file__), "../scripts/reference/cod_to_soc.json")

SOC_CODE_RE = re.compile(r"^\d{2}-\d{4}$")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_cod_to_soc_covers_every_subgrupo_in_cod_estrutura():
    cod_estrutura = _load(COD_ESTRUTURA_PATH)
    cod_to_soc = _load(COD_TO_SOC_PATH)

    subgrupo_codes = set(cod_estrutura["subgrupos"].keys())
    mapped_codes = set(cod_to_soc.keys())

    assert subgrupo_codes == mapped_codes


def test_every_subgrupo_has_at_least_one_soc_code():
    cod_to_soc = _load(COD_TO_SOC_PATH)

    for cod_code, entry in cod_to_soc.items():
        assert entry["soc_codes"], f"{cod_code} has no soc_codes"


def test_soc_codes_match_expected_format():
    cod_to_soc = _load(COD_TO_SOC_PATH)

    for cod_code, entry in cod_to_soc.items():
        for soc_code in entry["soc_codes"]:
            assert SOC_CODE_RE.match(soc_code), f"{cod_code}: malformed SOC code {soc_code!r}"


def test_manual_overrides_are_documented():
    cod_to_soc = _load(COD_TO_SOC_PATH)

    military_police = cod_to_soc["41"]
    military_firefighters = cod_to_soc["51"]

    assert military_police["source"] == "manual-override"
    assert military_police["mapping_note"]
    assert military_firefighters["source"] == "manual-override"
    assert military_firefighters["mapping_note"]


def test_non_override_entries_are_sourced_from_bls_crosswalk():
    cod_to_soc = _load(COD_TO_SOC_PATH)

    # Spot-check a code known to be covered directly by the BLS crosswalks.
    assert cod_to_soc["212"]["source"] == "isco08-soc2010-soc2018-bls-crosswalk"


def test_software_developers_map_to_the_merged_soc2018_code():
    # Regression check: SOC2010's separate "Software Developers, Applications"
    # (15-1132) and "Systems Software" (15-1133) were merged into a single
    # SOC2018 code, 15-1252. Without chaining through the SOC2010->SOC2018
    # crosswalk, this occupation would silently end up with zero exposure
    # coverage (verified empirically before this fix).
    cod_to_soc = _load(COD_TO_SOC_PATH)
    assert "15-1252" in cod_to_soc["251"]["soc_codes"]
