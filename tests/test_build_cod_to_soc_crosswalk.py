import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from build_cod_to_soc_crosswalk import build_crosswalk  # noqa: E402


def _cod_estrutura(subgrupos, grupo_base_to_subgrupo):
    return {"subgrupos": subgrupos, "grupo_base_to_subgrupo": grupo_base_to_subgrupo}


def test_chains_isco_soc2010_and_soc2010_soc2018_crosswalks():
    cod_estrutura = _cod_estrutura(
        subgrupos={"251": {"name": "Desenvolvedores de software"}},
        grupo_base_to_subgrupo={"2511": "251"},
    )
    isco_to_soc2010 = {"2511": {"15-1131", "15-1132"}}
    soc2010_to_soc2018 = {"15-1131": {"15-1251"}, "15-1132": {"15-1252"}}

    result = build_crosswalk(cod_estrutura, isco_to_soc2010, soc2010_to_soc2018)

    assert result["251"]["soc_codes"] == ["15-1251", "15-1252"]
    assert result["251"]["source"] == "isco08-soc2010-soc2018-bls-crosswalk"
    assert result["251"]["mapping_note"] is None


def test_aggregates_multiple_grupo_base_children_of_one_subgrupo():
    cod_estrutura = _cod_estrutura(
        subgrupos={"911": {"name": "Trabalhadores domésticos"}},
        grupo_base_to_subgrupo={"9111": "911", "9112": "911"},
    )
    isco_to_soc2010 = {"9111": {"37-2011"}, "9112": {"37-2012"}}
    soc2010_to_soc2018 = {"37-2011": {"37-2011"}, "37-2012": {"37-2012"}}

    result = build_crosswalk(cod_estrutura, isco_to_soc2010, soc2010_to_soc2018)

    assert result["911"]["soc_codes"] == ["37-2011", "37-2012"]


def test_manual_override_applies_regardless_of_crosswalk_data():
    cod_estrutura = _cod_estrutura(
        subgrupos={"41": {"name": "Policiais militares"}},
        grupo_base_to_subgrupo={},  # no grupo_base maps to 41 at all
    )

    result = build_crosswalk(cod_estrutura, isco_to_soc2010={}, soc2010_to_soc2018={})

    assert result["41"]["soc_codes"] == ["33-3051"]
    assert result["41"]["source"] == "manual-override"
    assert "policiamento" in result["41"]["mapping_note"]


def test_raises_when_soc2010_code_has_no_soc2018_mapping():
    cod_estrutura = _cod_estrutura(
        subgrupos={"999": {"name": "Ocupação de teste"}},
        grupo_base_to_subgrupo={"9991": "999"},
    )
    isco_to_soc2010 = {"9991": {"00-0000"}}  # a SOC2010 code with no SOC2018 mapping below

    with pytest.raises(ValueError, match="no SOC2018"):
        build_crosswalk(cod_estrutura, isco_to_soc2010, soc2010_to_soc2018={})


def test_raises_when_no_crosswalk_coverage_and_no_manual_override():
    cod_estrutura = _cod_estrutura(
        subgrupos={"999": {"name": "Ocupação de teste"}},
        grupo_base_to_subgrupo={},  # no grupo_base maps to this subgrupo
    )

    with pytest.raises(ValueError, match="no SOC mapping"):
        build_crosswalk(cod_estrutura, isco_to_soc2010={}, soc2010_to_soc2018={})
