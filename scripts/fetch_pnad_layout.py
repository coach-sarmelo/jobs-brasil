import json
import os
import re
import urllib.error
import urllib.request
import zipfile
import io

BASE_URL = "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados"
ZIP_NAME = "Documentacao/Dicionario_e_input_20221031.zip"
TARGET_SAS = "input_PNADC_trimestral.sas"

OUT_JSON = os.path.join(os.path.dirname(__file__), "reference", "pnadc_layout.json")

VARIABLES_OF_INTEREST = {
    "UF", "V1028", "V2007", "V2010", "V4010", 
    "VD4009", "V4019", "VD4016", "VD3005", "V2009", "VD4010"
}

def fetch_and_parse():
    url = f"{BASE_URL}/{ZIP_NAME}"
    print(f"Baixando dicionário e input SAS de {url} ...")
    
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            zip_data = response.read()
    except (urllib.error.URLError, OSError) as e:
        raise OSError(f"Falha ao baixar {url}: {e}") from e
        
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        sas_name = next(n for n in z.namelist() if TARGET_SAS in n)
        sas_content = z.read(sas_name).decode("latin-1")
        
    layout = {}
    # Busca formato típico do SAS INPUT: @0006 UF $2.
    pattern = re.compile(r'@\s*(\d+)\s+([A-Za-z0-9_]+)\s+\$?(\d+)')
    
    for line in sas_content.splitlines():
        match = pattern.search(line)
        if match:
            start = int(match.group(1))
            var_name = match.group(2)
            length = int(match.group(3))
            
            if var_name in VARIABLES_OF_INTEREST:
                layout[var_name] = {"start": start, "length": length}
                
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2)
        
    print(f"Salvo {len(layout)} variáveis em {OUT_JSON}")

if __name__ == "__main__":
    fetch_and_parse()
