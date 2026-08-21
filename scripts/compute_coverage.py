"""Cobertura de exposicao por UF: emprego coberto / emprego elegivel.

Regra de cobertura (PRODUCT.md, "Coverage Rules"): a cobertura e um
resultado de primeira classe. Para cada UF e para o Brasil,

    cobertura_s = emprego coberto_s / emprego total_s

- emprego coberto = soma de pesos (V1028) das ocupacoes com exposicao
  nao-nula (indice Eloundou et al. 2024);
- emprego total (elegivel) = todo o emprego agregado pela estrutura COD,
  incluindo ocupacoes com exposicao null (ex.: forcas armadas);
- exposicao null NUNCA vira zero: fica fora do numerador e do estimador
  de exposicao, mas permanece no denominador de cobertura;
- estimativas usam TODOS os registros validos, incluindo celulas
  ocupacao x UF suprimidas no detalhe publico (regra #3 do PRODUCT.md) —
  por isso re-agregamos os microdados com pesos completos.
"""

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from compute_decomposition import (  # noqa: E402
    _artifact_vintage,
    _resolve_source,
    load_scores,
)
from process_microdata import (  # noqa: E402
    COVERAGE_DEFINITION,
    MIN_SAMPLE_GRUPO,
    MIN_SAMPLE_OCUPACAO,
    aggregate_quarter,
    load_reference,
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../data/output/coverage.json")


def compute_coverage(by_uf_weights, scores):
    """Cobertura por UF e nacional a partir de pesos NAO suprimidos.

    by_uf_weights: {uf: {codigo_ocupacao: peso_ponderado_total}}
    scores:        {codigo: theta ou None}
    Retorna dict de data/output/coverage.json (sem o bloco meta).
    Funcao pura — testavel com fixtures.
    """
    ufs_out = {}
    national_covered = 0.0
    national_total = 0.0
    for uf in sorted(by_uf_weights):
        covered = sum(
            w for code, w in by_uf_weights[uf].items()
            if scores.get(code) is not None
        )
        total = sum(by_uf_weights[uf].values())
        national_covered += covered
        national_total += total
        ufs_out[uf] = {
            "covered_employment": round(covered),
            "eligible_employment": round(total),
            "uncovered_employment": round(total - covered),
            "coverage_rate": (covered / total) if total > 0 else None,
        }

    national_rate = (
        national_covered / national_total if national_total > 0 else None
    )
    return {
        "brazil": {
            "covered_employment": round(national_covered),
            "eligible_employment": round(national_total),
            "uncovered_employment": round(national_total - national_covered),
            "coverage_rate": national_rate,
        },
        "ufs": ufs_out,
        "validation": {
            "n_ufs": len(ufs_out),
            "coverage_bounded_0_1": all(
                0.0 <= v["coverage_rate"] <= 1.0
                for v in ufs_out.values()
                if v["coverage_rate"] is not None
            ),
            "null_never_zero": True,  # null fica fora do numerador, nunca somado como 0
        },
    }


def main():
    subgrupos, grupo_base_to_subgrupo, uf_codes = load_reference()
    scores, exposure_source = load_scores()

    source, source_id = _resolve_source()
    year = int(os.getenv("IBGE_MICRODATA_YEAR", "2026"))
    quarter = int(os.getenv("IBGE_MICRODATA_QUARTER", "1"))

    artifact_vintage = _artifact_vintage()
    if artifact_vintage and artifact_vintage != (year, quarter):
        print(f"Aviso: uf_totals.json declara {artifact_vintage}, mas o microdado "
              f"selecionado e {year} Q{quarter}. Rode `make refresh`.", file=sys.stderr)

    print(f"Re-agregando microdados (pesos completos, sem supressao): {source}")
    _national, by_uf, skipped, _by_sector, _sector_aggs = aggregate_quarter(
        source, subgrupos, grupo_base_to_subgrupo, uf_codes,
        want_by_uf=True, group_by="subgrupo",
    )
    if by_uf is None:
        raise RuntimeError("aggregate_quarter retornou by_uf=None")

    by_uf_weights = {
        uf: {code: acc.w for code, acc in occs.items()}
        for uf, occs in by_uf.items()
    }

    result = compute_coverage(by_uf_weights, scores)

    result["meta"] = {
        "survey_year": year,
        "survey_quarter": quarter,
        "source": source_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage_definition": (
            "cobertura = emprego em ocupacoes com exposicao nao-nula / emprego "
            "total agregado pela estrutura COD; exposicao null fica fora do "
            "numerador (nunca vira zero) e permanece no denominador"
        ),
        "state_estimates_include_suppressed_cells": (
            "Estimativas por UF usam todos os registros cobertos validos, "
            "incluindo celulas ocupacao x UF suprimidas no detalhe publico "
            "(amostra nao ponderada < MIN_SAMPLE_OCUPACAO)."
        ),
        "sample_suppression_thresholds": {
            "min_sample_ocupacao": MIN_SAMPLE_OCUPACAO,
            "min_sample_grupo": MIN_SAMPLE_GRUPO,
        },
        "exposure_index_source": exposure_source,
        "input_coverage_definition": COVERAGE_DEFINITION,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    br = result["brazil"]
    print(f"Brasil: cobertura = {br['coverage_rate']:.4f} "
          f"({br['covered_employment']:,} de {br['eligible_employment']:,})")
    ranked = sorted(result["ufs"].items(), key=lambda kv: kv[1]["coverage_rate"])
    lo, hi = ranked[0], ranked[-1]
    print(f"Menor cobertura: {lo[0]} {lo[1]['coverage_rate']:.4f} | "
          f"maior: {hi[0]} {hi[1]['coverage_rate']:.4f}")
    assert result["validation"]["coverage_bounded_0_1"], "cobertura fora de [0,1]"
    if skipped:
        print(f"Aviso: {skipped} registros com ocupacao fora da estrutura COD ignorados.")
    print(f"-> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
