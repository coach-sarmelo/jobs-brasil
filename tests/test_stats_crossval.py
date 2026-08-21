"""Valida scripts/stats/*.py contra scipy.stats/statsmodels — ver SPEC.md
seção 5 ("verificados uma vez contra scipy.stats"). Opt-in via
`pytest tests/ -m crossval` (requer requirements-dev.txt); pulado
automaticamente (não falha) quando scipy/statsmodels não estão instalados,
como em CI/produção.
"""
import math
import os
import sys

import pytest

scipy_stats = pytest.importorskip("scipy.stats")
sm_weightstats = pytest.importorskip("statsmodels.stats.weightstats")
sm_proportion = pytest.importorskip("statsmodels.stats.proportion")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from stats import correlation, hypothesis, weighted  # noqa: E402

pytestmark = pytest.mark.crossval

SAMPLE_A = [10.0, 12.0, 9.0, 15.0, 11.0, 13.0, 8.0, 14.0, 10.0, 12.5]
SAMPLE_B = [x - 3.0 for x in SAMPLE_A]


def _unit_weight_sufficient_stats(xs):
    """Soma de pesos == n quando cada observação tem peso 1 (caso não ponderado)."""
    w_sum = float(len(xs))
    wsum_x = sum(xs)
    wsum_x_sq = sum(x ** 2 for x in xs)
    return w_sum, wsum_x, wsum_x_sq, w_sum


def test_z95_matches_scipy_norm_ppf():
    assert weighted.Z_95 == pytest.approx(scipy_stats.norm.ppf(0.975), abs=1e-9)


def test_weighted_mean_and_variance_match_unweighted_reference():
    w_sum, wsum_x, wsum_x_sq, w_sq_sum = _unit_weight_sufficient_stats(SAMPLE_A)

    assert weighted.weighted_mean(w_sum, wsum_x) == pytest.approx(sum(SAMPLE_A) / len(SAMPLE_A))
    assert weighted.weighted_variance(w_sum, wsum_x, wsum_x_sq) == pytest.approx(
        sum((x - sum(SAMPLE_A) / len(SAMPLE_A)) ** 2 for x in SAMPLE_A) / len(SAMPLE_A)
    )


def test_standard_error_mean_matches_scipy_sem_for_unit_weights():
    # scipy.stats.sem(ddof=0) usa variância populacional dividida por n — a
    # mesma convenção de weighted.py (sem correção de Bessel), então é a
    # comparação correta aqui (statsmodels.DescrStatsW.std_mean usa n-1 no
    # denominador independentemente do ddof passado, o que não é comparável).
    w_sum, wsum_x, wsum_x_sq, w_sq_sum = _unit_weight_sufficient_stats(SAMPLE_A)
    se = weighted.standard_error_mean(w_sum, wsum_x, wsum_x_sq, w_sq_sum)

    assert se == pytest.approx(scipy_stats.sem(SAMPLE_A, ddof=0))


def test_weighted_proportion_ci_matches_statsmodels_normal_method():
    count, nobs = 42, 150
    p = weighted.weighted_proportion(float(nobs), float(count))
    se = weighted.standard_error_proportion(float(nobs), float(count), float(nobs))
    ours = weighted.ci_95(p, se)

    theirs = sm_proportion.proportion_confint(count, nobs, alpha=0.05, method="normal")
    assert ours[0] == pytest.approx(theirs[0])
    assert ours[1] == pytest.approx(theirs[1])


def test_normal_cdf_matches_scipy():
    for z in (-2.5, -1.0, 0.0, 0.5, 1.96, 3.1):
        assert hypothesis.normal_cdf(z) == pytest.approx(scipy_stats.norm.cdf(z))


def test_two_sided_p_value_matches_scipy_norm_sf():
    for z in (0.1, 1.0, 1.96, 2.58, 4.0):
        assert hypothesis.two_sided_p_value(z) == pytest.approx(2 * scipy_stats.norm.sf(abs(z)))


def test_z_test_diff_matches_statsmodels_ztest_unequal_variance():
    w_sum_a, wsum_a, wsum_a_sq, wsq_a = _unit_weight_sufficient_stats(SAMPLE_A)
    w_sum_b, wsum_b, wsum_b_sq, wsq_b = _unit_weight_sufficient_stats(SAMPLE_B)
    mean_a = weighted.weighted_mean(w_sum_a, wsum_a)
    se_a = weighted.standard_error_mean(w_sum_a, wsum_a, wsum_a_sq, wsq_a)
    mean_b = weighted.weighted_mean(w_sum_b, wsum_b)
    se_b = weighted.standard_error_mean(w_sum_b, wsum_b, wsum_b_sq, wsq_b)

    ours = hypothesis.z_test_diff(mean_a, se_a, mean_b, se_b)
    # ddof=0: casa com a convenção de variância populacional de weighted.py
    # (o default ddof=1 do statsmodels aplicaria correção de Bessel, que
    # z_test_diff não usa).
    z_stat, p_value = sm_weightstats.ztest(SAMPLE_A, SAMPLE_B, usevar="unequal", ddof=0)
    assert ours["z"] == pytest.approx(z_stat)
    assert ours["p_value"] == pytest.approx(p_value)


def test_pearson_r_matches_scipy():
    xs = [1, 2, 3, 4, 5, 6, 7]
    ys = [2, 1, 4, 3, 6, 5, 8]
    assert correlation.pearson_r(xs, ys) == pytest.approx(scipy_stats.pearsonr(xs, ys).statistic)


def test_linear_regression_matches_scipy_linregress():
    xs = [1, 2, 3, 4, 5, 6, 7]
    ys = [2, 1, 4, 3, 6, 5, 8]
    ours = correlation.linear_regression(xs, ys)
    theirs = scipy_stats.linregress(xs, ys)
    assert ours["slope"] == pytest.approx(theirs.slope)
    assert ours["intercept"] == pytest.approx(theirs.intercept)


def test_correlation_significance_z_matches_fisher_transform_reference():
    # Formula de referência (Fisher, 1921) recalculada de forma independente
    # (math.atanh, não hypothesis.normal_cdf) e comparada ao p-valor via
    # scipy.stats.norm — cross-validação do resultado combinado de
    # correlation.py + hypothesis.py, já que nem scipy nem statsmodels
    # expõem o teste de significância de r por transformação z de Fisher
    # como função standalone.
    r, n = 0.6, 20
    ours = correlation.correlation_significance(r, n)

    z_reference = math.atanh(r) * math.sqrt(n - 3)
    p_reference = 2 * scipy_stats.norm.sf(abs(z_reference))
    assert ours["z"] == pytest.approx(z_reference)
    assert ours["p_value"] == pytest.approx(p_reference)
