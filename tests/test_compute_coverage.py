"""Testes da cobertura de exposicao (scripts/compute_coverage.py).

Validacoes do PRODUCT.md: cobertura em [0,1]; exposicao null nunca vira zero
(fica fora do numerador, permanece no denominador); 27 UFs presentes.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from compute_coverage import compute_coverage  # noqa: E402


ALL_UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
]


def _fixture():
    """SP e MG: tres ocupacoes com score + forcas armadas (null).

    SP: coberto 4000 (111+211+522), total 4500 -> 8/9
    MG: coberto 3000, total 3100 -> 30/31
    Nacional: coberto 7000, total 7600 -> 35/38
    """
    scores = {"111": 8.0, "211": 6.0, "522": 1.0, "999": None}
    by_uf = {
        "SP": {"111": 1000.0, "211": 1000.0, "522": 2000.0, "999": 500.0},
        "MG": {"111": 200.0, "211": 400.0, "522": 2400.0, "999": 100.0},
    }
    return by_uf, scores


def test_coverage_hand_computed_values():
    by_uf, scores = _fixture()
    result = compute_coverage(by_uf, scores)

    sp = result["ufs"]["SP"]
    assert sp["covered_employment"] == 4000
    assert sp["eligible_employment"] == 4500
    assert sp["uncovered_employment"] == 500
    assert sp["coverage_rate"] == pytest.approx(4000 / 4500)

    mg = result["ufs"]["MG"]
    assert mg["coverage_rate"] == pytest.approx(3000 / 3100)

    br = result["brazil"]
    assert br["covered_employment"] == 7000
    assert br["eligible_employment"] == 7600
    assert br["coverage_rate"] == pytest.approx(7000 / 7600)


def test_coverage_bounded_zero_one():
    by_uf, scores = _fixture()
    result = compute_coverage(by_uf, scores)
    assert result["validation"]["coverage_bounded_0_1"] is True
    for v in result["ufs"].values():
        assert v["coverage_rate"] is not None
        assert 0.0 <= v["coverage_rate"] <= 1.0


def test_null_exposure_never_zero_in_numerator():
    """A ocupacao null (999) entra no denominador (elegivel) mas nao no
    numerador — diferenca coberto vs elegivel e exatamente o peso dela."""
    by_uf, scores = _fixture()
    result = compute_coverage(by_uf, scores)
    for uf, occs in by_uf.items():
        out = result["ufs"][uf]
        assert out["uncovered_employment"] == round(occs["999"])
        assert out["eligible_employment"] - out["covered_employment"] == round(occs["999"])


def test_all_null_state_has_zero_coverage_not_crash():
    scores = {"111": 8.0, "999": None}
    by_uf = {
        "SP": {"111": 100.0, "999": 10.0},
        "RR": {"999": 50.0},  # UF inteira sem cobertura
    }
    result = compute_coverage(by_uf, scores)
    assert result["ufs"]["RR"]["coverage_rate"] == 0.0
    assert result["ufs"]["RR"]["covered_employment"] == 0
    assert result["ufs"]["RR"]["eligible_employment"] == 50
    assert result["validation"]["coverage_bounded_0_1"] is True


def test_all_27_ufs_present():
    by_uf, scores = _fixture()
    full = {uf: dict(by_uf["SP"]) for uf in ALL_UFS}
    result = compute_coverage(full, scores)
    assert set(result["ufs"].keys()) == set(ALL_UFS)
    assert result["validation"]["n_ufs"] == 27


def test_suppressed_cells_included():
    """Regra #3: celulas que o detalhe publico suprimiria (peso pequeno)
    entram normalmente na cobertura — a funcao recebe pesos completos."""
    scores = {"111": 8.0, "522": 1.0, "999": None}
    by_uf = {"AC": {"111": 5_000_000.0, "522": 3.0, "999": 2.0}}  # 522/999 seriam suprimidas
    result = compute_coverage(by_uf, scores)
    ac = result["ufs"]["AC"]
    assert ac["covered_employment"] == 5_000_003  # 522 (coberta, minúscula) conta
    assert ac["eligible_employment"] == 5_000_005
    assert ac["coverage_rate"] == pytest.approx(5_000_003 / 5_000_005)


def test_deterministic_uf_ordering():
    by_uf, scores = _fixture()
    result = compute_coverage(by_uf, scores)
    assert list(result["ufs"].keys()) == sorted(result["ufs"].keys())
