import json
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from stats import correlation  # noqa: E402


def test_pearson_r_is_one_for_perfect_positive_linear_relationship():
    xs, ys = [1, 2, 3, 4], [2, 4, 6, 8]
    assert correlation.pearson_r(xs, ys) == pytest.approx(1.0)


def test_pearson_r_is_negative_one_for_perfect_negative_linear_relationship():
    xs, ys = [1, 2, 3, 4], [8, 6, 4, 2]
    assert correlation.pearson_r(xs, ys) == pytest.approx(-1.0)


def test_pearson_r_returns_none_when_y_is_constant():
    xs, ys = [1, 2, 3, 4], [5, 5, 5, 5]
    assert correlation.pearson_r(xs, ys) is None


def test_pearson_r_returns_none_when_series_lengths_differ():
    assert correlation.pearson_r([1, 2, 3], [1, 2]) is None


def test_linear_regression_recovers_known_slope_and_intercept():
    xs, ys = [1, 2, 3, 4], [3, 5, 7, 9]  # y = 1 + 2x
    result = correlation.linear_regression(xs, ys)
    assert result["slope"] == pytest.approx(2.0)
    assert result["intercept"] == pytest.approx(1.0)


def test_linear_regression_returns_none_when_x_is_constant():
    xs, ys = [3, 3, 3], [1, 2, 3]
    assert correlation.linear_regression(xs, ys) is None


def test_correlation_significance_flags_significant_for_strong_r_with_enough_n():
    result = correlation.correlation_significance(r=0.6, n=20)
    assert result["significant"] is True
    assert result["p_value"] < 0.01


def test_correlation_significance_flags_not_significant_for_weak_r_with_small_n():
    result = correlation.correlation_significance(r=0.1, n=10)
    assert result["significant"] is False
    assert result["p_value"] > 0.5


def test_correlation_significance_returns_none_for_too_few_points():
    assert correlation.correlation_significance(r=0.9, n=3) is None


def test_correlation_significance_z_is_json_safe_at_perfect_correlation():
    # r=1.0 faria z_stat=atanh(1)=inf antes do fix; json.dumps(inf) produz
    # o token nao-padrao `Infinity`, que JS JSON.parse() rejeita no browser.
    result = correlation.correlation_significance(r=1.0, n=10)
    assert result["z"] is None
    assert result["p_value"] == 0.0
    assert result["significant"] is True

    round_tripped = json.loads(json.dumps(result))
    assert round_tripped["z"] is None
    assert "Infinity" not in json.dumps(result)
