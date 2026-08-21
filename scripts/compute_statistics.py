"""Calcula ICs 95%, testes de significância de gaps e correlações entre
exposição à IA e informalidade/gaps, a partir de cod_subgroups.json e
scores.json — ver SPEC.md F4.

Nenhum resultado aqui é apresentado como causal: a correlação/regressão entre
score de exposição à IA e informalidade/gaps entre ocupações é associação
observacional entre agregados, não um efeito causal estimado — ver a ressalva
de honestidade metodológica em SPEC.md F4 e na página de metodologia (F3).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from stats import correlation, hypothesis, weighted  # noqa: E402

INPUT_SUBGROUPS = os.path.join(os.path.dirname(__file__), "../data/output/cod_subgroups.json")
INPUT_SCORES = os.path.join(os.path.dirname(__file__), "../data/output/scores.json")
OUTPUT_STATISTICS = os.path.join(os.path.dirname(__file__), "../data/output/statistics.json")

MIN_CORRELATION_N = 4  # correlation_significance() exige n >= 4 (transformação z de Fisher)
CORRELATION_FIELDS = {
    "ai_exposure_vs_informality": "informality_rate",
    "ai_exposure_vs_gender_gap": "gender_gap_pct",
    "ai_exposure_vs_race_gap": "race_gap_pct",
    "ai_exposure_vs_income": "avg_income",
}
CAUSAL_DISCLAIMER = "Correlação, não causalidade — ver metodologia (F3)."


def _scaled_ci_block(estimate, se, scale=1, ndigits=4):
    if estimate is None or se is None:
        return None
    ci = weighted.ci_95(estimate, se)
    if ci is None:
        return None
    return {
        "estimate": round(estimate * scale, ndigits),
        "se": round(se * scale, ndigits),
        "ci_low": round(ci[0] * scale, ndigits),
        "ci_high": round(ci[1] * scale, ndigits),
    }


def income_ci(item):
    """IC 95% da renda média nacional da ocupação, a partir das somas ponderadas brutas."""
    w_sum = item.get("income_weight_sum")
    wsum_x = item.get("wage_bill")
    wsum_x_sq = item.get("income_sq_weighted_sum")
    w_sq_sum = item.get("weight_sq_sum")
    if not w_sum or wsum_x is None or wsum_x_sq is None or not w_sq_sum:
        return None
    mean = weighted.weighted_mean(w_sum, wsum_x)
    se = weighted.standard_error_mean(w_sum, wsum_x, wsum_x_sq, w_sq_sum)
    return _scaled_ci_block(mean, se, scale=1, ndigits=2)


def informality_ci(item):
    """IC 95% da taxa de informalidade ponderada da ocupação, em pontos percentuais."""
    w_sum = item.get("informal_weight_sum")
    w_numerator = item.get("informal_weight_numerator")
    w_sq_sum = item.get("weight_sq_sum")
    if not w_sum or w_numerator is None or not w_sq_sum:
        return None
    p = weighted.weighted_proportion(w_sum, w_numerator)
    se = weighted.standard_error_proportion(w_sum, w_numerator, w_sq_sum)
    return _scaled_ci_block(p, se, scale=100, ndigits=1)


def _subgroup_mean_ci(item, avg_key, weight_sum_key, sq_key):
    """IC 95% de uma média de subgrupo (homem/mulher, branco/preto+pardo).

    Reconstrói Sigma(w*x) = media*w_sum a partir da média já publicada, pois
    cod_subgroups.json guarda a média e não a soma bruta por subgrupo.
    """
    avg = item.get(avg_key)
    w_sum = item.get(weight_sum_key)
    wsum_x_sq = item.get(sq_key)
    w_sq_sum = item.get("weight_sq_sum")
    if avg is None or not w_sum or wsum_x_sq is None or not w_sq_sum:
        return None
    wsum_x = avg * w_sum
    se = weighted.standard_error_mean(w_sum, wsum_x, wsum_x_sq, w_sq_sum)
    return _scaled_ci_block(avg, se, scale=1, ndigits=2)


def gender_gap_significance(item):
    """Teste z: o gap de gênero (renda média homem vs mulher) é distinguível de zero?"""
    male = _subgroup_mean_ci(item, "male_avg_income", "male_income_weight_sum", "male_income_sq_weighted_sum")
    female = _subgroup_mean_ci(item, "female_avg_income", "female_income_weight_sum", "female_income_sq_weighted_sum")
    if male is None or female is None:
        return None
    return hypothesis.z_test_diff(male["estimate"], male["se"], female["estimate"], female["se"])


def race_gap_significance(item):
    """Teste z: o gap de raça (renda média branca vs preta+parda) é distinguível de zero?"""
    white = _subgroup_mean_ci(item, "white_avg_income", "white_income_weight_sum", "white_income_sq_weighted_sum")
    black = _subgroup_mean_ci(item, "black_avg_income", "black_income_weight_sum", "black_income_sq_weighted_sum")
    if white is None or black is None:
        return None
    return hypothesis.z_test_diff(white["estimate"], white["se"], black["estimate"], black["se"])


def compute_occupation_statistics(item):
    stats = {}
    income = income_ci(item)
    if income:
        stats["income_ci"] = income
    informality = informality_ci(item)
    if informality:
        stats["informality_ci"] = informality
    gender = gender_gap_significance(item)
    if gender:
        stats["gender_gap_significance"] = gender
    race = race_gap_significance(item)
    if race:
        stats["race_gap_significance"] = race
    return stats or None


def cross_occupation_correlations(subgroups, scores):
    """Correlação (não-causal) entre score de exposição à IA e informalidade/gaps entre ocupações."""
    pairs = {key: [] for key in CORRELATION_FIELDS}
    for item in subgroups:
        code = item.get("code") or item.get("name")
        score_entry = scores.get(code)
        if not score_entry or score_entry.get("exposure") is None:
            continue
        score = score_entry["exposure"]
        for key, field in CORRELATION_FIELDS.items():
            value = item.get(field)
            if value is not None:
                pairs[key].append((score, value))

    results = {}
    for key, xy in pairs.items():
        if len(xy) < MIN_CORRELATION_N:
            continue
        xs, ys = zip(*xy)
        r = correlation.pearson_r(list(xs), list(ys))
        if r is None:
            continue
        regression = correlation.linear_regression(list(xs), list(ys))
        results[key] = {
            "r": round(r, 4),
            "n": len(xy),
            "significance": correlation.correlation_significance(r, len(xy)),
            "regression": regression,
        }

    if not results:
        return {}
    return {"pairs": results, "disclaimer": CAUSAL_DISCLAIMER}


def compute_statistics(subgroups, scores):
    per_occupation = {}
    for item in subgroups:
        stats = compute_occupation_statistics(item)
        if stats:
            code = item.get("code") or item.get("name")
            per_occupation[code] = stats
    return {
        "per_occupation": per_occupation,
        "correlations": cross_occupation_correlations(subgroups, scores),
    }


def load_json(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        raise FileNotFoundError(
            f"{path} não existe. Rode 'python3 scripts/process_microdata.py' primeiro."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    raw_subgroups = load_json(INPUT_SUBGROUPS)
    # Fix 1 (scripts/process_microdata.py): cod_subgroups.json agora e um dict
    # com `meta` + `occupations`; aceita o formato antigo (lista).
    subgroups = raw_subgroups.get("occupations") if isinstance(raw_subgroups, dict) else raw_subgroups
    scores = load_json(INPUT_SCORES, default={})
    result = compute_statistics(subgroups, scores)
    with open(OUTPUT_STATISTICS, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved statistics for {len(result['per_occupation'])} occupations to {OUTPUT_STATISTICS}")


if __name__ == "__main__":
    main()
