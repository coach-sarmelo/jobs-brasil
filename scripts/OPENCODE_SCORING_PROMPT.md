# Prompt de Pontuação via opencode + DeepSeek

Este arquivo documenta o prompt exato usado para gerar os scores "llm" em
`scores.json`, para manter o processo auditável (ver seção "Transparência
Metodológica" do README). Não é executado por nenhum script — é colado
manualmente numa sessão do [opencode](https://opencode.ai) configurada com
DeepSeek como provedor/modelo.

Sempre que o prompt abaixo for alterado, atualize também esta nota e regenere
`scores.json` para manter os dois em sincronia.

---

## Prompt

```
Você é o motor de pontuação do projeto "Jobs BR". Sua tarefa é ler
cod_subgroups.json (lista de subgrupos ocupacionais COD do Brasil, cada um
com code, name, section, total_workers, avg_income, wage_bill) e produzir
scores.json com uma nota de exposição à Inteligência Artificial de 0 a 10
para CADA subgrupo, sem exceção e sem amostragem — processe os ~87 itens
inteiros, um por um.

RUBRICA (aplique com seu próprio julgamento, não apenas por palavra-chave):
- 0-1 Mínima: trabalho físico/braçal no campo ou obra (ex.: servente de
  pedreiro, lavoura manual, limpeza pesada).
- 2-3 Baixa: trabalho técnico presencial (eletricista, encanador, motorista,
  mecânico, bombeiro).
- 4-5 Moderada: trabalho presencial com rotinas (enfermagem presencial,
  policial, veterinário, balconista).
- 6-7 Alta: ensino, gestão, contabilidade, jornalismo.
- 8-9 Muito Alta: trabalho 100% digital no computador (desenvolvimento de
  software, design gráfico, análise de investimentos, tradução).
- 10 Máxima: digitador de dados, telemarketing, assistente de transcrição.

Heurística central: se o trabalho pode ser feito 100% de um home office num
computador (escrita, código, análise, comunicação), a exposição é
inerentemente alta (7+). Trabalhos que exigem presença física, habilidade
manual operacional ou interação em tempo real têm barreira física natural e
tendem a pontuação mais baixa.

REGRAS IMPORTANTES:
1. Escreva uma justificativa original de 2 frases em português para cada
   ocupação, específica ao subgrupo (nome + setor). NÃO reutilize frases
   genéricas fixas nem reaproveite a mesma frase para múltiplos subgrupos —
   isso já foi identificado como um problema de integridade neste projeto
   (ver git log / README) e deve ser evitado.
2. Para cada item, escreva em scores.json (chave = "code", ou "name" se
   "code" estiver vazio) exatamente este schema:
   {
     "code": "<code>",
     "name": "<name>",
     "section": "<section>",
     "score": <inteiro 0-10>,
     "rationale": "<justificativa original em português, 2 frases>",
     "method": "llm",
     "model": "<identificador exato do modelo que você está executando
                nesta sessão — não invente uma string genérica>",
     "generated_at": "<timestamp ISO-8601 UTC atual>"
   }
3. Preserve UTF-8 (acentos legíveis, ensure_ascii=False), indentação de 2
   espaços, e não deixe nenhum subgrupo de fora.
4. Só edite scores.json. Não modifique nenhum outro arquivo do repositório.
5. Ao terminar, rode `python3 -m pytest tests/test_score.py -v` e relate o
   resultado. Se falhar, corrija scores.json e rode de novo até passar.
```

---

## Como usar

1. Instale e autentique o opencode com DeepSeek como provedor (veja o README,
   seção "Pontuação via opencode + DeepSeek").
2. Abra uma sessão do opencode com working directory na raiz deste
   repositório.
3. Rode `python3 scripts/extract_cod_subgroups.py` antes, se
   `cod_subgroups.json` ainda não existir.
4. Cole o prompt acima integralmente.
5. Depois que o opencode terminar, rode localmente:
   ```bash
   python3 build_site_data.py
   python3 scripts/generate_readme_report.py
   python3 -m pytest tests/ -v
   ```
