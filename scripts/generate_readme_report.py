import json
import os

SITE_DATA = os.path.join(os.path.dirname(__file__), "../site/data.json")
README_PATH = os.path.join(os.path.dirname(__file__), "../README.md")

def generate():
    with open(SITE_DATA, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    meta = data["meta"]
    occs = sorted(data["occupations"], key=lambda x: (x["exposure"], x["jobs"]), reverse=True)
    
    md = f"""# AI Exposure of the Brazilian Job Market (IBGE COD)

> **Réplica exata do projeto [karpathy/jobs](https://github.com/karpathy/jobs) de Andrej Karpathy adaptado para os microdados da PNAD Contínua / IBGE (2022).**

## Aggregate Statistics

- **Total Occupations (COD Subgroups):** {meta["total_occupations"]}
- **Total Jobs:** {meta["total_jobs"]:,}
- **Total Monthly Wages:** R$ {meta["total_wages"] / 1e9:.1f}B
- **Job-weighted Average AI Exposure:** **{meta["weighted_ai_exposure"]}/10**

---

## Breakdown by Exposure Tier

| Tier | Occupations | Jobs | % of Jobs | Monthly Wages | Avg Pay |
|---|---|---|---|---|---|
"""
    for tier_name, t in meta["tiers"].items():
        pct_jobs = (t["jobs"] / meta["total_jobs"]) * 100 if meta["total_jobs"] else 0
        avg_pay = (t["wages"] / t["jobs"]) if t["jobs"] else 0
        md += f"| {tier_name} | {t['count']} | {t['jobs']:,} | {pct_jobs:.1f}% | R$ {t['wages']/1e9:.1f}B | R$ {avg_pay:,.0f} |\n"

    md += """
---

## All Occupations (Sorted by AI Exposure)

| Code | Occupation | Section | Pay (R$) | Jobs | AI Exposure | Rationale |
|---|---|---|---|---|---|---|
"""
    for item in occs[:30]:
        md += f"| {item['code']} | **{item['name']}** | {item['section']} | R$ {item['pay']:,.0f} | {item['jobs']:,} | **{item['exposure']}/10** | {item['rationale']} |\n"

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(md)
        
    print(f"README report updated -> {README_PATH}")

if __name__ == "__main__":
    generate()
