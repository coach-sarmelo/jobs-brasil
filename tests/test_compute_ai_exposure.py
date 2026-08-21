import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from compute_ai_exposure import (  # noqa: E402
    compute_exposure_for_soc_codes,
    compute_scores,
    index_by_soc_prefix,
    load_employment_by_soc,
    load_onet_data,
)


def test_index_by_soc_prefix_groups_onet_codes_under_their_6_digit_soc():
    onet_ratings = {"15-1252.00": 0.8, "15-1253.00": 0.6, "33-3051.00": 0.25, "33-3051.04": 0.5}

    index = index_by_soc_prefix(onet_ratings)

    assert index["15-1252"] == [("15-1252.00", 0.8)]
    assert set(index["33-3051"]) == {("33-3051.00", 0.25), ("33-3051.04", 0.5)}
    assert "15-1253" in index and "33-3051" in index


def test_weights_across_soc_codes_by_employment():
    # SOC 15-1252 (Software Developers): one O*NET-SOC code, rating 0.8, emp 1000
    # SOC 15-1254 (Web Developers): one O*NET-SOC code, rating 0.4, emp 500
    # Expected weighted mean = (0.8*1000 + 0.4*500) / 1500 = 0.6667 -> *10 = 6.7
    onet_by_soc = index_by_soc_prefix({"15-1252.00": 0.8, "15-1254.00": 0.4})
    employment_by_soc = {"15-1252": 1000.0, "15-1254": 500.0}

    result = compute_exposure_for_soc_codes(
        soc_codes=["15-1252", "15-1254"],
        onet_by_soc=onet_by_soc,
        employment_by_soc=employment_by_soc,
    )

    assert result.exposure == pytest.approx(6.7, abs=0.05)
    assert set(result.onet_soc_codes) == {"15-1252.00", "15-1254.00"}


def test_averages_within_a_soc_code_before_weighting_across():
    # SOC 33-3051 has two O*NET-SOC codes (0.25, 0.5) -> within-SOC avg 0.375, emp 200
    # SOC 11-1011 has one O*NET-SOC code (0.6), emp 100
    # Combined = (0.375*200 + 0.6*100) / 300 = 0.45 -> *10 = 4.5
    onet_by_soc = index_by_soc_prefix({
        "33-3051.00": 0.25,
        "33-3051.04": 0.5,
        "11-1011.00": 0.6,
    })
    employment_by_soc = {"33-3051": 200.0, "11-1011": 100.0}

    result = compute_exposure_for_soc_codes(
        soc_codes=["33-3051", "11-1011"],
        onet_by_soc=onet_by_soc,
        employment_by_soc=employment_by_soc,
    )

    assert result.exposure == pytest.approx(4.5, abs=0.05)


def test_falls_back_to_unweighted_average_when_employment_missing():
    onet_by_soc = index_by_soc_prefix({"15-1252.00": 0.8, "15-1254.00": 0.4})
    employment_by_soc = {}  # no employment data available for either

    result = compute_exposure_for_soc_codes(
        soc_codes=["15-1252", "15-1254"],
        onet_by_soc=onet_by_soc,
        employment_by_soc=employment_by_soc,
    )

    assert result.exposure == pytest.approx(6.0, abs=0.05)  # (0.8+0.4)/2 * 10


def test_returns_none_when_no_onet_ratings_available():
    result = compute_exposure_for_soc_codes(
        soc_codes=["55-1011", "55-1012"],  # military occupations, not in Eloundou data
        onet_by_soc={},
        employment_by_soc={"55-1011": 500.0},
    )

    assert result is None


def test_exposure_is_rescaled_from_0_1_to_0_10_and_rounded():
    onet_by_soc = index_by_soc_prefix({"15-1252.00": 0.86842105})
    employment_by_soc = {"15-1252": 100.0}

    result = compute_exposure_for_soc_codes(
        soc_codes=["15-1252"],
        onet_by_soc=onet_by_soc,
        employment_by_soc=employment_by_soc,
    )

    assert result.exposure == 8.7


def test_load_onet_data_reads_ratings_and_titles_from_one_csv(tmp_path):
    csv_path = tmp_path / "occ_level.csv"
    csv_path.write_text(
        "O*NET-SOC Code,Title,dv_rating_alpha,dv_rating_beta,dv_rating_gamma\n"
        "15-1252.00,Software Developers,0.5,0.8,0.9\n"
        "33-2011.00,Firefighters,0.05,0.14,0.2\n",
        encoding="utf-8",
    )

    ratings, titles = load_onet_data(str(csv_path))

    assert ratings == {"15-1252.00": 0.8, "33-2011.00": 0.14}
    assert titles == {"15-1252.00": "Software Developers", "33-2011.00": "Firefighters"}


def test_load_employment_by_soc_skips_non_detailed_and_suppressed_rows(tmp_path):
    csv_path = tmp_path / "national_May2021_dl.csv"
    csv_path.write_text(
        "OCC_CODE,OCC_TITLE,O_GROUP,TOT_EMP\n"
        "11-0000,Management Occupations,major,8909910\n"  # aggregate row, must be excluded
        '15-1252,Software Developers,detailed,"1,847,900"\n'  # comma-formatted, must parse
        "39-9099,Personal Care Workers All Other,detailed,**\n"  # suppressed, must be skipped
        "13-1082,Project Management Specialists,detailed,\n",  # empty, must be skipped
        encoding="utf-8",
    )

    employment = load_employment_by_soc(str(csv_path))

    assert employment == {"15-1252": 1847900.0}


def test_compute_scores_includes_onet_soc_titles_for_the_methodology_page():
    subgroups = [{"code": "251", "name": "Desenvolvedores de software"}]
    cod_to_soc = {"251": {"soc_codes": ["15-1252"], "mapping_note": None}}
    onet_ratings = {"15-1252.00": 0.8}
    onet_titles = {"15-1252.00": "Software Developers"}
    employment_by_soc = {"15-1252": 100.0}

    scores = compute_scores(subgroups, cod_to_soc, onet_ratings, onet_titles, employment_by_soc)

    assert scores["251"]["onet_soc_titles"] == ["Software Developers"]


def test_compute_scores_onet_soc_titles_is_empty_when_exposure_is_null():
    subgroups = [{"code": "11", "name": "Oficiais das forças armadas"}]
    cod_to_soc = {"11": {"soc_codes": ["55-1011"], "mapping_note": None}}

    scores = compute_scores(subgroups, cod_to_soc, onet_ratings={}, onet_titles={}, employment_by_soc={})

    assert scores["11"]["exposure"] is None
    assert scores["11"]["onet_soc_titles"] == []
