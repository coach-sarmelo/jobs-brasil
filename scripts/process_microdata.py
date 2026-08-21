import json
import os
from datetime import datetime, timezone

# Layout extraído automaticamente do dicionário SAS oficial do IBGE
# (ver scripts/fetch_pnad_layout.py para proveniência).
REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")
LAYOUT_JSON = os.path.join(REFERENCE_DIR, "pnadc_layout.json")

def _make_slice(var_info):
    start = var_info["start"] - 1
    return slice(start, start + var_info["length"])

with open(LAYOUT_JSON, encoding="utf-8") as f:
    _layout = json.load(f)

COL_UF = _make_slice(_layout["UF"])
COL_PESO = _make_slice(_layout["V1028"])
COL_SEXO = _make_slice(_layout["V2007"])
COL_RACA = _make_slice(_layout["V2010"])
COL_OCUP = _make_slice(_layout["V4010"])
COL_POSICAO = _make_slice(_layout["VD4009"])
COL_CNPJ = _make_slice(_layout["V4019"])
COL_RENDA = _make_slice(_layout["VD4016"])

# Novas variáveis
COL_IDADE = _make_slice(_layout["V2009"])
COL_ANOS_ESTUDO = _make_slice(_layout["VD3005"])
COL_ATIVIDADE = _make_slice(_layout["VD4010"])

# VD4009: categorias "com carteira"/estatutário/militar são sempre formais;
# empregador (8) e conta-própria (9) dependem do CNPJ (V4019); trabalhador
# familiar auxiliar (10) é sempre informal. Esta é a definição de informalidade
# publicada pelo próprio IBGE nas notas metodológicas da PNAD Contínua.
FORMAL_SEMPRE = {"01", "03", "05", "07"}
DEPENDE_CNPJ = {"08", "09"}
INFORMAL_SEMPRE = {"02", "04", "06", "10"}

MIN_SAMPLE_OCUPACAO = 20   # amostra mínima (não ponderada) p/ publicar uma ocupação numa UF
MIN_SAMPLE_GRUPO = 15      # amostra mínima por grupo (homem/mulher, branco/preto+pardo) p/ publicar um gap

# Regra de cobertura gravada no bloco `meta` dos artefatos (mesmo texto de
# scripts/compute_ai_exposure.py).
COVERAGE_DEFINITION = "Ocupacoes sem correspondencia O*NET-SOC ficam com exposicao null"

OUTPUT_NATIONAL = os.path.join(os.path.dirname(__file__), "../data/output/cod_subgroups.json")
OUTPUT_BY_UF = os.path.join(os.path.dirname(__file__), "../data/output/cod_subgroups_by_uf.json")
OUTPUT_UF_TOTALS = os.path.join(os.path.dirname(__file__), "../data/output/uf_totals.json")
OUTPUT_BY_SECTOR = os.path.join(os.path.dirname(__file__), "../data/output/cod_subgroups_by_sector.json")
OUTPUT_SECTOR_METRICS = os.path.join(os.path.dirname(__file__), "../data/output/sector_metrics.json")


def is_informal(posicao, cnpj):
    if posicao in FORMAL_SEMPRE:
        return False
    if posicao in INFORMAL_SEMPRE:
        return True
    if posicao in DEPENDE_CNPJ:
        return cnpj != "1"
    return None  # posição não aplicável / ignorada


class Accum:
    __slots__ = (
        "n", "w", "w_sq",
        "n_income", "w_income", "wsum_income", "wsum_income_sq",
        "n_informal_known", "w_informal_known", "w_informal",
        "n_male", "w_male_income", "wsum_male_income", "wsum_male_income_sq",
        "n_female", "w_female_income", "wsum_female_income", "wsum_female_income_sq",
        "n_white", "w_white_income", "wsum_white_income", "wsum_white_income_sq",
        "n_black", "w_black_income", "wsum_black_income", "wsum_black_income_sq",
        "w_male", "w_female", "w_white", "w_black",
        "w_idade", "wsum_idade", "w_anos_estudo", "wsum_anos_estudo",
    )

    def __init__(self):
        for slot in self.__slots__:
            setattr(self, slot, 0)

    def add(self, weight, income, sexo, raca, informal, idade=None, anos_estudo=None):
        self.n += 1
        self.w += weight
        self.w_sq += weight ** 2

        if sexo == "1":
            self.w_male += weight
        elif sexo == "2":
            self.w_female += weight

        if raca == "1":
            self.w_white += weight
        elif raca in ("2", "4"):  # pretos + pardos
            self.w_black += weight

        if idade is not None:
            self.w_idade += weight
            self.wsum_idade += weight * idade

        if anos_estudo is not None:
            self.w_anos_estudo += weight
            self.wsum_anos_estudo += weight * anos_estudo

        if income and income > 0:
            self.n_income += 1
            self.w_income += weight
            self.wsum_income += weight * income
            self.wsum_income_sq += weight * income ** 2

            if sexo == "1":
                self.n_male += 1
                self.w_male_income += weight
                self.wsum_male_income += weight * income
                self.wsum_male_income_sq += weight * income ** 2
            elif sexo == "2":
                self.n_female += 1
                self.w_female_income += weight
                self.wsum_female_income += weight * income
                self.wsum_female_income_sq += weight * income ** 2

            if raca == "1":
                self.n_white += 1
                self.w_white_income += weight
                self.wsum_white_income += weight * income
                self.wsum_white_income_sq += weight * income ** 2
            elif raca in ("2", "4"):  # pretos + pardos
                self.n_black += 1
                self.w_black_income += weight
                self.wsum_black_income += weight * income
                self.wsum_black_income_sq += weight * income ** 2

        if informal is not None:
            self.n_informal_known += 1
            self.w_informal_known += weight
            if informal:
                self.w_informal += weight

    def merge(self, other):
        for slot in self.__slots__:
            setattr(self, slot, getattr(self, slot) + getattr(other, slot))
        return self

    def to_metrics(self):
        if self.n < MIN_SAMPLE_OCUPACAO or self.w_income <= 0:
            return None

        avg_income = self.wsum_income / self.w_income

        informality_rate = None
        if self.w_informal_known > 0:
            informality_rate = round(100 * self.w_informal / self.w_informal_known, 1)

        male_avg = self.wsum_male_income / self.w_male_income if self.w_male_income > 0 else None
        female_avg = self.wsum_female_income / self.w_female_income if self.w_female_income > 0 else None
        gender_gap_pct = None
        if male_avg and female_avg and self.n_male >= MIN_SAMPLE_GRUPO and self.n_female >= MIN_SAMPLE_GRUPO:
            gender_gap_pct = round(100 * (male_avg - female_avg) / male_avg, 1)

        white_avg = self.wsum_white_income / self.w_white_income if self.w_white_income > 0 else None
        black_avg = self.wsum_black_income / self.w_black_income if self.w_black_income > 0 else None
        race_gap_pct = None
        if white_avg and black_avg and self.n_white >= MIN_SAMPLE_GRUPO and self.n_black >= MIN_SAMPLE_GRUPO:
            race_gap_pct = round(100 * (white_avg - black_avg) / white_avg, 1)

        return {
            "total_workers": round(self.w),
            "avg_income": round(avg_income, 2),
            "wage_bill": round(self.wsum_income, 2),
            "informality_rate": informality_rate,
            "gender_gap_pct": gender_gap_pct,
            "male_avg_income": round(male_avg, 2) if male_avg else None,
            "female_avg_income": round(female_avg, 2) if female_avg else None,
            "race_gap_pct": race_gap_pct,
            "white_avg_income": round(white_avg, 2) if white_avg else None,
            "black_avg_income": round(black_avg, 2) if black_avg else None,
            "sample_size": self.n,
            "weight_sq_sum": round(self.w_sq, 2),
            "income_sq_weighted_sum": round(self.wsum_income_sq, 2),
            "male_income_sq_weighted_sum": round(self.wsum_male_income_sq, 2),
            "female_income_sq_weighted_sum": round(self.wsum_female_income_sq, 2),
            "white_income_sq_weighted_sum": round(self.wsum_white_income_sq, 2),
            "black_income_sq_weighted_sum": round(self.wsum_black_income_sq, 2),
            # Denominadores (soma de pesos) para SE ponderado — scripts/stats/weighted.py
            # precisa de w_sum por subgrupo, não só da média já calculada acima.
            "income_weight_sum": round(self.w_income, 2),
            "male_income_weight_sum": round(self.w_male_income, 2) if male_avg else None,
            "female_income_weight_sum": round(self.w_female_income, 2) if female_avg else None,
            "white_income_weight_sum": round(self.w_white_income, 2) if white_avg else None,
            "black_income_weight_sum": round(self.w_black_income, 2) if black_avg else None,
            "informal_weight_sum": round(self.w_informal_known, 2) if informality_rate is not None else None,
            "informal_weight_numerator": round(self.w_informal, 2) if informality_rate is not None else None,
            "male_workers": round(self.w_male),
            "female_workers": round(self.w_female),
            "white_workers": round(self.w_white),
            "black_workers": round(self.w_black),
            "avg_age": round(self.wsum_idade / self.w_idade, 1) if self.w_idade > 0 else None,
            "avg_study_years": round(self.wsum_anos_estudo / self.w_anos_estudo, 1) if self.w_anos_estudo > 0 else None,
        }


def load_reference():
    with open(os.path.join(REFERENCE_DIR, "cod_estrutura.json"), encoding="utf-8") as f:
        estrutura = json.load(f)
    with open(os.path.join(REFERENCE_DIR, "uf_codes.json"), encoding="utf-8") as f:
        uf_codes = json.load(f)
    return estrutura["subgrupos"], estrutura["grupo_base_to_subgrupo"], uf_codes


def aggregate_quarter(source, subgrupos, grupo_base_to_subgrupo, uf_codes, want_by_uf=True, group_by="subgrupo", write_individual_csv=False):
    """Agrega um trimestre de microdados em Accum por chave (subgrupo COD ou grande grupo).

    Preserva o comportamento original: um registro só entra em national/by_uf se
    a UF for reconhecida, mesmo quando want_by_uf=False (o filtro de UF não é
    exclusivo do by_uf, é um filtro de qualidade do registro).
    """
    if group_by == "subgrupo":
        grupo_base_to_key = grupo_base_to_subgrupo
    elif group_by == "grande_grupo":
        grupo_base_to_key = {
            gb: subgrupos[sg]["grande_grupo"].strip()
            for gb, sg in grupo_base_to_subgrupo.items()
            if sg in subgrupos
        }
    else:
        raise ValueError(f"group_by inválido: {group_by!r}")

    national = {}
    by_uf = {}
    by_sector = {}
    sector_aggregates = {}
    skipped_unknown_occupation = 0

    if isinstance(source, str):
        f = open(source, encoding="latin-1")
        close_file = True
    else:
        f = source
        close_file = False

    csv_file = None
    csv_writer = None
    if write_individual_csv:
        import csv
        csv_path = os.path.join(os.path.dirname(__file__), "../data/output/individual_microdata.csv")
        csv_file = open(csv_path, "w", encoding="utf-8", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["uf", "occupation", "weight", "income", "sex", "race", "informal", "age", "years_of_study"])

    try:
        for line in f:
            ocup = line[COL_OCUP].strip()
            if not ocup:
                continue  # não ocupado no trabalho principal

            uf_code = line[COL_UF]
            uf = uf_codes.get(uf_code)
            if uf is None:
                continue

            weight = float(line[COL_PESO])
            renda_raw = line[COL_RENDA].strip()
            income = int(renda_raw) if renda_raw else 0
            sexo = line[COL_SEXO].strip()
            raca = line[COL_RACA].strip()
            posicao = line[COL_POSICAO].strip()
            cnpj = line[COL_CNPJ].strip()
            informal = is_informal(posicao, cnpj)
            
            idade_raw = line[COL_IDADE].strip()
            idade = int(idade_raw) if idade_raw else None
            
            anos_raw = line[COL_ANOS_ESTUDO].strip()
            anos_estudo = int(anos_raw) if anos_raw else None

            atividade = line[COL_ATIVIDADE].strip()
            if atividade:
                sector_aggregates.setdefault(atividade, Accum()).add(weight, income, sexo, raca, informal, idade, anos_estudo)

            key = grupo_base_to_key.get(ocup)
            if key is None:
                skipped_unknown_occupation += 1
                continue
                
            if csv_writer is not None:
                informal_val = int(informal) if informal is not None else ""
                age_val = idade if idade is not None else ""
                study_val = anos_estudo if anos_estudo is not None else ""
                csv_writer.writerow([uf["sigla"], key, weight, income, sexo, raca, informal_val, age_val, study_val])

            national.setdefault(key, Accum()).add(weight, income, sexo, raca, informal, idade, anos_estudo)

            if want_by_uf:
                uf_bucket = by_uf.setdefault(uf["sigla"], {})
                uf_bucket.setdefault(key, Accum()).add(weight, income, sexo, raca, informal, idade, anos_estudo)

            if atividade:
                sec_bucket = by_sector.setdefault(atividade, {})
                sec_bucket.setdefault(key, Accum()).add(weight, income, sexo, raca, informal, idade, anos_estudo)

    finally:
        if csv_file is not None:
            csv_file.close()
        if close_file:
            f.close()

    return national, (by_uf if want_by_uf else None), skipped_unknown_occupation, by_sector, sector_aggregates


def build_rows(accums, subgrupos):
    rows = []
    for code, acc in accums.items():
        metrics = acc.to_metrics()
        if metrics is None:
            continue
        meta = subgrupos[code]
        rows.append({
            "code": code,
            "name": meta["name"].strip(),
            "section": meta["grande_grupo"].strip().capitalize(),
            "subgrupo_principal": meta["subgrupo_principal"].strip().capitalize(),
            **metrics,
        })
    rows.sort(key=lambda r: -r["total_workers"])
    return rows


def process(path=None):
    subgrupos, grupo_base_to_subgrupo, uf_codes = load_reference()

    if path is None:
        path = os.getenv("MICRODATA_TXT")
        
    if path is None:
        import fetch_ibge_microdata as fim
        print(f"Streaming data for {fim.YEAR} Q{fim.QUARTER}...")
        source = fim.fetch_quarter(fim.YEAR, fim.QUARTER)
        source_url = fim.BASE_URL
    else:
        source = path
        source_url = os.path.abspath(path)

    # Bloco `meta` (Fix 1 do vintage-fix-plan): identifica a safra dos dados e
    # as regras de cobertura/supressao; gravado no topo dos tres artefatos.
    meta = {
        "survey_year": int(os.getenv("IBGE_MICRODATA_YEAR", "2026")),
        "survey_quarter": int(os.getenv("IBGE_MICRODATA_QUARTER", "1")),
        "source": source_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage_definition": COVERAGE_DEFINITION,
        "sample_suppression_thresholds": {
            "min_sample_ocupacao": MIN_SAMPLE_OCUPACAO,
            "min_sample_grupo": MIN_SAMPLE_GRUPO,
        },
    }

    national, by_uf, skipped_unknown_occupation, by_sector, sector_aggregates = aggregate_quarter(
        source, subgrupos, grupo_base_to_subgrupo, uf_codes, want_by_uf=True, group_by="subgrupo", write_individual_csv=True
    )

    national_rows = build_rows(national, subgrupos)
    with open(OUTPUT_NATIONAL, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "occupations": national_rows}, f, ensure_ascii=False, indent=2)

    by_uf_rows = {sigla: build_rows(accums, subgrupos) for sigla, accums in sorted(by_uf.items())}
    with open(OUTPUT_BY_UF, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, **by_uf_rows}, f, ensure_ascii=False, indent=2)

    uf_totals = {sigla: round(sum(acc.w for acc in accums.values())) for sigla, accums in sorted(by_uf.items())}
    with open(OUTPUT_UF_TOTALS, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, **uf_totals}, f, ensure_ascii=False, indent=2)

    by_sector_rows = {sector: build_rows(accums, subgrupos) for sector, accums in sorted(by_sector.items())}
    with open(OUTPUT_BY_SECTOR, "w", encoding="utf-8") as f:
        json.dump(by_sector_rows, f, ensure_ascii=False, indent=2)

    sector_metrics = {}
    for sector, acc in sector_aggregates.items():
        metrics = acc.to_metrics()
        if metrics:
            sector_metrics[sector] = metrics
    with open(OUTPUT_SECTOR_METRICS, "w", encoding="utf-8") as f:
        json.dump(sector_metrics, f, ensure_ascii=False, indent=2)

    total_workers = sum(r["total_workers"] for r in national_rows)
    print(f"Processadas {sum(a.n for a in national.values())} pessoas ocupadas em {len(national_rows)} "
          f"subgrupos COD (Brasil), total ponderado = {total_workers:,} trabalhadores.")
    if skipped_unknown_occupation:
        print(f"Aviso: {skipped_unknown_occupation} registros com código de ocupação fora da "
              "Estrutura_Ocupacao_COD.xls foram ignorados.")
    print(f"-> {OUTPUT_NATIONAL}")
    print(f"-> {OUTPUT_BY_UF} ({len(by_uf_rows)} UFs)")
    print(f"-> {OUTPUT_BY_SECTOR} ({len(by_sector_rows)} setores)")
    print(f"-> {OUTPUT_SECTOR_METRICS} ({len(sector_metrics)} setores)")


if __name__ == "__main__":
    process()
