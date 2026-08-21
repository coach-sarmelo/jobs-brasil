"""Gera scripts/reference/cod_to_soc.json a partir de tres fatos:

1. Os codigos COD (scripts/reference/cod_estrutura.json) SAO codigos ISCO-08
   (grupo menor de 3 digitos / grupo unitario de 4 digitos), nao uma
   classificacao brasileira independente -- verificado por amostragem contra
   a estrutura oficial ISCO-08 (ver tasks/plan.md, "Correcao importante").
2. O crosswalk oficial ISCO-08 x SOC 2010 do BLS (data/external/
   isco08_to_soc2010.csv) mapeia 428 dos 434 codigos grupo_base do COD
   diretamente.
3. occ_level.csv (Eloundou et al.) e national_May2021_dl.csv usam codigos
   SOC 2018, nao SOC 2010 -- as duas versoes divergem em varias ocupacoes
   (ex.: "Software Developers, Applications"/"Systems Software" de 2010
   foram fundidos em "Software Developers" de 2018). Por isso o crosswalk
   oficial BLS "2010 SOC -> 2018 SOC" (data/external/soc2010_to_soc2018.csv)
   e encadeado apos o passo 2, para que cod_to_soc.json guarde codigos SOC
   2018 prontos para juncao direta com occ_level.csv/national_May2021_dl.csv.

Para cada subgrupo COD, agrega os codigos SOC 2018 de todos os seus
grupo_base filhos via os dois crosswalks encadeados. Os 6 grupo_base sem
cobertura no crosswalk ISCO->SOC2010 afetam apenas 4 subgrupos (41, 51, 516,
622) -- 516 e 622 mantem cobertura via seus outros filhos; 41 e 51
(policiais/bombeiros militares, categorias institucionais brasileiras sem
equivalente direto no ISCO-08/SOC padrao) recebem override manual
documentado (ja em SOC 2018).
"""
import csv
import json
import os

REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")
EXTERNAL_DIR = os.path.join(os.path.dirname(__file__), "../data/external")
COD_ESTRUTURA_PATH = os.path.join(REFERENCE_DIR, "cod_estrutura.json")
ISCO_SOC2010_CSV_PATH = os.path.join(EXTERNAL_DIR, "isco08_to_soc2010.csv")
SOC2010_SOC2018_CSV_PATH = os.path.join(EXTERNAL_DIR, "soc2010_to_soc2018.csv")
OUTPUT_PATH = os.path.join(REFERENCE_DIR, "cod_to_soc.json")

# Subgrupos que o crosswalk BLS nao cobre em nenhum de seus grupo_base
# filhos -- categorias institucionais brasileiras (policia/bombeiros
# organizados como forcas militares estaduais) sem equivalente direto no
# ISCO-08/SOC padrao. Mapeados pelo conteudo real da ocupacao (patrulha
# policial civil, combate a incendio), nao pelo rotulo "militar".
MANUAL_OVERRIDES = {
    "41": {
        "soc_codes": ["33-3051"],
        "mapping_note": (
            "Policiais militares brasileiros exercem policiamento ostensivo "
            "civil (patrulha, ordem publica) apesar do enquadramento "
            "institucional 'militar' -- sem equivalente direto no ISCO-08/SOC "
            "padrao (que reserva o grupo 0/55-xxxx a forcas armadas "
            "propriamente ditas). Mapeado para SOC 33-3051 (Police and "
            "Sheriff's Patrol Officers) pelo conteudo real da ocupacao."
        ),
    },
    "51": {
        "soc_codes": ["33-2011"],
        "mapping_note": (
            "Bombeiros militares brasileiros exercem combate a incendio e "
            "resgate civil apesar do enquadramento institucional 'militar' -- "
            "mesma logica de 41. Mapeado para SOC 33-2011 (Firefighters)."
        ),
    },
}


def load_isco_to_soc2010(path):
    isco_to_soc2010 = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            isco_to_soc2010.setdefault(row["isco08_code"], set()).add(row["soc2010_code"])
    return isco_to_soc2010


def load_soc2010_to_soc2018(path):
    soc2010_to_soc2018 = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            soc2010_to_soc2018.setdefault(row["soc2010_code"], set()).add(row["soc2018_code"])
    return soc2010_to_soc2018


def build_crosswalk(cod_estrutura, isco_to_soc2010, soc2010_to_soc2018):
    grupo_base_to_subgrupo = cod_estrutura["grupo_base_to_subgrupo"]

    subgrupo_to_grupo_bases = {}
    for grupo_base, subgrupo in grupo_base_to_subgrupo.items():
        subgrupo_to_grupo_bases.setdefault(subgrupo, []).append(grupo_base)

    result = {}
    for cod_code in cod_estrutura["subgrupos"]:
        if cod_code in MANUAL_OVERRIDES:
            override = MANUAL_OVERRIDES[cod_code]
            result[cod_code] = {
                "soc_codes": override["soc_codes"],
                "source": "manual-override",
                "mapping_note": override["mapping_note"],
            }
            continue

        soc2010_codes = set()
        for grupo_base in subgrupo_to_grupo_bases.get(cod_code, []):
            soc2010_codes |= isco_to_soc2010.get(grupo_base, set())

        soc2018_codes = set()
        for soc2010_code in soc2010_codes:
            mapped = soc2010_to_soc2018.get(soc2010_code)
            if not mapped:
                raise ValueError(
                    f"COD {cod_code}: SOC2010 {soc2010_code} has no SOC2018 "
                    "mapping — check data/external/soc2010_to_soc2018.csv."
                )
            soc2018_codes |= mapped

        if not soc2018_codes:
            raise ValueError(
                f"COD {cod_code} has no SOC mapping and no manual override — "
                "add one to MANUAL_OVERRIDES before regenerating."
            )

        result[cod_code] = {
            "soc_codes": sorted(soc2018_codes),
            "source": "isco08-soc2010-soc2018-bls-crosswalk",
            "mapping_note": None,
        }

    return result


if __name__ == "__main__":
    with open(COD_ESTRUTURA_PATH, encoding="utf-8") as f:
        cod_estrutura = json.load(f)
    isco_to_soc2010 = load_isco_to_soc2010(ISCO_SOC2010_CSV_PATH)
    soc2010_to_soc2018 = load_soc2010_to_soc2018(SOC2010_SOC2018_CSV_PATH)

    crosswalk = build_crosswalk(cod_estrutura, isco_to_soc2010, soc2010_to_soc2018)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(crosswalk, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"-> {OUTPUT_PATH} ({len(crosswalk)} ocupacoes COD mapeadas)")
