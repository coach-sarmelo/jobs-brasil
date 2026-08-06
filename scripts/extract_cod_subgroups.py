import csv
import json
import os
import re

RENDIMENTO_CSV = "/home/sarmelo/projeto empregos/Rendimento.csv"
WORKERS_CSV = "/home/sarmelo/projeto empregos/numero-trabalhadores.csv"
OUTPUT_JSON = os.path.join(os.path.dirname(__file__), "../cod_subgroups.json")

def clean_float(val):
    if not val: return 0.0
    val_str = str(val).strip().replace('"', '').replace(',', '.')
    try: return float(val_str)
    except ValueError: return 0.0

def clean_int(val):
    if not val: return 0
    val_str = str(val).strip().replace('"', '').replace('.', '')
    try: return int(val_str)
    except ValueError: return 0

def extract():
    rendimento_map = {}
    workers_map = {}
    
    with open(RENDIMENTO_CSV, mode='r', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 3 and row[0] == "Brasil":
                rendimento_map[row[1].strip()] = clean_float(row[2])

    with open(WORKERS_CSV, mode='r', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 3 and row[0] == "Brasil":
                workers_map[row[1].strip()] = clean_int(row[2])

    subgroups = []
    current_section = "Outros"

    for activity, workers in workers_map.items():
        if activity in ["Total", ""]: continue
        income = rendimento_map.get(activity, 0.0)
        if workers <= 0 or income <= 0: continue
        
        match = re.match(r'^([0-9\.]+)\s+(.*)$', activity.strip('"'))
        if match:
            code, name = match.group(1), match.group(2)
        else:
            code, name = "", activity

        # Detect CNAE / COD Section header
        if not code or len(code) == 1:
            current_section = name
            continue
            
        # Target main 2-digit / 3-digit subgroups (approx ~96 items)
        if code.count('.') == 1 or (len(code) <= 6 and not code.replace('.', '').isdigit()):
            wage_bill = round(workers * income, 2)
            subgroups.append({
                "code": code,
                "name": name,
                "section": current_section,
                "total_workers": workers,
                "avg_income": income,
                "wage_bill": wage_bill
            })

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(subgroups, f, ensure_ascii=False, indent=2)
        
    print(f"Extracted {len(subgroups)} COD subgroups into {OUTPUT_JSON}")

if __name__ == "__main__":
    extract()
