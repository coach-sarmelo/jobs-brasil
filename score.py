import json
import os
import time

INPUT_SUBGROUPS = os.path.join(os.path.dirname(__file__), "cod_subgroups.json")
OUTPUT_SCORES = os.path.join(os.path.dirname(__file__), "scores.json")

# Heuristic scoring table for offline mode or initial seeding
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
    api_key = os.getenv("GEMINI_API_KEY")
    client = None
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
        except Exception as e:
            print(f"Could not initialize Gemini Client: {e}")

    print(f"Scoring {len(subgroups)} COD subgroups...")

    for item in subgroups:
        code = item["code"] or item["name"]
        name = item["name"]
        section = item["section"]
        
        score, rationale = get_heuristic_score(name, section)
        
        # If Gemini API key is available, score via Gemini API
        if client:
            try:
                prompt = f"""Avalie a exposição à Inteligência Artificial (0 a 10) para a seguinte ocupação no Brasil:
Ocupação: {name} (Setor: {section})

Rubrica:
0-1 Mínima: Trabalho físico/braçal no campo ou obra.
2-3 Baixa: Trabalho técnico presencial (eletricista, mecânico).
4-5 Moderada: Trabalho presencial com rotinas (enfermagem, polícia).
6-7 Alta: Ensino, gestão, contabilidade.
8-9 Muito Alta: Trabalho 100% digital no computador (desenvolvimento de software, design, redação).
10 Máxima: Digitador, telemarketing.

Responda EXATAMENTE neste formato JSON:
{{"score": X, "rationale": "Justificativa em 2 frases em português."}}
"""
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                text = response.text.strip()
                if "{" in text:
                    json_str = text[text.find("{"):text.rfind("}")+1]
                    res = json.loads(json_str)
                    score = int(res.get("score", score))
                    rationale = res.get("rationale", rationale)
            except Exception as e:
                print(f"Fallback for {name}: {e}")


        scores[code] = {
            "code": code,
            "name": name,
            "section": section,
            "score": score,
            "rationale": rationale
        }

    with open(OUTPUT_SCORES, 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved {len(scores)} scores to {OUTPUT_SCORES}")

if __name__ == "__main__":
    run_scoring()
