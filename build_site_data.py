import json
import os

SUBGROUPS_FILE = os.path.join(os.path.dirname(__file__), "cod_subgroups.json")
SCORES_FILE = os.path.join(os.path.dirname(__file__), "scores.json")
OUTPUT_SITE_DATA = os.path.join(os.path.dirname(__file__), "site/data.json")

def build_data():
    with open(SUBGROUPS_FILE, 'r', encoding='utf-8') as f:
        subgroups = json.load(f)
    with open(SCORES_FILE, 'r', encoding='utf-8') as f:
        scores = json.load(f)

    total_jobs = sum(item["total_workers"] for item in subgroups)
    total_wages = sum(item["wage_bill"] for item in subgroups)

    weighted_exposure_sum = 0.0
    occupations = []
    method_counts = {}

    # Exposure Tiers
    tiers = {
        "Minimal (0-1)": {"jobs": 0, "wages": 0.0, "count": 0},
        "Low (2-3)": {"jobs": 0, "wages": 0.0, "count": 0},
        "Moderate (4-5)": {"jobs": 0, "wages": 0.0, "count": 0},
        "High (6-7)": {"jobs": 0, "wages": 0.0, "count": 0},
        "Very high (8-10)": {"jobs": 0, "wages": 0.0, "count": 0},
    }

    for item in subgroups:
        code = item["code"] or item["name"]
        score_data = scores.get(code, {"score": 4, "rationale": "Informação não disponível.", "method": "unavailable"})

        score = score_data["score"]
        rationale = score_data["rationale"]
        method = score_data.get("method", "unknown")
        workers = item["total_workers"]
        wage_bill = item["wage_bill"]
        income = item["avg_income"]

        weighted_exposure_sum += score * workers
        method_counts[method] = method_counts.get(method, 0) + 1

        if score <= 1: tier = "Minimal (0-1)"
        elif score <= 3: tier = "Low (2-3)"
        elif score <= 5: tier = "Moderate (4-5)"
        elif score <= 7: tier = "High (6-7)"
        else: tier = "Very high (8-10)"

        tiers[tier]["jobs"] += workers
        tiers[tier]["wages"] += wage_bill
        tiers[tier]["count"] += 1

        occupations.append({
            "code": code,
            "name": item["name"],
            "section": item["section"],
            "jobs": workers,
            "pay": income,
            "wage_bill": wage_bill,
            "exposure": score,
            "rationale": rationale,
            "method": method,
            "tier": tier
        })

    weighted_ai_exposure = round(weighted_exposure_sum / total_jobs, 2) if total_jobs > 0 else 0.0

    meta = {
        "total_occupations": len(occupations),
        "total_jobs": total_jobs,
        "total_wages": total_wages,
        "weighted_ai_exposure": weighted_ai_exposure,
        "tiers": tiers,
        "scoring_method_counts": method_counts
    }

    os.makedirs(os.path.dirname(OUTPUT_SITE_DATA), exist_ok=True)
    with open(OUTPUT_SITE_DATA, 'w', encoding='utf-8') as f:
        json.dump({"meta": meta, "occupations": occupations}, f, ensure_ascii=False, indent=2)

    print(f"Site data built successfully -> {OUTPUT_SITE_DATA}")

if __name__ == "__main__":
    build_data()
