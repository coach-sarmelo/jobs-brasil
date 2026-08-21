import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from stats import weighted  # noqa: E402


def test_weighted_mean_divides_weighted_sum_by_weight_total():
    assert weighted.weighted_mean(w_sum=10.0, wsum_x=1000.0) == 100.0


def test_weighted_mean_returns_none_when_weight_is_zero():
    assert weighted.weighted_mean(w_sum=0.0, wsum_x=0.0) is None


def test_weighted_variance_matches_population_variance_when_unweighted():
    # x = [2, 4, 6, 8], peso 1 cada -> variancia populacional conhecida = 5.0
    w_sum, wsum_x, wsum_x_sq = 4.0, 20.0, 120.0
    assert weighted.weighted_variance(w_sum, wsum_x, wsum_x_sq) == 5.0


def test_effective_n_equals_raw_count_when_weights_are_equal():
    # 5 itens, peso 2 cada -> n_eff deve coincidir com n=5 (pesos uniformes)
    w_sum, w_sq_sum = 10.0, 5 * 2.0 ** 2
    assert weighted.effective_n(w_sum, w_sq_sum) == 5.0


def test_effective_n_shrinks_when_one_weight_dominates():
    # 4 unidades de peso 1 + 1 unidade de peso 96 -> n_eff bem menor que n=5,
    # refletindo que quase toda a informacao amostral vem de uma unica linha.
    w_sum = 4 * 1.0 + 96.0
    w_sq_sum = 4 * 1.0 ** 2 + 96.0 ** 2
    n_eff = weighted.effective_n(w_sum, w_sq_sum)
    assert n_eff < 2.0


def test_standard_error_mean_uses_kish_effective_n():
    # Mesmos dados do teste de variancia: variancia=5, n_eff=4 -> SE=sqrt(5/4)
    w_sum, wsum_x, wsum_x_sq = 4.0, 20.0, 120.0
    w_sq_sum = 4.0  # peso 1 cada, 4 itens
    se = weighted.standard_error_mean(w_sum, wsum_x, wsum_x_sq, w_sq_sum)
    assert se == pytest.approx(math.sqrt(1.25))


def test_weighted_proportion_divides_matching_weight_by_total():
    assert weighted.weighted_proportion(w_sum=200.0, w_numerator=50.0) == 0.25


def test_standard_error_proportion_uses_bernoulli_variance_over_effective_n():
    # p=0.25, n_eff=100 (peso 1 cada, 100 itens) -> SE = sqrt(0.25*0.75/100)
    w_sum, w_numerator, w_sq_sum = 100.0, 25.0, 100.0
    se = weighted.standard_error_proportion(w_sum, w_numerator, w_sq_sum)
    assert se == pytest.approx(math.sqrt(0.25 * 0.75 / 100))


def test_ci_95_brackets_estimate_by_1_96_standard_errors():
    lower, upper = weighted.ci_95(estimate=10.0, se=2.0)
    assert lower == pytest.approx(10.0 - 1.959963984540054 * 2.0)
    assert upper == pytest.approx(10.0 + 1.959963984540054 * 2.0)


def test_ci_95_returns_none_when_estimate_or_se_missing():
    assert weighted.ci_95(None, 2.0) is None
    assert weighted.ci_95(10.0, None) is None
