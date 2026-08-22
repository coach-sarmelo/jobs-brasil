# Mapa do Trabalho Brasileiro

Em 2026, 35 milhões de brasileiros trabalham em ocupações com exposição quase
nula à inteligência artificial. Este projeto investiga por quê — estimando
regressões ponderadas sobre 227.629 observações de microdados da **PNAD
Contínua (IBGE)**, cruzadas com o índice de exposição ocupacional de
[Eloundou et al. (2024)](https://doi.org/10.1126/science.adj0998).

> 🖥️ **Ver os resultados:** [Mapa do Trabalho Brasileiro — site interativo](https://coach-sarmelo.github.io/jobs-brasil/)

## O que este projeto mostra

- **Dados auditáveis** — microdados oficiais da PNAD Contínua (IBGE), peso
  amostral oficial `V1028`, safra 2026Q1.
- **Índice externo verificado** — exposição à IA pelo índice de
  Eloundou et al. (2024) (escala 0–10), combinado à informalidade e à
  qualificação.
- **Econometria reproduzível** — regressões ponderadas (WLS), especificações
  principais (S1–S4), bateria de robustez (R1–R7), estimação determinística
  sem LLM.
- **Cobertura nacional** — 12 grandes grupos ocupacionais, 27 UF e 5 regiões.
- **Disseminação em duas camadas** — artigo técnico em PDF e um site
  interativo que traduz os achados para leitores não acadêmicos.

## Estrutura do repositório

| Componente | Conteúdo |
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