import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

import compute_statistics as cs  # noqa: E402
from stats import weighted  # noqa: E402

Z_95 = 1.959963984540054


def _occupation(**overrides):
    base = {
        "code": "111",
        "name": "Ocupação Teste",
        "section": "Seção Teste",
        "informality_rate": 20.0,
        "gender_gap_pct": 10.0,
        "race_gap_pct": 5.0,
        "income_weight_sum": 100.0,
        "wage_bill": 300000.0,
        "income_sq_weighted_sum": 925000000.0,
        "weight_sq_sum": 100.0,
        "male_avg_income": 3200.0,
        "male_income_weight_sum": 60.0,
        "male_income_sq_weighted_sum": 650000000.0,
        "female_avg_income": 2800.0,
        "female_income_weight_sum": 40.0,
        "female_income_sq_weighted_sum": 320000000.0,
        "white_avg_income": 3300.0,
        "white_income_weight_sum": 55.0,
        "white_income_sq_weighted_sum": 610000000.0,
        "black_avg_income": 2900.0,
        "black_income_weight_sum": 45.0,
        "black_income_sq_weighted_sum": 390000000.0,
        "informal_weight_sum": 100.0,
        "informal_weight_numerator": 20.0,
        "avg_income": 3112.04,
    }
    base.update(overrides)
    return base


def test_income_ci_returns_none_when_weight_sum_missing():
    assert cs.income_ci(_occupation(income_weight_sum=None)) is None


def test_income_ci_matches_manual_weighted_mean_and_ci():
    item = _occupation()
    result = cs.income_ci(item)

    mean = weighted.weighted_mean(item["income_weight_sum"], item["wage_bill"])
    se = weighted.standard_error_mean(
        item["income_weight_sum"], item["wage_bill"], item["income_sq_weighted_sum"], item["weight_sq_sum"]
    )
    assert result["estimate"] == pytest.approx(mean, abs=0.01)
    assert result["se"] == pytest.approx(se, abs=0.01)
    assert result["ci_low"] == pytest.approx(mean - Z_95 * se, abs=0.01)
    assert result["ci_high"] == pytest.approx(mean + Z_95 * se, abs=0.01)


def test_informality_ci_is_scaled_to_percentage_points():
    item = _occupation()
    result = cs.informality_ci(item)

    p = weighted.weighted_proportion(item["informal_weight_sum"], item["informal_weight_numerator"])
    assert result["estimate"] == pytest.approx(p * 100, abs=0.1)
    assert 0 <= result["ci_low"] <= result["estimate"] <= result["ci_high"] <= 100


def test_informality_ci_returns_none_when_numerator_missing():
    assert cs.informality_ci(_occupation(informal_weight_sum=None, informal_weight_numerator=None)) is None


def test_gender_gap_significance_flags_large_gap_as_significant():
    item = _occupation(male_avg_income=6000.0, female_avg_income=2000.0)
    result = cs.gender_gap_significance(item)

    assert result is not None
    assert result["z"] > 0
    assert result["significant"] is True


def test_gender_gap_significance_none_when_subgroup_data_missing():
    item = _occupation(male_income_weight_sum=None)
    assert cs.gender_gap_significance(item) is None


def test_race_gap_significance_returns_z_test_block():
    item = _occupation()
    result = cs.race_gap_significance(item)

    assert result is not None
    assert set(result) == {"z", "p_value", "significant"}


def test_compute_occupation_statistics_includes_all_available_blocks():
    stats = cs.compute_occupation_statistics(_occupation())

    assert set(stats) == {"income_ci", "informality_ci", "gender_gap_significance", "race_gap_significance"}


def test_compute_occupation_statistics_returns_none_when_nothing_computable():
    sparse = {"code": "999", "name": "Sem dados"}
    assert cs.compute_occupation_statistics(sparse) is None


def test_cross_occupation_correlations_empty_below_minimum_n():
    subgroups = [_occupation(code=str(i), informality_rate=10.0 + i) for i in range(3)]
    scores = {str(i): {"exposure": 5.0 + i} for i in range(3)}

    assert cs.cross_occupation_correlations(subgroups, scores) == {}


def test_cross_occupation_correlations_computes_perfect_positive_correlation():
    subgroups = [_occupation(code=str(i), informality_rate=float(10 + i)) for i in range(5)]
    scores = {str(i): {"exposure": float(i)} for i in range(5)}

    result = cs.cross_occupation_correlations(subgroups, scores)

    assert result["disclaimer"] == cs.CAUSAL_DISCLAIMER
    pair = result["pairs"]["ai_exposure_vs_informality"]
    assert pair["r"] == pytest.approx(1.0)
    assert pair["n"] == 5
    assert pair["significance"]["significant"] is True
    assert pair["regression"]["slope"] == pytest.approx(1.0)


def test_correlation_fields_includes_income_pair_mapped_to_avg_income():
    assert cs.CORRELATION_FIELDS["ai_exposure_vs_income"] == "avg_income"


def test_cross_occupation_correlations_computes_income_pair_as_income_over_exposure():
    incomes = [1000.0, 2000.0, 3000.0, 4000.0, 5000.0]
    exposures = [0.0, 0.0, 2.0, 1.0, 3.0]
    subgroups = [_occupation(code=str(i), avg_income=incomes[i]) for i in range(5)]
    scores = {str(i): {"exposure": exposures[i]} for i in range(5)}

    result = cs.cross_occupation_correlations(subgroups, scores)

    pair = result["pairs"]["ai_exposure_vs_income"]
    assert pair["r"] == pytest.approx(7000 / math.sqrt(10_000_000 * 6.8), abs=0.0001)
    assert pair["n"] == 5
    # Mesma convenção dos demais pares: métrica (renda) regredida sobre
    # exposição — slope em R$ por ponto de exposição.
    assert pair["regression"]["slope"] == pytest.approx(7000 / 6.8)
    assert pair["regression"]["intercept"] == pytest.approx(12000 / 6.8)


def test_cross_occupation_correlations_skips_occupations_without_scores():
    subgroups = [_occupation(code=str(i), informality_rate=float(10 + i)) for i in range(5)]
    scores = {str(i): {"exposure": float(i)} for i in range(3)}  # only 3 have scores

    assert cs.cross_occupation_correlations(subgroups, scores) == {}


def test_compute_statistics_combines_per_occupation_and_correlations():
    subgroups = [_occupation(code=str(i), informality_rate=float(10 + i)) for i in range(5)]
    scores = {str(i): {"exposure": float(i)} for i in range(5)}

    result = cs.compute_statistics(subgroups, scores)

    assert set(result) == {"per_occupation", "correlations"}
    assert len(result["per_occupation"]) == 5
    assert "ai_exposure_vs_informality" in result["correlations"]["pairs"]


def test_load_json_raises_when_required_file_missing(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        cs.load_json(str(missing))


def test_load_json_returns_default_when_optional_file_missing(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    assert cs.load_json(str(missing), default={}) == {}
