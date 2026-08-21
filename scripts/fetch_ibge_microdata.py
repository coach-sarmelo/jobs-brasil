import os
import re
import urllib.error
import urllib.request
import zipfile


class QuarterUnavailable(RuntimeError):
    """O IBGE ainda não publicou este trimestre — não é uma falha transitória de rede."""

# PNAD Contínua microdados trimestrais publicados pelo IBGE via FTP público.
# Layout fixo desde 1o tri/2012 (ver Documentacao/Dicionario_e_input_20221031.zip),
# então qualquer trimestre novo funciona com o mesmo parser em process_microdata.py.
YEAR = os.getenv("IBGE_MICRODATA_YEAR", "2026")
QUARTER = os.getenv("IBGE_MICRODATA_QUARTER", "1")

BASE_URL = (
    "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
    "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados"
)


def resolve_zip_name(year, quarter, dir_url):
    """Descobre o nome real do .zip de um trimestre listando o diretório do IBGE.

    O IBGE republica trimestres antigos com um sufixo de data de revisão
    variável (ex.: PNADC_012020_20250815.zip); só o trimestre mais recente e
    ainda não revisado usa o nome sem sufixo (ex.: PNADC_012026.zip). Por isso
    o nome não pode ser montado diretamente a partir de ano/trimestre.
    """
    pattern = re.compile(rf'href="(PNADC_{quarter.zfill(2)}{year}(?:_\d+)?\.zip)"')
    try:
        with urllib.request.urlopen(dir_url, timeout=60) as response:
            html = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError:
        return None
    matches = pattern.findall(html)
    if not matches:
        return None
    # Se houver mais de uma revisão publicada, o sufixo de data mais recente
    # ordena por último lexicograficamente (AAAAMMDD).
    return sorted(matches)[-1]


def fetch_quarter(year, quarter):
    """Baixa o zip do trimestre, extrai e decodifica o txt em memória."""
    import io
    dir_url = f"{BASE_URL}/{year}/"
    zip_name = resolve_zip_name(year, quarter, dir_url)
    if zip_name is None:
        raise QuarterUnavailable(
            f"IBGE não tem microdados para {quarter}o tri/{year} ainda. "
            "Ajuste IBGE_MICRODATA_YEAR/IBGE_MICRODATA_QUARTER "
            f"para o trimestre mais recente disponível em {dir_url}."
        )

    zip_url = f"{dir_url}{zip_name}"

    print(f"Baixando {zip_url} para a memória...")
    try:
        with urllib.request.urlopen(zip_url, timeout=120) as response:
            zip_bytes = response.read()
    except (urllib.error.URLError, OSError) as e:
        raise OSError(f"Falha ao baixar {zip_url}: {e}") from e

    size_mb = len(zip_bytes) / (1024 * 1024)
    print(f"-> ({size_mb:.0f} MB baixados)")

    print("Extraindo microdados fixed-width em memória...")
    buf = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(buf) as z:
        member = next(n for n in z.namelist() if n.endswith(".txt"))
        with z.open(member) as f:
            yield from io.TextIOWrapper(f, encoding="latin-1")


def fetch():
    lines = fetch_quarter(YEAR, QUARTER)
    # Exaustão do stream (apenas para teste standalone do fetcher)
    count = 0
    for _ in lines:
        count += 1
    print(f"Lidas {count} linhas de microdados do trimestre {QUARTER}/{YEAR}.")


if __name__ == "__main__":
    fetch()
