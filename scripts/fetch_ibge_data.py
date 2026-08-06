import csv
import json
import os
import urllib.request

TABLE_ID = "10287"
# Table 10287 has only ever been published for a single reference year (2022)
# by IBGE — there is no newer period to fetch as of this writing. This is
# configurable so a future year can be picked up with no code change once
# (if) IBGE extends the series.
PERIOD = os.getenv("IBGE_PERIOD", "2022")

VAR_WORKERS = "13535"  # Pessoas ocupadas com rendimento de trabalho
VAR_INCOME = "13536"   # Rendimento médio mensal nominal de todos os trabalhos

# n1/1 = Brasil, c2/6794 = Sexo Total, c86/95251 = Cor ou raça Total,
# c12390/all = todas as categorias de Seção/divisão/classe de atividade
API_URL = (
    f"https://apisidra.ibge.gov.br/values/t/{TABLE_ID}/n1/1/v/{{var}}/p/{PERIOD}"
    f"/c2/6794/c86/95251/c12390/all?formato=json"
)

RENDIMENTO_CSV = os.path.join(os.path.dirname(__file__), "../data/raw/Rendimento.csv")
WORKERS_CSV = os.path.join(os.path.dirname(__file__), "../data/raw/numero-trabalhadores.csv")


def fetch_variable(var_id):
    url = API_URL.format(var=var_id)
    with urllib.request.urlopen(url, timeout=60) as response:
        rows = json.load(response)
    # First element is the header/label row (D6N == "Seção, divisão e ...");
    # data rows have a numeric D3C (Ano).
    return [r for r in rows if r.get("D3C") == PERIOD]


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["Fonte", "Atividade", "Valor"])
        writer.writerow(["", f"Tabela {TABLE_ID} (IBGE/SIDRA) — PNAD Contínua {PERIOD}", ""])
        for r in rows:
            writer.writerow(["Brasil", r["D6N"], r["V"]])


def fetch():
    workers = fetch_variable(VAR_WORKERS)
    income = fetch_variable(VAR_INCOME)

    if not workers or not income:
        raise RuntimeError(
            f"API do SIDRA não retornou dados para a Tabela {TABLE_ID}/período {PERIOD}. "
            "Verifique se o período ainda existe (ver IBGE_PERIOD)."
        )

    write_csv(WORKERS_CSV, workers)
    write_csv(RENDIMENTO_CSV, income)

    total = next((r["V"] for r in workers if r["D6N"] == "Total"), "?")
    print(f"Baixados {len(workers)} registros de trabalhadores e {len(income)} de renda "
          f"(Tabela {TABLE_ID}, período {PERIOD}, total Brasil = {total}).")
    print(f"-> {WORKERS_CSV}")
    print(f"-> {RENDIMENTO_CSV}")


if __name__ == "__main__":
    fetch()
