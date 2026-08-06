import json
import os

SITE_DATA = os.path.join(os.path.dirname(__file__), "../site/data.json")
README_PATH = os.path.join(os.path.dirname(__file__), "../README.md")

MARKER_START = "<!-- AUTO-GENERATED-REPORT:START -->"
MARKER_END = "<!-- AUTO-GENERATED-REPORT:END -->"


def build_report(data):
    meta = data["meta"]
    occs = sorted(data["occupations"], key=lambda x: (x["exposure"], x["jobs"]), reverse=True)

    method_counts = meta.get("scoring_method_counts", {})
    method_summary = ", ".join(f"{k}: {v}" for k, v in method_counts.items()) or "n/d"

    md = f"""{MARKER_START}
<!-- Gerado automaticamente por scripts/generate_readme_report.py a partir de site/data.json. Não edite manualmente entre estes marcadores. -->

### Estatísticas Agregadas

- **Total de Ocupações (Subgrupos COD):** {meta["total_occupations"]}
- **Total de Trabalhadores:** {meta["total_jobs"]:,}
- **Massa Salarial Mensal Total:** R$ {meta["total_wages"] / 1e9:.2f} Bi
- **Exposição Média Ponderada à IA:** **{meta["weighted_ai_exposure"]}/10**
- **Método de pontuação (contagem por origem):** {method_summary}

### Distribuição por Tier de Exposição

| Tier | Ocupações | Empregos | % dos Empregos | Massa Salarial Mensal | Salário Médio |
|---|---|---|---|---|---|
"""
    for tier_name, t in meta["tiers"].items():
        pct_jobs = (t["jobs"] / meta["total_jobs"]) * 100 if meta["total_jobs"] else 0
        avg_pay = (t["wages"] / t["jobs"]) if t["jobs"] else 0
        md += f"| {tier_name} | {t['count']} | {t['jobs']:,} | {pct_jobs:.1f}% | R$ {t['wages']/1e9:.1f} Bi | R$ {avg_pay:,.0f} |\n"

    md += "\n### Top 30 Ocupações por Exposição à IA\n\n"
    md += "| Código | Ocupação | Setor | Renda (R$) | Trabalhadores | Exposição | Método | Justificativa |\n"
    md += "|---|---|---|---|---|---|---|---|\n"
    for item in occs[:30]:
        md += (
            f"| {item['code']} | **{item['name']}** | {item['section']} | "
            f"R$ {item['pay']:,.0f} | {item['jobs']:,} | **{item['exposure']}/10** | "
            f"{item.get('method', 'n/d')} | {item['rationale']} |\n"
        )

    md += f"\n{MARKER_END}"
    return md


def generate():
    with open(SITE_DATA, 'r', encoding='utf-8') as f:
        data = json.load(f)

    report = build_report(data)

    with open(README_PATH, 'r', encoding='utf-8') as f:
        readme = f.read()

    if MARKER_START in readme and MARKER_END in readme:
        before = readme.split(MARKER_START)[0]
        after = readme.split(MARKER_END)[1]
        readme = before + report + after
    else:
        readme = readme.rstrip() + "\n\n" + report + "\n"

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(readme)

    print(f"README report section updated -> {README_PATH}")


if __name__ == "__main__":
    generate()
