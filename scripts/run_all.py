#!/usr/bin/env python3
"""run_all.py — executa a pipeline do projeto sem depender de make.

Uso:
  python scripts/run_all.py             # pipeline completa (equivale a `make refresh`)
  python scripts/run_all.py pipeline
  python scripts/run_all.py test        # pytest (equivale a `make test`)

Todos os passos rodam com o mesmo interpretador que invocou este script
(sys.executable). Instale as dependências nele primeiro — veja `make setup`
ou, sem make:  python3 -m pip install -r requirements.txt -r requirements-dev.txt

A ordem dos passos espelha o alvo `refresh` do Makefile (não reordenar):
cada etapa consome o artefato da anterior, de data/microdata/ até as tabelas
do artigo em data/output/. O site (site/) é estático e já vem commitado:
não é compilado por esta pipeline (ver README, seção "Site").
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PIPELINE = [
    "scripts/fetch_pnad_layout.py",
    "scripts/fetch_ibge_microdata.py",
    "scripts/process_microdata.py",
    "scripts/fetch_historical_microdata.py",
    "scripts/build_cod_to_soc_crosswalk.py",
    "scripts/compute_ai_exposure.py",
    "scripts/compute_decomposition.py",
    "scripts/compute_coverage.py",
    "scripts/compute_statistics.py",
    "scripts/build_regional_panel.py",
    "scripts/compute_econometrics.py",
    "scripts/stats/logit.py",
    "scripts/build_paper_tables.py",
]


def run(args, step=None):
    label = f"[{step}] " if step else ""
    print(f"{label}>>> {' '.join(args)}", flush=True)
    return subprocess.run(args, cwd=ROOT, check=True)


def pipeline():
    total = len(PIPELINE)
    for i, script in enumerate(PIPELINE, 1):
        print(f"--- passo {i}/{total}: {script}", flush=True)
        run([sys.executable, script], step=f"{i}/{total}")
    print("pipeline concluída: data/output/ atualizado.")


def test():
    run([sys.executable, "-m", "pytest", "-q"], step="test")


def main():
    ap = argparse.ArgumentParser(
        description="Executa a pipeline do Mapa do Trabalho Brasileiro sem make.")
    ap.add_argument("task", nargs="?", default="pipeline",
                    choices=["pipeline", "test"])
    args = ap.parse_args()
    if args.task == "pipeline":
        pipeline()
    else:
        test()


if __name__ == "__main__":
    main()