import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from process_microdata import (  # noqa: E402
    COL_ANOS_ESTUDO,
    COL_ATIVIDADE,
    COL_CNPJ,
    COL_IDADE,
    COL_OCUP,
    COL_PESO,
    COL_POSICAO,
    COL_RACA,
    COL_RENDA,
    COL_SEXO,
    COL_UF,
    Accum,
    aggregate_quarter,
)

LINE_LEN = 440

SUBGRUPOS = {
    "111": {"name": "Diretor Geral", "grande_grupo": "DIRETORES E GERENTES", "subgrupo_principal": "Diretores"},
    "911": {"name": "Trabalhador de limpeza", "grande_grupo": "OCUPAÇÕES ELEMENTARES", "subgrupo_principal": "Limpeza"},
    # subgrupo "999" propositalmente ausente de SUBGRUPOS: cobre o filtro
    # defensivo `if sg in subgrupos` de aggregate_quarter.
}
GRUPO_BASE_TO_SUBGRUPO = {
    "0111": "111",
    "9111": "911",
    "8000": "999",
}
UF_CODES = {
    "11": {"sigla": "RO"},
    "35": {"sigla": "SP"},
}


def make_line(uf="35", peso="100.00000000", sexo="1", raca="1", ocup="0111", posicao="01", cnpj=" ", renda="3000", idade="35 ", anos_estudo="12", atividade="01"):
    chars = [" "] * LINE_LEN

    def place(sl, value):
        for i, ch in enumerate(value):
            chars[sl.start + i] = ch

    place(COL_UF, uf.rjust(2, "0")[:2])
    place(COL_PESO, peso.rjust(15, "0")[:15])
    place(COL_SEXO, sexo)
    place(COL_RACA, raca)
    place(COL_OCUP, ocup.rjust(4, "0")[:4])
    place(COL_POSICAO, posicao)
    place(COL_CNPJ, cnpj)
    place(COL_RENDA, renda.rjust(8, "0")[:8])
    place(COL_IDADE, idade.ljust(3)[:3])
    place(COL_ANOS_ESTUDO, anos_estudo.ljust(2)[:2])
    place(COL_ATIVIDADE, atividade.ljust(2)[:2])
    return "".join(chars)


def write_fixture(path, lines):
    with open(path, "w", encoding="latin-1") as f:
        for line in lines:
            f.write(line + "\n")


def test_aggregate_quarter_groups_by_grande_grupo(tmp_path):
    path = tmp_path / "microdados.txt"
    write_fixture(path, [
        make_line(uf="35", ocup="0111", posicao="01", renda="6000"),   # diretores, SP, formal
        make_line(uf="35", ocup="0111", posicao="01", renda="4000"),   # diretores, SP, formal
        make_line(uf="11", ocup="9111", posicao="10", renda="1200"),   # elementares, RO, informal
        make_line(uf="11", ocup="9111", posicao="10", renda="1000"),   # elementares, RO, informal
        make_line(uf="35", ocup="8000", posicao="01", renda="5000"),   # subgrupo "999" ausente -> desconhecida
        make_line(uf="99", ocup="0111", posicao="01", renda="9999"),   # UF não reconhecida -> descartada
    ])

    national, by_uf, skipped_unknown_occupation, _, _ = aggregate_quarter(
        str(path), SUBGRUPOS, GRUPO_BASE_TO_SUBGRUPO, UF_CODES, want_by_uf=False, group_by="grande_grupo",
    )

    assert set(national.keys()) == {"DIRETORES E GERENTES", "OCUPAÇÕES ELEMENTARES"}
    assert by_uf is None
    assert skipped_unknown_occupation == 1  # a linha do ocup "8000" (subgrupo "999" ausente)

    diretores = national["DIRETORES E GERENTES"]
    assert diretores.n == 2
    assert diretores.w == 200.0  # peso=100 por linha, 2 linhas

    elementares = national["OCUPAÇÕES ELEMENTARES"]
    assert elementares.n == 2
    assert elementares.w_informal == elementares.w  # ambas as linhas são informais (posicao "10")


def test_aggregate_quarter_by_uf_when_requested(tmp_path):
    path = tmp_path / "microdados.txt"
    write_fixture(path, [
        make_line(uf="35", ocup="0111"),
        make_line(uf="11", ocup="0111"),
    ])

    national, by_uf, _, _, _ = aggregate_quarter(
        str(path), SUBGRUPOS, GRUPO_BASE_TO_SUBGRUPO, UF_CODES, want_by_uf=True, group_by="grande_grupo",
    )

    assert national["DIRETORES E GERENTES"].n == 2
    assert set(by_uf.keys()) == {"SP", "RO"}
    assert by_uf["SP"]["DIRETORES E GERENTES"].n == 1
    assert by_uf["RO"]["DIRETORES E GERENTES"].n == 1


def test_aggregate_quarter_collects_sector_metrics(tmp_path):
    path = tmp_path / "microdados.txt"
    write_fixture(path, [
        make_line(ocup="0111", atividade="01", renda="5000", peso="10"),
        make_line(ocup="0111", atividade="01", renda="3000", peso="10"),
        make_line(ocup="9111", atividade="02", renda="1000", peso="5"),
        make_line(ocup="9999", atividade="02", renda="2000", peso="5"),  # totally unmapped occupation
    ])

    _, _, skipped, by_sector, sector_aggregates = aggregate_quarter(
        str(path), SUBGRUPOS, GRUPO_BASE_TO_SUBGRUPO, UF_CODES, want_by_uf=False, group_by="subgrupo",
    )

    assert skipped == 1
    
    assert set(by_sector.keys()) == {"01", "02"}
    assert by_sector["01"]["111"].n == 2
    assert by_sector["02"]["911"].n == 1
    assert "999" not in by_sector["02"]  # skipped unmapped occupations

    assert set(sector_aggregates.keys()) == {"01", "02"}
    assert sector_aggregates["01"].n == 2
    assert sector_aggregates["01"].w == 20.0
    
    # Sector 02 has 2 workers total, one from mapped and one from unmapped occupation.
    # Its aggregate should capture BOTH.
    assert sector_aggregates["02"].n == 2
    assert sector_aggregates["02"].w == 10.0


def test_aggregate_quarter_rejects_invalid_group_by(tmp_path):
    import pytest

    path = tmp_path / "microdados.txt"
    write_fixture(path, [make_line()])
    with pytest.raises(ValueError):
        aggregate_quarter(str(path), SUBGRUPOS, GRUPO_BASE_TO_SUBGRUPO, UF_CODES, group_by="ano")


def test_accum_merge_preserves_weighted_average_income():
    # A fusão de trimestres precisa somar pesos/somas antes de calcular
    # médias, não fazer "média das médias" — mesclar o mesmo trimestre
    # consigo mesmo 4x deve manter avg_income igual e quadruplicar n/w.
    base = Accum()
    for _ in range(25):
        base.add(weight=100.0, income=3000, sexo="1", raca="1", informal=False)
    for _ in range(25):
        base.add(weight=50.0, income=1000, sexo="2", raca="2", informal=True)

    single_metrics = base.to_metrics()
    assert single_metrics is not None  # n=50 >= MIN_SAMPLE_OCUPACAO

    merged = Accum()
    for _ in range(4):
        merged.merge(base)
    merged_metrics = merged.to_metrics()

    assert merged.n == base.n * 4
    assert merged.w == base.w * 4
    assert merged_metrics["avg_income"] == single_metrics["avg_income"]
    assert merged_metrics["total_workers"] == single_metrics["total_workers"] * 4


def test_accum_tracks_weighted_sum_of_squares_for_variance_estimation():
    # F4 (SPEC.md) precisa de Sigma(w^2) e Sigma(w*income^2) por subgrupo para
    # estimar erro padrao ponderado (n_eff de Kish) sem guardar os microdados
    # brutos, que sao descartados por design. 25 linhas homem/branco (peso=100,
    # renda=3000) + 25 linhas mulher/preta (peso=50, renda=1000) -> valores
    # calculados a mao.
    acc = Accum()
    for _ in range(25):
        acc.add(weight=100.0, income=3000, sexo="1", raca="1", informal=False)
    for _ in range(25):
        acc.add(weight=50.0, income=1000, sexo="2", raca="2", informal=True)

    assert acc.w_sq == 25 * 100.0 ** 2 + 25 * 50.0 ** 2
    assert acc.wsum_income_sq == 25 * 100.0 * 3000 ** 2 + 25 * 50.0 * 1000 ** 2
    assert acc.wsum_male_income_sq == 25 * 100.0 * 3000 ** 2
    assert acc.wsum_female_income_sq == 25 * 50.0 * 1000 ** 2
    assert acc.wsum_white_income_sq == 25 * 100.0 * 3000 ** 2
    assert acc.wsum_black_income_sq == 25 * 50.0 * 1000 ** 2

    metrics = acc.to_metrics()
    assert metrics is not None
    assert metrics["weight_sq_sum"] == acc.w_sq
    assert metrics["income_sq_weighted_sum"] == acc.wsum_income_sq
    assert metrics["male_income_sq_weighted_sum"] == acc.wsum_male_income_sq
    assert metrics["female_income_sq_weighted_sum"] == acc.wsum_female_income_sq
    assert metrics["white_income_sq_weighted_sum"] == acc.wsum_white_income_sq
    assert metrics["black_income_sq_weighted_sum"] == acc.wsum_black_income_sq


def test_accum_merge_sums_weighted_sum_of_squares():
    base = Accum()
    for _ in range(25):
        base.add(weight=100.0, income=3000, sexo="1", raca="1", informal=False)

    merged = Accum()
    merged.merge(base)
    merged.merge(base)

    assert merged.w_sq == base.w_sq * 2
    assert merged.wsum_income_sq == base.wsum_income_sq * 2


def test_accum_demographics_without_income():
    # Testa headcounts por gênero/raça e médias de idade e anos de estudo,
    # que devem ser independentes do filtro de renda > 0.
    acc = Accum()
    
    # 1. Mulher (2), preta (2), sem renda (0), 30 anos, 10 anos de estudo, peso 150
    for _ in range(10):
        acc.add(weight=15.0, income=0, sexo="2", raca="2", informal=False, idade=30, anos_estudo=10)
    
    # 2. Homem (1), branco (1), renda 1000, 40 anos, 15 anos de estudo, peso 50
    for _ in range(10):
        acc.add(weight=5.0, income=1000, sexo="1", raca="1", informal=False, idade=40, anos_estudo=15)
    
    # 3. Mulher (2), parda (4) -> negra, renda 2000, 20 anos, 5 anos de estudo, peso 200
    for _ in range(10):
        acc.add(weight=20.0, income=2000, sexo="2", raca="4", informal=False, idade=20, anos_estudo=5)

    metrics = acc.to_metrics()
    assert metrics is not None
    
    assert metrics["male_workers"] == 50
    assert metrics["female_workers"] == 350
    assert metrics["white_workers"] == 50
    assert metrics["black_workers"] == 350
    
    # avg_age = (150*30 + 50*40 + 200*20) / 400 = (4500 + 2000 + 4000) / 400 = 10500 / 400 = 26.25
    assert metrics["avg_age"] == 26.2
    
    # avg_study_years = (150*10 + 50*15 + 200*5) / 400 = (1500 + 750 + 1000) / 400 = 3250 / 400 = 8.125
    assert metrics["avg_study_years"] == 8.1

