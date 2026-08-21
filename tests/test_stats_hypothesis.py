import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from stats import hypothesis  # noqa: E402


def test_normal_cdf_at_zero_is_one_half():
    assert hypothesis.normal_cdf(0.0) == pytest.approx(0.5)


def test_normal_cdf_at_1_96_is_approximately_0_975():
    assert hypothesis.normal_cdf(1.959963984540054) == pytest.approx(0.975, abs=1e-6)


def test_two_sided_p_value_at_z_zero_is_one():
    assert hypothesis.two_sided_p_value(0.0) == pytest.approx(1.0)


def test_two_sided_p_value_at_z_1_96_is_approximately_0_05():
    assert hypothesis.two_sided_p_value(1.959963984540054) == pytest.approx(0.05, abs=1e-6)


def test_z_test_diff_flags_significant_when_difference_is_large_relative_to_se():
    # medias bem separadas (10 vs 5) com SE pequeno (0.1 cada) -> z grande, p ~0
    result = hypothesis.z_test_diff(mean_a=10.0, se_a=0.1, mean_b=5.0, se_b=0.1)
    assert result["z"] == pytest.approx(5.0 / math.sqrt(0.02))
    assert result["p_value"] < 0.001
    assert result["significant"] is True


def test_z_test_diff_flags_not_significant_when_difference_is_within_noise():
    # medias quase iguais com SE grande -> z pequeno, p alto, nao significativo
    result = hypothesis.z_test_diff(mean_a=10.0, se_a=5.0, mean_b=9.0, se_b=5.0)
    assert result["significant"] is False
    assert result["p_value"] > 0.05


def test_z_test_diff_returns_none_when_any_input_is_missing():
    assert hypothesis.z_test_diff(None, 0.1, 5.0, 0.1) is None
    assert hypothesis.z_test_diff(10.0, None, 5.0, 0.1) is None


def test_z_test_diff_respects_custom_alpha():
    # z ~= 1.6444 -> p ~= 0.10: nao significativo a 5%, significativo a 20%.
    result_default = hypothesis.z_test_diff(mean_a=10.0, se_a=4.3, mean_b=0.0, se_b=4.3)
    result_loose = hypothesis.z_test_diff(mean_a=10.0, se_a=4.3, mean_b=0.0, se_b=4.3, alpha=0.20)
    assert result_default["significant"] is False
    assert result_loose["significant"] is True
