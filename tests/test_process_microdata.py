import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from process_microdata import Accum  # noqa: E402


def _accum_with(weight=10.0, income=1000.0, sexo="1", raca="1", informal=False, n=20):
    acc = Accum()
    for _ in range(n):
        acc.add(weight, income, sexo, raca, informal)
    return acc


def test_accum_to_metrics_exports_weight_sums_needed_for_weighted_se():
    acc = _accum_with()
    metrics = acc.to_metrics()

    assert metrics is not None
    assert metrics["income_weight_sum"] == pytest.approx(acc.w_income)
    assert metrics["male_income_weight_sum"] == pytest.approx(acc.w_male_income)
    assert metrics["white_income_weight_sum"] == pytest.approx(acc.w_white_income)
    assert metrics["informal_weight_sum"] == pytest.approx(acc.w_informal_known)
    assert metrics["informal_weight_numerator"] == pytest.approx(acc.w_informal)
    # sem observações femininas/pretas nesta amostra: os campos correspondentes
    # devem ficar None em vez de 0, espelhando o comportamento de *_avg_income.
    assert metrics["female_income_weight_sum"] is None
    assert metrics["black_income_weight_sum"] is None


def test_accum_to_metrics_returns_none_below_min_sample():
    acc = _accum_with(n=5)  # abaixo de MIN_SAMPLE_OCUPACAO (20)
    assert acc.to_metrics() is None


def test_cod_subgroups_national():
    json_path = os.path.join(os.path.dirname(__file__), '../data/output/cod_subgroups.json')
    assert os.path.exists(json_path), "cod_subgroups.json does not exist"

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Fix 1 (scripts/process_microdata.py): aceita lista (formato antigo) ou
    # dict com bloco `meta` + lista em "occupations" (formato novo).
    if isinstance(data, dict):
        assert "meta" in data, "cod_subgroups.json com bloco `meta` ausente"
        meta = data["meta"]
        assert isinstance(meta["survey_year"], int)
        assert isinstance(meta["survey_quarter"], int)
        assert meta["generated_at"]
        assert meta["source"]
        assert meta["sample_suppression_thresholds"]["min_sample_ocupacao"] == 20
        rows = data["occupations"]
    else:
        rows = data

    assert isinstance(rows, list)
    assert 80 <= len(rows) <= 130, f"Expected ~124 subgrupos COD, found {len(rows)}"

    item = rows[0]
    for field in ("code", "name", "section", "total_workers", "avg_income", "wage_bill", "sample_size"):
        assert field in item
    assert item["total_workers"] > 0
    assert item["avg_income"] > 0
    assert item["sample_size"] >= 20  # MIN_SAMPLE_OCUPACAO em process_microdata.py

    # Ao menos uma ocupação precisa ter os campos de desigualdade/informalidade
    # preenchidos (não None) para a amostra nacional, que é grande o bastante.
    assert any(row["informality_rate"] is not None for row in rows)
    assert any(row["gender_gap_pct"] is not None for row in rows)
    assert any(row["race_gap_pct"] is not None for row in rows)


def test_cod_subgroups_by_uf():
    json_path = os.path.join(os.path.dirname(__file__), '../data/output/cod_subgroups_by_uf.json')
    assert os.path.exists(json_path), "cod_subgroups_by_uf.json does not exist"

    with open(json_path, 'r', encoding='utf-8') as f:
        by_uf = json.load(f)

    assert isinstance(by_uf, dict)
    # Fix 1 (scripts/process_microdata.py): o arquivo pode carregar um bloco
    # `meta` no topo; conta apenas as entradas que sao listas de ocupacoes.
    uf_keys = [k for k, v in by_uf.items() if isinstance(v, list)]
    assert len(uf_keys) == 27, f"Esperado 27 UFs, encontrado {len(uf_keys)}"

    sp = by_uf.get("SP")
    assert sp, "UF 'SP' ausente ou vazia em cod_subgroups_by_uf.json"
    for field in ("code", "name", "total_workers", "avg_income", "sample_size"):
        assert field in sp[0]


def test_pnad_layout_slices_match_expected():
    import process_microdata as pm
    
    # Variáveis originais (confirmando que o dicionário bate com o que já usávamos)
    assert pm.COL_UF == slice(5, 7)
    assert pm.COL_PESO == slice(49, 64)
    assert pm.COL_SEXO == slice(94, 95)
    assert pm.COL_RACA == slice(106, 107)
    assert pm.COL_OCUP == slice(151, 155)
    assert pm.COL_POSICAO == slice(416, 418)
    assert pm.COL_CNPJ == slice(185, 186)
    assert pm.COL_RENDA == slice(426, 434)
    
    # Variáveis novas da fase B (VD3005: 406/2, V2009: 104/3, VD4010: 419/2)
    # Convertidas de coluna SAS 1-indexada para slice Python 0-indexado
    assert pm.COL_ANOS_ESTUDO == slice(405, 407)
    assert pm.COL_IDADE == slice(103, 106)
    assert pm.COL_ATIVIDADE == slice(418, 420)
