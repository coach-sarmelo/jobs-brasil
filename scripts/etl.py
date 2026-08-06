import csv
import json
import os
import re

RENDIMENTO_CSV = "/home/sarmelo/projeto empregos/Rendimento.csv"
WORKERS_CSV = "/home/sarmelo/projeto empregos/numero-trabalhadores.csv"
OUTPUT_JSON = os.path.join(os.path.dirname(__file__), "../src/data/jobs_br.json")

# Heuristic dictionary for AI Exposure Score based on CNAE Section/Keywords
AI_EXPOSURE_MAP = {
  "Informação e comunicação": 0.85,
  "Atividades financeiras, de seguros e serviços relacionados": 0.82,
  "Atividades profissionais, científicas e técnicas": 0.78,
  "Atividades administrativas e serviços complementares": 0.70,
  "Administração pública, defesa e seguridade social": 0.65,
  "Educação": 0.60,
  "Saúde humana e serviços sociais": 0.45,
  "Comércio, reparação de veículos automotores e motocicletas": 0.50,
  "Indústrias de transformação": 0.40,
  "Alojamento e alimentação": 0.30,
  "Construção": 0.25,
  "Transporte, armazenagem e correio": 0.35,
  "Agricultura, pecuária, produção florestal, pesca e aquicultura": 0.20,
}

def clean_float(val):
    if not val:
        return 0.0
    val_str = str(val).strip().replace('"', '').replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def clean_int(val):
    if not val:
        return 0
    val_str = str(val).strip().replace('"', '').replace('.', '')
    try:
        return int(val_str)
    except ValueError:
        return 0

def parse_code_and_name(full_text):
    full_text = full_text.strip().strip('"')
    match = re.match(r'^([0-9\.]+)\s+(.*)$', full_text)
    if match:
        return match.group(1), match.group(2)
    return "", full_text

def run_etl():
    rendimento_map = {}
    workers_map = {}
    
    with open(RENDIMENTO_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3 and row[0] == "Brasil":
                activity = row[1].strip()
                val = clean_float(row[2])
                rendimento_map[activity] = val

    with open(WORKERS_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3 and row[0] == "Brasil":
                activity = row[1].strip()
                val = clean_int(row[2])
                workers_map[activity] = val

    items = []
    sections = set()
    current_section = "Outros"
    
    total_country_workers = workers_map.get("Total", 87830899)
    total_country_income = rendimento_map.get("Total", 2850.64)

    for activity, workers in workers_map.items():
        if activity in ["Total", ""]:
            continue
            
        income = rendimento_map.get(activity, 0.0)
        if workers <= 0 or income <= 0:
            continue
            
        code, name = parse_code_and_name(activity)
        
        # Classify CNAE hierarchy level
        is_section = not code or len(code) == 1
        is_division = len(code) > 1 and code.count('.') == 1 and not code.replace('.', '').isdigit()
        is_class = len(code) > 4
        
        if is_section or re.match(r'^\d+\s', activity):
            current_section = name
            sections.add(name)
            
        ai_score = 0.40
        for sec_key, score in AI_EXPOSURE_MAP.items():
            if sec_key.lower() in current_section.lower() or sec_key.lower() in name.lower():
                ai_score = score
                break
                
        wage_bill = round(workers * income, 2)
        
        items.append({
            "id": code if code else activity,
            "full_name": activity,
            "code": code,
            "name": name,
            "section": current_section,
            "total_workers": workers,
            "avg_income": income,
            "wage_bill": wage_bill,
            "share_of_workforce": round((workers / total_country_workers) * 100, 4),
            "ai_exposure_score": ai_score,
            "is_section": is_section
        })

    output_data = {
        "totals": {
            "total_workers": total_country_workers,
            "avg_income": total_country_income,
            "total_wage_bill": round(total_country_workers * total_country_income, 2)
        },
        "sections": sorted(list(sections)),
        "items": items
    }
    
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"ETL completed successfully! Output written to {OUTPUT_JSON} ({len(items)} items)")

if __name__ == "__main__":
    run_etl()
