import argparse
import json
import os
from datetime import datetime, timezone

from fetch_ibge_microdata import BASE_URL, QuarterUnavailable, fetch_quarter
from process_microdata import Accum, aggregate_quarter, load_reference

# PNAD Contínua tem layout fixo trimestral desde 1o tri/2012, mas 2015 é o
# ponto de partida padrão da série histórica deste projeto (ver SPEC.md F1).
DEFAULT_FROM_YEAR = 2015
DEFAULT_TO_YEAR = int(os.getenv("IBGE_MICRODATA_YEAR", "2026"))
QUARTERS = ("1", "2", "3", "4")



def process_year(year, subgrupos, grupo_base_to_subgrupo, uf_codes):
    """Baixa os 4 trimestres do ano, funde os agregados por grande grupo e
    descarta cada .zip/.txt bruto assim que processado (não acumula em disco)."""
    annual = {}
    for quarter in QUARTERS:
        lines = fetch_quarter(str(year), quarter)
        national, _, _, _, _ = aggregate_quarter(
            lines, subgrupos, grupo_base_to_subgrupo, uf_codes,
            want_by_uf=False, group_by="grande_grupo",
        )
        for grande_grupo, acc in national.items():
            annual.setdefault(grande_grupo, Accum()).merge(acc)

    rows = []
    for grande_grupo, acc in annual.items():
        metrics = acc.to_metrics()
        if metrics is None:
            continue
        rows.append({"grande_grupo": grande_grupo, "ano": year, **metrics})
    rows.sort(key=lambda r: -r["total_workers"])
    return rows


OUTPUT_TIMESERIES = os.path.join(os.path.dirname(__file__), "../data/output/grande_grupos_timeseries.json")


def build_timeseries(rows):
    by_grande_grupo = {}
    for row in rows:
        grande_grupo = row["grande_grupo"]
        point = {k: v for k, v in row.items() if k != "grande_grupo"}
        by_grande_grupo.setdefault(grande_grupo, []).append(point)

    for points in by_grande_grupo.values():
        points.sort(key=lambda p: p["ano"])

    return by_grande_grupo


def build_meta(anos):
    """Bloco de metadados de topo do JSON (safra/vintage da série anual).

    Documenta a série sem alterar o contrato do artefato: as chaves de grande
    grupo continuam no topo do dicionário (consumidores existentes iteram o
    objeto diretamente). O corte principal do projeto é o 1o tri/2026
    (IBGE_MICRODATA_YEAR/IBGE_MICRODATA_QUARTER); esta série é anual.
    """
    first = anos[0] if anos else None
    last = anos[-1] if anos else None
    return {
        "survey_year_min": first,
        "survey_year_max": last,
        "aggregation": (
            "média ponderada dos 4 trimestres de cada ano: os agregados "
            "trimestrais são fundidos por grande grupo e as métricas são "
            "calculadas sobre os totais ponderados (pesos amostrais da PNAD "
            "Contínua)"
        ),
        "source": BASE_URL,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "notes": (
            "O corte principal do projeto é o 1o trimestre de 2026 "
            "(IBGE_MICRODATA_YEAR/IBGE_MICRODATA_QUARTER); esta série agrega os "
            "4 trimestres de cada ano e não deve ser comparada diretamente com "
            "um trimestre isolado."
        ),
    }


def fetch_historical(from_year, to_year):
    subgrupos, grupo_base_to_subgrupo, uf_codes = load_reference()
    
    all_rows = []
    for year in range(from_year, to_year + 1):
        print(f"Processando {year} (4 trimestres)...")
        try:
            rows = process_year(year, subgrupos, grupo_base_to_subgrupo, uf_codes)
            all_rows.extend(rows)
        except QuarterUnavailable as e:
            print(f"Aviso: {year} indisponível no IBGE ainda ({e}). Parando a série histórica aqui.")
            break

    timeseries = build_timeseries(all_rows)
    anos = sorted({p["ano"] for points in timeseries.values() for p in points})
    payload = {"meta": build_meta(anos), **timeseries}
    with open(OUTPUT_TIMESERIES, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    if anos:
        print(f"Consolidados {len(anos)} anos ({anos[0]}-{anos[-1]}) em {len(timeseries)} grandes grupos.")
    print(f"-> {OUTPUT_TIMESERIES}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Baixa e agrega microdados trimestrais da PNAD Contínua em pontos anuais por grande grupo COD, diretamente para timeseries."
    )
    parser.add_argument("--from", dest="from_year", type=int, default=DEFAULT_FROM_YEAR)
    parser.add_argument("--to", dest="to_year", type=int, default=DEFAULT_TO_YEAR)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    fetch_historical(args.from_year, args.to_year)
