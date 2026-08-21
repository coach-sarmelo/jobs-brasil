"""Testes da decomposicao exata por composicao (scripts/compute_decomposition.py).

Fixtures sinteticas com valores calculados a mao verificam as validacoes #1-4
do PRODUCT.md: 27 UFs presentes, identidade sum_j C_js = E_s - E_BR,
reconciliacao nacional e exclusao de exposicao null das participacoes.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from compute_decomposition import TOLERANCE, decompose  # noqa: E402


ALL_UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
]

SUBGRUPOS = {
    "111": {"name": "Dirigentes", "grande_grupo": "DIRETORES E GERENTES"},
    "211": {"name": "Profissionais de TI", "grande_grupo": "PROFISSIONAIS DAS CIENCIAS E INTELECTUAIS"},
    "522": {"name": "Vendedores", "grande_grupo": "TRABALHADORES DOS SERVICOS"},
    "999": {"name": "Forcas armadas", "grande_grupo": "MEMBROS DAS FORCAS ARMADAS"},
}


def _fixture_two_states():
    """Duas UFs, tres ocupacoes com score + uma null (forcas armadas).

    Construido para ser verificavel a mao:
    - theta = {"111": 8.0, "211": 6.0, "522": 1.0, "999": None}
    - SP: 111->1000, 211->1000, 522->2000, 999->500  (coberto = 4000)
    - MG: 111->200,  211->400,  522->2400, 999->100   (coberto = 3000)
    """
    scores = {"111": 8.0, "211": 6.0, "522": 1.0, "999": None}
    by_uf = {
        "SP": {"111": 1000.0, "211": 1000.0, "522": 2000.0, "999": 500.0},
        "MG": {"111": 200.0, "211": 400.0, "522": 2400.0, "999": 100.0},
    }
    return by_uf, scores


def _expected_hand_values():
    """Valores exatos derivados a mao para o fixture acima."""
    # Emprego coberto nacional por ocupacao: 111=1200, 211=1400, 522=4400; total 7000
    # E_BR = (1200*8 + 1400*6 + 4400*1)/7000 = 22400/7000 = 3.2
    e_br = 22400 / 7000
    p_br = {"111": 1200 / 7000, "211": 1400 / 7000, "522": 4400 / 7000}
    # SP: E_SP = (1000*8 + 1000*6 + 2000*1)/4000 = 16000/4000 = 4.0
    e_sp = 4.0
    p_sp = {"111": 0.25, "211": 0.25, "522": 0.5}
    # MG: E_MG = (200*8 + 400*6 + 2400*1)/3000 = 6400/3000
    e_mg = 6400 / 3000
    p_mg = {"111": 200 / 3000, "211": 400 / 3000, "522": 2400 / 3000}
    thetas = {"111": 8.0, "211": 6.0, "522": 1.0}
    contribs_sp = {c: (p_sp[c] - p_br[c]) * (thetas[c] - e_br) for c in p_sp}
    contribs_mg = {c: (p_mg[c] - p_br[c]) * (thetas[c] - e_br) for c in p_mg}
    return e_br, e_sp, e_mg, contribs_sp, contribs_mg


def test_identity_contributions_sum_to_gap():
    by_uf, scores = _fixture_two_states()
    result = decompose(by_uf, scores, SUBGRUPOS)
    for uf, block in result["ufs"].items():
        total = sum(c["contribution"] for c in block["contributions_by_occupation"])
        assert total == pytest.approx(block["gap"], abs=1e-12)
        assert block["residual"] == pytest.approx(0.0, abs=1e-12)
    assert result["validation"]["max_identity_residual"] <= TOLERANCE


def test_hand_computed_values_match():
    by_uf, scores = _fixture_two_states()
    result = decompose(by_uf, scores, SUBGRUPOS)
    e_br, e_sp, e_mg, contribs_sp, contribs_mg = _expected_hand_values()

    assert result["brazil"]["exposure"] == pytest.approx(e_br)
    assert result["brazil"]["covered_employment"] == 7000
    assert result["brazil"]["total_employment"] == 7600  # inclui null (500+100)
    assert result["ufs"]["SP"]["exposure"] == pytest.approx(e_sp)
    assert result["ufs"]["MG"]["exposure"] == pytest.approx(e_mg)
    assert result["ufs"]["SP"]["gap"] == pytest.approx(e_sp - e_br)
    assert result["ufs"]["MG"]["gap"] == pytest.approx(e_mg - e_br)

    got_sp = {c["code"]: c["contribution"] for c in result["ufs"]["SP"]["contributions_by_occupation"]}
    got_mg = {c["code"]: c["contribution"] for c in result["ufs"]["MG"]["contributions_by_occupation"]}
    for code, expected in contribs_sp.items():
        assert got_sp[code] == pytest.approx(expected), code
    for code, expected in contribs_mg.items():
        assert got_mg[code] == pytest.approx(expected), code


def test_null_exposure_excluded_from_shares_never_zero():
    """Ocupacao com exposure null (999) nao pode aparecer nas contribuicoes
    nem entrar no denominador; total_employment ainda a inclui."""
    by_uf, scores = _fixture_two_states()
    result = decompose(by_uf, scores, SUBGRUPOS)

    for uf in ("SP", "MG"):
        codes = {c["code"] for c in result["ufs"][uf]["contributions_by_occupation"]}
        assert "999" not in codes
        assert result["ufs"][uf]["covered_employment"] == 4000 if uf == "SP" else 3000
        assert result["ufs"][uf]["total_employment"] > result["ufs"][uf]["covered_employment"]
    # nenhuma secao de forcas armadas nas contribuicoes por grupo
    for uf in ("SP", "MG"):
        sections = {g["section"] for g in result["ufs"][uf]["contributions_by_major_group"]}
        assert not any("ARMADAS" in s.upper() for s in sections)


def test_national_reconciliation():
    """Validacao #4: media ponderada das UFs reproduz E_BR."""
    by_uf, scores = _fixture_two_states()
    result = decompose(by_uf, scores, SUBGRUPOS)
    v = result["validation"]
    assert v["national_reconciliation"] == pytest.approx(result["brazil"]["exposure"], abs=1e-12)
    assert v["national_reconciliation_residual"] <= 1e-9
    assert v["shares_sum_to_one_within_tolerance"] is True


def test_major_group_aggregation_sums_to_gap():
    by_uf, scores = _fixture_two_states()
    result = decompose(by_uf, scores, SUBGRUPOS)
    for uf, block in result["ufs"].items():
        total = sum(g["contribution"] for g in block["contributions_by_major_group"])
        assert total == pytest.approx(block["gap"], abs=1e-12)


def test_all_27_ufs_present_synthetic():
    by_uf, scores = _fixture_two_states()
    # replica a UF de SP para todas as 27 (mesma estrutura, gaps identicos)
    full = {uf: dict(by_uf["SP"]) for uf in ALL_UFS}
    result = decompose(full, scores, SUBGRUPOS)
    assert set(result["ufs"].keys()) == set(ALL_UFS)
    assert result["validation"]["n_ufs"] == 27


def test_deterministic_ordering():
    by_uf, scores = _fixture_two_states()
    result = decompose(by_uf, scores, SUBGRUPOS)
    for block in result["ufs"].values():
        contribs = [c["contribution"] for c in block["contributions_by_occupation"]]
        positives = [c for c in contribs if c > 0]
        others = [c for c in contribs if c <= 0]
        # positivas descrescentes; nao-positivas da mais negativa p/ menos negativa
        assert positives == sorted(positives, reverse=True)
        assert others == sorted(others)
        groups = [g["contribution"] for g in block["contributions_by_major_group"]]
        assert groups == sorted(groups, reverse=True)


def test_state_estimates_include_suppressed_cells():
    """Regra #3: celula pequena (seria suprimida no detalhe publico) entra na
    estimativa da UF — o fixture tem células que to_metrics descartaria, e a
    decomposicao deve usa-las mesmo assim (presente no covered_employment)."""
    by_uf, scores = _fixture_two_states()
    result = decompose(by_uf, scores, SUBGRUPOS)
    # MG tem pouquíssimos trabalhadores em 111 (200.0 de peso): qualquer
    # threshold de publicacao independe da decomposicao — aqui entra tudo.
    assert result["ufs"]["MG"]["covered_employment"] == 3000


def test_smoke_real_artifacts():
    """Smoke contra artefatos reais quando o microdado local existe.

    Re-agrega so uma fracao do arquivo (primeiras N linhas) para manter o
    teste rapido; valida formato e identidade, nao os numeros finais.
    """
    micro = os.path.join(os.path.dirname(__file__), "../data/microdata/PNADC_012026.txt")
    if not os.path.exists(micro):
        pytest.skip("microdados 2026 Q1 nao disponiveis localmente")

    from compute_decomposition import load_scores
    from process_microdata import load_reference

    subgrupos, grupo_base_to_subgrupo, uf_codes = load_reference()
    scores, _src = load_scores()

    with open(micro, encoding="latin-1") as f:
        lines = [f.readline() for _ in range(200_000)]

    import io
    national, by_uf, _skipped, _bs, _sa = __import__("process_microdata").aggregate_quarter(
        io.StringIO("".join(lines)), subgrupos, grupo_base_to_subgrupo, uf_codes,
        want_by_uf=True, group_by="subgrupo",
    )
    by_uf_weights = {
        uf: {code: acc.w for code, acc in occs.items()} for uf, occs in by_uf.items()
    }
    # apenas UFs com alguma cobertura de score no trecho
    by_uf_weights = {
        uf: occs for uf, occs in by_uf_weights.items()
        if sum(w for c, w in occs.items() if scores.get(c) is not None) > 0
    }
    if len(by_uf_weights) < 2:
        pytest.skip("amostra pequena demais para o smoke test")

    result = decompose(by_uf_weights, scores, subgrupos)
    v = result["validation"]
    assert v["n_ufs"] == len(by_uf_weights)
    assert v["max_identity_residual"] <= 1e-6
    assert v["national_reconciliation_residual"] <= 1e-6
    for uf, block in result["ufs"].items():
        assert 0 <= block["exposure"] <= 10  # escala 0-10 do indice
