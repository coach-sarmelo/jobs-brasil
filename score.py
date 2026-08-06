import json
import os
from datetime import datetime, timezone

INPUT_SUBGROUPS = os.path.join(os.path.dirname(__file__), "cod_subgroups.json")
OUTPUT_SCORES = os.path.join(os.path.dirname(__file__), "scores.json")

HEURISTIC_METHOD = "heuristic-keyword-v1"

# Heuristic scoring table — deterministic baseline, no external LLM calls.
# LLM-sourced scores (method="llm") are produced separately via an opencode +
# DeepSeek session that edits scores.json directly — see
# scripts/OPENCODE_SCORING_PROMPT.md and the README's "Transparência
# Metodológica" section.
HEURISTIC_SCORES = {
    "tecnologia": (9, "Trabalho 100% digital em computador focado em código, análise de dados e arquitetura, áreas em rápida evolução por IA."),
    "informação": (8, "Processamento de informação digital, redação e suporte técnico altamente expostos a LLMs."),
    "financeira": (8, "Análise de dados financeiros, contabilidade e gestão de risco digitalmente automatizáveis."),
    "administrativ": (7, "Rotinas de escritório, fluxo de documentos e atendimento ao cliente suscetíveis à automação por agentes de IA."),
    "educação": (6, "Ensino e criação de conteúdo instrucional com alto potencial de suporte por IA, mantendo interação humana."),
    "saúde": (4, "Atendimento presencial e cuidados médicos com barreira física, combinando diagnósticos digitais."),
    "comércio": (5, "Vendas e atendimento com mix de atendimento presencial e automação e-commerce."),
    "construção": (2, "Trabalho predominantemente físico, manual e presencial nos canteiros de obras."),
    "agricultura": (2, "Atividade física e operational no campo com baixa substituição direta por software de IA."),
    "transporte": (3, "Operação de veículos e logística física com automação gradual.")
}


def get_heuristic_score(name, section):
    text = (name + " " + section).lower()
    for kw, (score, rat) in HEURISTIC_SCORES.items():
        if kw in text:
            return score, rat
    return 4, "Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas."


def run_scoring():
    if not os.path.exists(INPUT_SUBGROUPS):
        from scripts.extract_cod_subgroups import extract
        extract()

    with open(INPUT_SUBGROUPS, 'r', encoding='utf-8') as f:
        subgroups = json.load(f)

    scores = {}
    print(f"Scoring {len(subgroups)} COD subgroups (motor heurístico local)...")

    for item in subgroups:
        code = item["code"] or item["name"]
        name = item["name"]
        section = item["section"]

        score, rationale = get_heuristic_score(name, section)

        scores[code] = {
            "code": code,
            "name": name,
            "section": section,
            "score": score,
            "rationale": rationale,
            "method": HEURISTIC_METHOD,
            "model": None,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    with open(OUTPUT_SCORES, 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved {len(scores)} heuristic scores to {OUTPUT_SCORES}")
    print("Para pontuação via LLM (DeepSeek), use o fluxo opencode descrito no README.")


if __name__ == "__main__":
    run_scoring()
