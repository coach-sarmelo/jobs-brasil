"""Calcula scores.json a partir do indice de exposicao publicado de Eloundou,
Manning, Mishkin & Rock (2024, Science, "GPTs are GPTs"), nao mais via LLM
(GABRIEL) -- ver tasks/plan.md (F5) e data/external/SOURCES.md para
proveniencia dos dados vendidos.

Para cada ocupacao COD (cod_subgroups.json), usa scripts/reference/
cod_to_soc.json para os codigos SOC 2018 correspondentes, expande cada um
para os codigos O*NET-SOC filhos em data/external/occ_level.csv, e calcula
a media de dv_rating_beta ponderada por emprego (data/external/
national_May2021_dl.csv). Quando o emprego nao esta disponivel para nenhum
SOC contribuinte, cai para media simples entre os SOCs (nao inventa peso).
Ocupacoes sem nenhuma cobertura O*NET-SOC (ex.: forcas armadas, fora do
escopo do estudo de Eloundou et al.) recebem exposure: null -- lacuna de
dado real, nao mascarada por um fallback heuristico. O artefato inclui um
bloco _meta com as versoes do indice de exposicao e do crosswalk CBO->SOC
(contrato de vintage do PRODUCT.md).
"""
import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone

SCRIPTS_DIR = os.path.dirname(__file__)
INPUT_SUBGROUPS = os.path.join(SCRIPTS_DIR, "../data/output/cod_subgroups.json")
COD_TO_SOC_PATH = os.path.join(SCRIPTS_DIR, "reference/cod_to_soc.json")
OCC_LEVEL_CSV = os.path.join(SCRIPTS_DIR, "../data/external/occ_level.csv")
EMPLOYMENT_CSV = os.path.join(SCRIPTS_DIR, "../data/external/national_May2021_dl.csv")
OUTPUT_SCORES = os.path.join(SCRIPTS_DIR, "../data/output/scores.json")

SOURCE = "eloundou-2024-dv-beta"

# Versao do crosswalk CBO->SOC gravada em cada entrada de cod_to_soc.json
# (ver scripts/build_cod_to_soc_crosswalk.py e data/external/SOURCES.md:
# BLS ISCO-08 x SOC 2010, ago/2012 atualizado jun/2015; SOC 2010 x SOC 2018,
# nov/2017).
CROSSWALK_VERSION = "isco08-soc2010-soc2018-bls-crosswalk"

# Regra de cobertura: ocupacoes sem correspondencia O*NET-SOC ficam com
# exposure null (lacuna real, nao mascarada por fallback heuristico).
COVERAGE_DEFINITION = "Ocupacoes sem correspondencia O*NET-SOC ficam com exposicao null"


@dataclass
class ExposureResult:
    exposure: float
    onet_soc_codes: list


def index_by_soc_prefix(onet_ratings):
    """Agrupa avaliacoes O*NET-SOC pelo prefixo de 6 digitos (codigo SOC),
    uma vez, para busca O(1) em compute_exposure_for_soc_codes -- em vez de
    escanear todo o dict de avaliacoes para cada soc_code de cada ocupacao."""
    index = {}
    for code, rating in onet_ratings.items():
        index.setdefault(code[:7], []).append((code, rating))
    return index


def compute_exposure_for_soc_codes(soc_codes, onet_by_soc, employment_by_soc):
    """dv_rating_beta (0-1) ponderado por emprego entre os SOCs de uma
    ocupacao COD, reescalado para 0-10. Dentro de um SOC (varios O*NET-SOC
    filhos), simples media -- BLS nao publica emprego no nivel O*NET-SOC.
    Quando o emprego de algum SOC contribuinte falta, cai para media simples
    entre os SOCs (nao inventa peso). Retorna None se nenhum soc_code tiver
    avaliacao O*NET-SOC disponivel. onet_by_soc: saida de index_by_soc_prefix."""
    per_soc = []
    for soc_code in soc_codes:
        matched = onet_by_soc.get(soc_code, [])
        if not matched:
            continue
        soc_avg = sum(rating for _, rating in matched) / len(matched)
        weight = employment_by_soc.get(soc_code)
        per_soc.append((soc_avg, weight, [code for code, _ in matched]))

    if not per_soc:
        return None

    onet_soc_codes = sorted(code for _, _, codes in per_soc for code in codes)

    if all(weight is not None and weight > 0 for _, weight, _ in per_soc):
        total_weight = sum(weight for _, weight, _ in per_soc)
        weighted_avg = sum(avg * weight for avg, weight, _ in per_soc) / total_weight
    else:
        weighted_avg = sum(avg for avg, _, _ in per_soc) / len(per_soc)

    return ExposureResult(exposure=round(weighted_avg * 10, 1), onet_soc_codes=onet_soc_codes)


def load_onet_data(path):
    """Le occ_level.csv uma unica vez, retornando (ratings, titles) --
    antes eram duas funcoes fazendo duas passadas separadas pelo mesmo
    arquivo."""
    ratings = {}
    titles = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            code = row["O*NET-SOC Code"]
            ratings[code] = float(row["dv_rating_beta"])
            titles[code] = row["Title"]
    return ratings, titles


def load_employment_by_soc(path):
    employment = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["O_GROUP"] != "detailed":
                continue
            raw = row["TOT_EMP"].replace(",", "").strip()
            if not raw or not raw.isdigit():
                continue
            employment[row["OCC_CODE"]] = float(raw)
    return employment


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_meta(generated_at):
    """Metadados de versao do artefato scores.json (contrato de vintage do
    PRODUCT.md): versao do indice de exposicao, versao do crosswalk CBO->SOC,
    timestamp deterministico (um por execucao) e regra de cobertura."""
    return {
        "exposure_index_version": SOURCE,
        "crosswalk_version": CROSSWALK_VERSION,
        "generated_at": generated_at,
        "coverage_definition": COVERAGE_DEFINITION,
    }


def compute_scores(subgroups, cod_to_soc, onet_ratings, onet_titles, employment_by_soc):
    generated_at = datetime.now(timezone.utc).isoformat()
    onet_by_soc = index_by_soc_prefix(onet_ratings)
    scores = {}
    for item in subgroups:
        code = item["code"]
        crosswalk_entry = cod_to_soc.get(code)
        soc_codes = crosswalk_entry["soc_codes"] if crosswalk_entry else []

        result = compute_exposure_for_soc_codes(soc_codes, onet_by_soc, employment_by_soc)
        onet_soc_codes = result.onet_soc_codes if result else []

        scores[code] = {
            "code": code,
            "name": item["name"],
            "exposure": result.exposure if result else None,
            "soc_codes": soc_codes,
            "onet_soc_codes": onet_soc_codes,
            "onet_soc_titles": [onet_titles[c] for c in onet_soc_codes if c in onet_titles],
            "source": SOURCE,
            "mapping_note": crosswalk_entry["mapping_note"] if crosswalk_entry else None,
            "generated_at": generated_at,
        }
    scores["_meta"] = build_meta(generated_at)
    return scores


if __name__ == "__main__":
    raw_subgroups = load_json(INPUT_SUBGROUPS)
    # Fix 1 (scripts/process_microdata.py): cod_subgroups.json agora e um dict
    # com `meta` + `occupations`; aceita o formato antigo (lista).
    subgroups = raw_subgroups.get("occupations") if isinstance(raw_subgroups, dict) else raw_subgroups
    cod_to_soc = load_json(COD_TO_SOC_PATH)
    onet_ratings, onet_titles = load_onet_data(OCC_LEVEL_CSV)
    employment_by_soc = load_employment_by_soc(EMPLOYMENT_CSV)

    scores = compute_scores(subgroups, cod_to_soc, onet_ratings, onet_titles, employment_by_soc)

    with open(OUTPUT_SCORES, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2, sort_keys=True)

    occupation_codes = [code for code in scores if code != "_meta"]
    missing = [code for code in occupation_codes if scores[code]["exposure"] is None]
    print(f"-> {OUTPUT_SCORES} ({len(occupation_codes)} ocupações, {len(missing)} sem exposure: {missing})")
