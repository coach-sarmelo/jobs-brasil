"""Decomposicao exata por composicao da exposicao ocupacional a IA (UF vs Brasil).

Identidade contabil (PRODUCT.md, "Core Analytical Framework"):

    E_s     = sum_j p_js * theta_j                    (exposicao da UF s)
    C_js    = (p_js - p_jBR) * (theta_j - E_BR)       (contribuicao da ocupacao j)
    E_s-E_BR = sum_j C_js                             (soma exata, sem residuo)

com p_js = participacao da ocupacao j no emprego COBERTO (exposicao nao-nula)
da UF s. Theta e fixo no nivel da ocupacao (indice Eloundou et al. 2024),
portanto a forma entre/dentro do plano reduz-se a esta forma exata.

Regra de cobertura (PRODUCT.md #3): as estimativas por UF usam TODOS os
registros cobertos validos — incluindo celulas ocupacao x UF suprimidas nos
detalhes publicos (amostra nao ponderada < MIN_SAMPLE_OCUPACAO). Por isso este
script re-agrega os microdados via process_microdata.aggregate_quarter, que
expande os pesos completos (a supressao so acontece em build_rows/to_metrics).

Exposicao null nunca vira zero: ocupacoes sem score ficam fora do numerador
e do denominador das participacoes.

Isto e uma decomposicao contabil. Nao e instrumento Bartik, desenho causal,
previsao ou estimativa de adocao de IA.
"""

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from process_microdata import (  # noqa: E402
    COVERAGE_DEFINITION,
    MIN_SAMPLE_GRUPO,
    MIN_SAMPLE_OCUPACAO,
    aggregate_quarter,
    load_reference,
)
from stats.weighted import weighted_mean  # noqa: E402

# Tolerancia relativa da identidade contabil sum_j C_js = E_s - E_BR.
TOLERANCE = 1e-9

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../data/output/decomposition.json")
SCORES_PATH = os.path.join(os.path.dirname(__file__), "../data/output/scores.json")
UF_TOTALS_PATH = os.path.join(os.path.dirname(__file__), "../data/output/uf_totals.json")


def load_scores(path=SCORES_PATH):
    """Le scores.json -> {codigo: exposicao ou None}.

    Ocupacoes ausentes do score ficam de fora (mesma semantica que null).
    """
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    entries = raw.values() if isinstance(raw, dict) else raw
    scores = {}
    source = None
    for entry in entries:
        if not isinstance(entry, dict) or "code" not in entry:
            continue
        scores[str(entry["code"])] = entry.get("exposure")
        if source is None and entry.get("source"):
            source = entry["source"]
    return scores, source


def _section_name(subgrupos, code):
    meta = subgrupos.get(code)
    if not meta:
        return "Outras ocupacoes"
    return meta["grande_grupo"].strip().capitalize()


def decompose(by_uf_weights, scores, subgrupos):
    """Decomposicao exata a partir de pesos ocupacao x UF NAO suprimidos.

    by_uf_weights: {uf: {codigo_ocupacao: peso_ponderado_total}}
    scores:        {codigo: theta ou None}
    subgrupos:     {codigo: {"grande_grupo": ..., "name": ...}} (cod_estrutura)

    Retorna o dict completo de data/output/decomposition.json (sem o bloco
    meta, preenchido pelo chamador). Funcao pura — testavel com fixtures.
    """
    # 1. Emprego coberto por UF/ocupacao (exposicao nao-nula; null nunca e 0).
    covered = {
        uf: {
            code: w
            for code, w in occs.items()
            if scores.get(code) is not None and w > 0
        }
        for uf, occs in by_uf_weights.items()
    }

    # 2. Totais e participacoes.
    uf_covered_employment = {uf: sum(occs.values()) for uf, occs in covered.items()}
    national_weight_by_code = {}
    for occs in covered.values():
        for code, w in occs.items():
            national_weight_by_code[code] = national_weight_by_code.get(code, 0.0) + w
    brazil_covered_employment = sum(national_weight_by_code.values())

    # 3. Exposicao por UF e do Brasil (media ponderada por emprego coberto).
    uf_exposure = {}
    for uf, occs in covered.items():
        w_sum = uf_covered_employment[uf]
        wsum_x = sum(w * scores[code] for code, w in occs.items())
        uf_exposure[uf] = weighted_mean(w_sum, wsum_x)
    e_br = weighted_mean(
        brazil_covered_employment,
        sum(w * scores[code] for code, w in national_weight_by_code.items()),
    )

    # 4. Contribuicoes exatas por ocupacao e por grande grupo.
    # Importante: iterar sobre o conjunto NACIONAL coberto (uniao). Uma
    # ocupacao coberta nacionalmente mas ausente da UF s tem p_js = 0 e
    # contribuicao (0 - p_jBR)*(theta_j - E_BR) != 0 — sem ela a soma
    # nao fecha em E_s - E_BR.
    national_codes = sorted(national_weight_by_code)
    ufs_out = {}
    max_residual = 0.0
    for uf in sorted(covered):
        w_s = uf_covered_employment[uf]
        gap = uf_exposure[uf] - e_br
        occ_contribs = []
        group_contrib = {}
        group_weight = {}
        for code in national_codes:
            theta = scores[code]
            w = covered[uf].get(code, 0.0)
            p_state = w / w_s
            p_br = national_weight_by_code[code] / brazil_covered_employment
            contrib = (p_state - p_br) * (theta - e_br)
            section = _section_name(subgrupos, code)
            occ_contribs.append({
                "code": code,
                "name": subgrupos[code]["name"].strip() if code in subgrupos else code,
                "section": section,
                "theta": theta,
                "p_state": p_state,
                "p_brazil": p_br,
                "contribution": contrib,
            })
            group_contrib[section] = group_contrib.get(section, 0.0) + contrib
            group_weight[section] = group_weight.get(section, 0.0) + w

        # Ordenacao deterministica: positivas desc, depois negativas por
        # magnitude desc (mais negativa primeiro).
        positives = sorted((c for c in occ_contribs if c["contribution"] > 0),
                           key=lambda c: -c["contribution"])
        negatives = sorted((c for c in occ_contribs if c["contribution"] <= 0),
                           key=lambda c: c["contribution"])

        residual = gap - sum(c["contribution"] for c in occ_contribs)
        max_residual = max(max_residual, abs(residual))

        ufs_out[uf] = {
            "exposure": uf_exposure[uf],
            "gap": gap,
            "covered_employment": round(w_s),
            "total_employment": round(sum(by_uf_weights[uf].values())),
            "residual": residual,
            "contributions_by_occupation": positives + negatives,
            "contributions_by_major_group": [
                {
                    "section": section,
                    "contribution": group_contrib[section],
                    "covered_employment": round(group_weight[section]),
                    "covered_employment_share": (
                        group_weight[section] / w_s if w_s > 0 else None
                    ),
                }
                for section in sorted(group_contrib, key=lambda s: -group_contrib[s])
            ],
        }

    # Reconciliacao nacional (PRODUCT.md validacao #4): a media ponderada das
    # estimativas das UFs deve reproduzir E_BR.
    total_covered = sum(uf_covered_employment.values())
    reconciliation = (
        sum(uf_covered_employment[uf] * uf_exposure[uf] for uf in covered)
        / total_covered
        if total_covered > 0
        else None
    )

    return {
        "brazil": {
            "exposure": e_br,
            "covered_employment": round(brazil_covered_employment),
            "total_employment": round(sum(
                w for occs in by_uf_weights.values() for w in occs.values()
            )),
        },
        "ufs": ufs_out,
        "validation": {
            "tolerance": TOLERANCE,
            "max_identity_residual": max_residual,
            "national_reconciliation": reconciliation,
            "national_reconciliation_residual": (
                abs(reconciliation - e_br)
                if reconciliation is not None and e_br is not None
                else None
            ),
            "n_ufs": len(ufs_out),
            "shares_sum_to_one_within_tolerance": all(
                abs(sum(
                    w for w in covered[uf].values()
                ) / uf_covered_employment[uf] - 1.0) <= TOLERANCE
                for uf in covered
                if uf_covered_employment[uf] > 0
            ),
        },
    }


def _resolve_source():
    """Espelha process_microdata: MICRODATA_TXT ou o trimestre congelado."""
    path = os.getenv("MICRODATA_TXT")
    if path:
        return path, os.path.abspath(path)
    import fetch_ibge_microdata as fim

    year = fim.YEAR
    quarter = fim.QUARTER
    local = os.path.join(
        os.path.dirname(__file__), "../data/microdata",
        f"PNADC_{quarter.zfill(2)}{year}.txt",
    )
    if os.path.exists(local):
        return local, fim.BASE_URL
    return fim.fetch_quarter(year, quarter), fim.BASE_URL


def _artifact_vintage():
    """Vintage declarada nos artefatos existentes (pos-refresh), se houver."""
    try:
        with open(UF_TOTALS_PATH, encoding="utf-8") as f:
            meta = json.load(f).get("meta")
        if isinstance(meta, dict) and "survey_year" in meta:
            return int(meta["survey_year"]), int(meta["survey_quarter"])
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def main():
    subgrupos, grupo_base_to_subgrupo, uf_codes = load_reference()
    scores, exposure_source = load_scores()

    source, source_id = _resolve_source()
    year = int(os.getenv("IBGE_MICRODATA_YEAR", "2026"))
    quarter = int(os.getenv("IBGE_MICRODATA_QUARTER", "1"))

    # A safra e definida pelo microdado efetivamente lido (env/anos-padrao);
    # se os artefatos declararem outra, avisa — deve haver uma unica safra.
    artifact_vintage = _artifact_vintage()
    if artifact_vintage and artifact_vintage != (year, quarter):
        print(f"Aviso: uf_totals.json declara {artifact_vintage}, mas o microdado "
              f"selecionado e {year} Q{quarter}. Rode `make refresh`.", file=sys.stderr)

    print(f"Re-agregando microdados (pesos completos, sem supressao): {source}")
    national, by_uf, skipped, _by_sector, _sector_aggs = aggregate_quarter(
        source, subgrupos, grupo_base_to_subgrupo, uf_codes,
        want_by_uf=True, group_by="subgrupo",
    )

    if by_uf is None:  # want_by_uf=True acima; defesa contra assinatura Optional
        raise RuntimeError("aggregate_quarter retornou by_uf=None")

    by_uf_weights = {
        uf: {code: acc.w for code, acc in occs.items()}
        for uf, occs in by_uf.items()
    }

    result = decompose(by_uf_weights, scores, subgrupos)

    # Checagem cruzada: pesos por UF somados vs acumulador nacional direto
    # (mesmos registros; desvio deve ser zero).
    nat_w = {code: acc.w for code, acc in national.items()}
    cross = max(
        (abs(sum(by_uf_weights[uf].get(code, 0.0) for uf in by_uf_weights) - w)
         for code, w in nat_w.items()),
        default=0.0,
    )
    result["validation"]["uf_vs_national_weight_max_deviation"] = cross

    result["meta"] = {
        "survey_year": year,
        "survey_quarter": quarter,
        "source": source_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": (
            "Decomposicao exata por composicao: C_js = (p_js - p_jBR) * "
            "(theta_j - E_BR), com soma exata em E_s - E_BR (identidade "
            "contabil; nao e estimativa causal)."
        ),
        "coverage_definition": COVERAGE_DEFINITION,
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
        "tolerance": TOLERANCE,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    v = result["validation"]
    print(f"Brasil E_BR = {result['brazil']['exposure']:.4f} | "
          f"emprego coberto = {result['brazil']['covered_employment']:,}")
    ranked = sorted(result["ufs"].items(), key=lambda kv: -kv[1]["gap"])
    top, bottom = ranked[0], ranked[-1]
    print(f"Maior gap: {top[0]} {top[1]['gap']:+.4f} | menor: {bottom[0]} {bottom[1]['gap']:+.4f}")
    print(f"UFs: {v['n_ufs']} | residuo maximo da identidade: {v['max_identity_residual']:.2e} "
          f"| residuo reconciliacao nacional: {v['national_reconciliation_residual']:.2e} "
          f"| desvio pesos UF vs nacional: {cross:.2e}")
    if skipped:
        print(f"Aviso: {skipped} registros com ocupacao fora da estrutura COD ignorados.")
    print(f"-> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
