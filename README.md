# Mapa do Trabalho Brasileiro

Exposição ocupacional à IA, informalidade e qualificação no Brasil, modelada a
partir dos microdados da PNAD Contínua (IBGE) e do índice de exposição de
[Eloundou et al. (2024)](https://doi.org/10.1126/science.adj0998).

## Pré-requisitos

- Python 3.10+ (3.11 no CI)
- `make` é opcional (GNU Make, já presente no Linux/macOS e via WSL/Git Bash no
  Windows); sem make, use o fallback `python3 scripts/run_all.py`
- O PDF do artigo está publicado em [`main.pdf`](main.pdf) (a fonte LaTeX não
  faz parte do repositório público)

Crie o ambiente e instale as dependências:

```bash
make setup
```

Ou, sem make:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt   # Linux/WSL
.venv/Scripts/pip install -r requirements.txt -r requirements-dev.txt # Windows
```

Os alvos do Makefile usam o venv do projeto automaticamente quando ele existe
(ou o `python3` do PATH); sobrescreva com `make PYTHON=/caminho/python test` se
precisar.

## Rodar os modelos estatísticos

Pipeline completa (baixa os microdados, estima e regenera tudo):

```bash
make refresh          # sem make: python3 scripts/run_all.py pipeline
```

Só a estimação dos modelos e a geração das figuras/relatórios:

```bash
python3 scripts/compute_econometrics.py   # especificações WLS S1-S4
python3 scripts/compute_robustness.py     # robustez R1-R7
python3 scripts/build_paper_tables.py     # tabelas do artigo
python3 scripts/generate_paper_figures.py # figuras do artigo
```

`make refresh` baixa centenas de MB em `data/microdata/` (ignorado pelo git) e
precisa de rede. A estimação é determinística e não usa LLM em nenhuma etapa.

## Site (companion do artigo)

O site é estático e já vem pronto no repositório (`site/`). O payload
(`site/data.json`) foi compilado uma única vez a partir de `data/output/` e
fica congelado na safra 2026Q1, acompanhando o artigo — não há build nem
script de geração no repositório.

Deploy automático para o GitHub Pages a cada push em `master`: o CI apenas
valida o artefato commitado e faz o upload (`site/`), sem compilar nada
(`.github/workflows/deploy.yml`).

Pré-visualização local (sem build, apenas serve os arquivos commitados):

```bash
python3 -m http.server -d site/ 8080
```

## Testes

```bash
make test             # sem make: python3 scripts/run_all.py test
```

## Fonte de dados

PNAD Contínua (IBGE), microdados trimestrais, peso amostral oficial `V1028`; e
o índice de exposição ocupacional de Eloundou et al. (2024), escala 0-10.

## Licença

MIT. Veja [`LICENSE`](LICENSE).
