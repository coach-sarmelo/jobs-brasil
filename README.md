# Mapa do Trabalho Brasileiro

Projeto de análise econômica que mede a **exposição ocupacional à inteligência
artificial, níveis de informalidade e qualificação** no mercado de trabalho
brasileiro, a partir de mais de **227 mil observações** de microdados da
**PNAD Contínua (IBGE)** e do índice de exposição à IA de
[Eloundou et al. (2024)](https://doi.org/10.1126/science.adj0998).

> 🖥️ **Explore o resultado interativo:** [Mapa do Trabalho Brasileiro — site](https://coach-sarmelo.github.io/jobs-brasil/)

## Sobre o projeto

Este projeto foi estruturado como um **estudo replicável de ponta a ponta**, do
dado bruto à publicação:

- **Dados confiáveis e auditáveis** — microdados oficiais da PNAD Contínua
  (IBGE), peso amostral oficial `V1028`, safra 2026Q1.
- **Metodologia transparente** — exposição à IA usando o índice acadêmico de
  Eloundou et al. (2024) (escala 0–10), combinado à informalidade e à
  qualificação.
- **Análise econométrica rigorosa** — estimação determinística por regressões
  ponderadas (WLS), especificações principais (S1–S4) e bateria de robustez
  (R1–R7), sem uso de LLM em nenhuma etapa do cálculo.
- **Cobertura nacional** — resultados para **12 grandes grupos ocupacionais**,
  todas as **27 UF** e as **5 regiões** do país.
- **Comunicação em camadas** — artigo técnico em PDF e um **site interativo**
  que traduz os achados para um público não acadêmico.

## Repositório

| Componente | Descrição |
|---|---|
| `scripts/` | Pipeline de download dos microdados, estimação (WLS, robustez), tabelas e figuras |
| `tests/` | Suíte de testes do pipeline (`pytest`) |
| `site/` | Site estático do companion (já compilado, safra 2026Q1) |
| `main.pdf` | Artigo de referência do projeto |

## Fonte de dados

- **PNAD Contínua (IBGE)** — microdados trimestrais, peso amostral oficial
  `V1028`.
- **Índice de exposição ocupacional à IA** — Eloundou et al. (2024),
  *Science*, escala 0–10.

## Licença

MIT. Veja [`LICENSE`](LICENSE).