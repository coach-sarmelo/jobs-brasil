# 🇧🇷 Jobs BR — Exposição à Inteligência Artificial no Mercado de Trabalho Brasileiro (IBGE / COD)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![D3.js v7](https://img.shields.io/badge/D3.js-v7-orange.svg)](https://d3js.org/)
[![IBGE PNAD 2022](https://img.shields.io/badge/Dados-IBGE%20PNAD%202022-green.svg)](https://www.ibge.gov.br/)
[![Google Gemini API](https://img.shields.io/badge/LLM-Google%20Gemini%20Flash-purple.svg)](https://ai.google.dev/)
[![GitHub Pages Status](https://img.shields.io/badge/Deploy-GitHub%20Pages-brightgreen.svg)](https://coach-sarmelo.github.io/jobs-brasil/)

> **Réplica exata do projeto [karpathy/jobs](https://github.com/karpathy/jobs) de Andrej Karpathy, adaptado para a economia e ocupações do Brasil utilizando os microdados da PNAD Contínua (IBGE 2022) e a classificação COD.**

---

## 🌐 URLs de Acesso Público

- 🖥️ **Aplicação Web Interativa (Live Site):** [https://coach-sarmelo.github.io/jobs-brasil/](https://coach-sarmelo.github.io/jobs-brasil/)
- 📦 **Repositório do Código-Fonte no GitHub:** [https://github.com/coach-sarmelo/jobs-brasil](https://github.com/coach-sarmelo/jobs-brasil)
- 🏠 **Servidor Local / Rede Privada:** [http://192.168.68.130:3015/](http://192.168.68.130:3015/)

---

## 📋 Tabela de Conteúdos

- [Visão Geral e Objetivos](#-visão-geral-e-objetivos)
- [Funcionalidades Principais](#-funcionalidades-principais)
- [Metodologia de Pontuação por IA](#-metodologia-de-pontuação-por-ia)
- [Estatísticas Agregadas do Brasil](#-estatísticas-agregadas-do-brasil-pnad-2022)
- [Distribuição por Tier de Exposição](#-distribuição-por-tier-de-exposição)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Pré-requisitos](#-pré-requisitos)
- [Guia de Instalação e Execução Local](#-guia-de-instalação-e-execução-local)
- [Execução via Docker](#-execução-via-docker)
- [Implantação e Publicação (CI/CD)](#-implantação-e-publicação-cicd)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Comandos e Scripts Disponíveis](#-comandos-e-scripts-disponíveis)
- [Testes e Qualidade de Código](#-testes-e-qualidade-de-código)
- [Solução de Problemas (Troubleshooting)](#-solução-de-problemas-troubleshooting)
- [Créditos e Licença](#-créditos-e-licença)

---

## 🎯 Visão Geral e Objetivos

O **Jobs BR** quantifica e analisa a exposição do mercado de trabalho brasileiro às tecnologias de Inteligência Artificial Generativa e Automação de Dados. 

Utilizando os dados oficiais da **PNAD Contínua 2022 (IBGE Tabela 10287)** e a **COD (Classificação de Ocupações para Pesquisas Domiciliares)**, o projeto mapeia **87 subgrupos ocupacionais** (abrangendo mais de **87,8 milhões de trabalhadores ocupados** e uma massa salarial de **R$ 250,37 Bilhões por mês**).

Cada subgrupo recebe uma nota de exposição de **0 a 10** avaliada por LLMs (Google Gemini Flash) junto com uma justificativa qualitativa (*rationale*).

---

## ⚡ Funcionalidades Principais

- 🗺️ **Visualização em Treemap D3.js:** Área proporcional ao volume de trabalhadores ou massa salarial mensal de cada ocupação.
- 🎨 **4 Camadas de Cores Dinâmicas (*Color Layers*):**
  1. 🔴 **Exposição à IA (0 a 10):** Do azul/verde (trabalho manual) ao vermelho/roxo (trabalho digital em computador).
  2. 🟢 **Rendimento Médio Mensal (R$):** Escala de gradiente de salário médio.
  3. 🔵 **Número de Trabalhadores:** Concentração populacional da mão de obra.
  4. 🟣 **Massa Salarial Total (R$):** Volume financeiro total movimentado pela ocupação.
- 🔍 **Busca em Tempo Real:** Campo de pesquisa fuzzy com filtro instantâneo por nome da profissão ou setor.
- 📱 **Painel Lateral Detalhado (*Side Drawer*):** Exibe a justificativa gerada pelo Gemini, dados brutos do IBGE, renda média e contagem populacional ao clicar em qualquer nó.

---

## 🧠 Metodologia de Pontuação por IA

Cada ocupação foi pontuada em uma escala contínua de **0 a 10**, medindo a taxa potencial de reestruturação por IA (automação direta ou ganhos de produtividade que reduzem a necessidade de mão de obra adicional).

### 💡 A Heurística Central (Karpathy Anchor)
> *"Se o trabalho pode ser realizado 100% de um home office em um computador — escrita, código, análise, comunicação —, a exposição à IA é inerentemente alta (7+), pois as capacidades de IA no domínio digital avançam em ritmo acelerado. Em contrapartida, trabalhos que exigem presença física, habilidade manual operacional ou interação em tempo real possuem barreira física natural."*

### ⚓ Âncoras de Calibragem
- **0–1 Mínima:** Serventes de pedreiro, lavoura manual, serviços de limpeza pesada.
- **2–3 Baixa:** Eletricistas, encanadores, motoristas, mecânicos, bombeiros.
- **4–5 Moderada:** Enfermagem presencial, policiais, veterinários, balconistas.
- **6–7 Alta:** Professores, gestores de empresas, contadores, jornalistas.
- **8–9 Muito Alta:** Desenvolvedores de software, designers gráficos, analistas de investimentos, tradutores.
- **10 Máxima:** Digitadores de dados, telemarketing, assistentes de transcrição.

---

## 📊 Estatísticas Agregadas do Brasil (PNAD 2022)

- **Total de Ocupações (Subgrupos COD):** 87
- **Total de Trabalhadores Ocupados:** 87.830.902 (87,8 Milhões)
- **Massa Salarial Mensal Total:** R$ 250,37 Bilhões / mês
- **Exposição Média Ponderada à IA:** **4,03 / 10**

---

## 📈 Distribuição por Tier de Exposição

| Nível de Exposição (Tier) | Subgrupos | Empregos (Brasil) | % dos Empregos | Massa Salarial Mensal | Salário Médio (R$) |
|---|---|---|---|---|---|
| **Minimal (0-1)** | 16 | 13.914.887 | 15,8% | R$ 24,0 Bi | R$ 1.728 |
| **Low (2-3)** | 27 | 28.563.816 | 32,5% | R$ 57,0 Bi | R$ 1.996 |
| **Moderate (4-5)** | 20 | 25.132.880 | 28,6% | R$ 68,0 Bi | R$ 2.706 |
| **High (6-7)** | 14 | 12.871.218 | 14,7% | R$ 56,1 Bi | R$ 4.359 |
| **Very high (8-10)** | 10 | 7.348.101 | 8,4% | R$ 45,3 Bi | R$ 6.165 |

---

## 🏗️ Arquitetura do Sistema

```
+------------------------------------+       +-----------------------------------+
|  IBGE Microdados PNAD 2022         |       |  Google Gemini API                |
|  - Rendimento.csv                  |       |  (Score 0-10 & Rationale)         |
|  - numero-trabalhadores.csv        |       +-----------------+-----------------+
+-----------------+------------------+                         |
                  |                                            |
                  v                                            v
    +---------------------------+                +---------------------------+
    | extract_cod_subgroups.py  |                | score.py                  |
    | (Extrai 87 subgrupos COD) |                | (Gera scores.json)        |
    +--------------+------------+                +-------------+-------------+
                   |                                           |
                   +---------------------+---------------------+
                                         |
                                         v
                           +---------------------------+
                           | build_site_data.py        |
                           | (Calcula agregados/tiers) |
                           +-------------+-------------+
                                         |
                                         v
                           +---------------------------+
                           | site/data.json            |
                           +-------------+-------------+
                                         |
                                         v
                           +---------------------------+
                           | site/index.html (D3.js)   |
                           | GitHub Pages / Servidor   |
                           +---------------------------+
```

---

## 📁 Estrutura do Repositório

```text
jobs-brasil/
├── .github/
│   └── workflows/
│       └── deploy.yml             # Workflow de CI/CD para deploy automático no GitHub Pages
├── scripts/
│   ├── extract_cod_subgroups.py  # Extrai e limpa os subgrupos da COD a partir dos CSVs do IBGE
│   └── generate_readme_report.py # Atualiza o relatório analítico no README.md
├── site/
│   ├── index.html                 # Aplicação web Treemap interativa (D3.js)
│   ├── style.css                  # Estilos CSS dark mode estilo karpathy.ai/jobs
│   └── data.json                  # Dataset final compilado com as pontuações e métricas IBGE
├── tests/
│   ├── test_extraction.py         # Teste unitário da extração de subgrupos
│   ├── test_score.py              # Teste unitário do schema de scores.json
│   ├── test_build_site_data.py    # Teste unitário da compilação do site/data.json
│   └── test_etl.py                # Teste de integração do pipeline
├── cod_subgroups.json             # Dados limpos dos 87 subgrupos
├── score.py                       # Script Python para scoring via Gemini API com fallback
├── scores.json                    # Cache de notas e justificativas dos 87 subgrupos
├── build_site_data.py             # Compilador dos dados agregados para o site
├── server.py                      # Servidor HTTP leve em Python (porta 3015)
├── Dockerfile                     # Container multi-stage para deploy em produção
├── docker-compose.yml             # Orquestração do container Docker
├── package.json                   # Dependências Node.js / Vite (opcional)
├── vite.config.js                 # Configuração do Vite
└── README.md                      # Documentação completa do projeto
```

---

## 🛠️ Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina:

- **Python 3.10 ou superior**
- **pip** (Gerenciador de pacotes do Python)
- **Node.js 20+ / npm** (Opcional, apenas se for utilizar o servidor Vite)
- **Docker & Docker Compose** (Opcional, para execução em container)
- **Chave de API do Google Gemini (`GEMINI_API_KEY`)** (Opcional; caso não informada, o sistema utiliza o motor heurístico em Português)

---

## 🚀 Guia de Instalação e Execução Local

### 1. Clonar o Repositório

```bash
git clone https://github.com/coach-sarmelo/jobs-brasil.git
cd jobs-brasil
```

### 2. Instalar Dependências do Python

```bash
pip install -r requirements.txt
```
*(Ou instale manualmente: `pip install pytest requests google-genai pandas`)*

### 3. Configurar a Chave da API (Opcional)

```bash
export GEMINI_API_KEY="sua_chave_aqui"
```

### 4. Executar o Pipeline Completo de Dados

```bash
# Etapa 1: Extrair subgrupos da COD
python3 scripts/extract_cod_subgroups.py

# Etapa 2: Gerar notas e justificativas via Gemini API
python3 score.py

# Etapa 3: Compilar dados agregados para o site
python3 build_site_data.py
```

### 5. Iniciar o Servidor Web Local

```bash
python3 server.py
```

Acesse no seu navegador: **[http://localhost:3015](http://localhost:3015)** ou **[http://192.168.68.130:3015](http://192.168.68.130:3015)**

---

## 🐳 Execução via Docker

Para rodar a aplicação em um container isolado:

```bash
# Build e execução do container
docker-compose up -d --build
```

Acesse em: **[http://localhost:3015](http://localhost:3015)**

Para parar o container:
```bash
docker-compose down
```

---

## 🌐 Implantação e Publicação (CI/CD)

O projeto possui um workflow configurado no **GitHub Actions** (`.github/workflows/deploy.yml`).

### Como Funciona o Deploy Automático:
1. Cada `git push` na branch `master` ou `main` dispara o workflow de implantação.
2. O GitHub Actions faz o upload automático dos arquivos estáticos da pasta `site/`.
3. A aplicação entra no ar instantaneamente em **`https://coach-sarmelo.github.io/jobs-brasil/`**.

---

## 🔑 Variáveis de Ambiente

| Variável | Descrição | Exemplo | Obrigatório |
|---|---|---|---|
| `GEMINI_API_KEY` | Chave da API do Google Gemini para scoring LLM | `AIzaSy...` | Não (possui fallback local) |
| `PORT` | Porta do servidor web local | `3015` | Não (default: 3015) |

---

## 📜 Comandos e Scripts Disponíveis

| Comando | Descrição |
|---|---|
| `python3 scripts/extract_cod_subgroups.py` | Extrai os 87 subgrupos da COD dos CSVs originais do IBGE. |
| `python3 score.py` | Gera o arquivo `scores.json` avaliando as ocupações via Gemini API. |
| `python3 build_site_data.py` | Cruza as estatísticas e gera o arquivo `site/data.json`. |
| `python3 scripts/generate_readme_report.py` | Atualiza o relatório do `README.md` com os dados atuais. |
| `python3 server.py` | Inicia o servidor HTTP em Python na porta 3015. |
| `python3 -m pytest tests/` | Executa a suíte de testes automatizados do projeto. |

---

## 🧪 Testes e Qualidade de Código

O projeto possui uma suíte completa de testes automatizados com `pytest`:

```bash
python3 -m pytest tests/ -v
```

### Testes Incluídos:
- `tests/test_extraction.py`: Valida se exatamente ~87 subgrupos da COD são extraídos com valores de renda e trabalhadores > 0.
- `tests/test_score.py`: Valida se o schema do `scores.json` possui notas no intervalo válido `[0, 10]`.
- `tests/test_build_site_data.py`: Valida os cálculos agregados da população e massa salarial do Brasil.

---

## 🔧 Solução de Problemas (Troubleshooting)

### 1. Erro `Address already in use` na porta 3015
Se a porta 3015 estiver ocupada por outro processo:
```bash
fuser -k 3015/tcp
```
Ou altere a variável `PORT` dentro de `server.py`.

### 2. Chave de API do Gemini inválida ou quota estourada
O script `score.py` possui fallback automático. Se a API falhar ou não houver chave configurada, o script utilizará o motor heurístico integrado em Português sem interromper o pipeline.

### 3. Erro de CORS ao abrir `index.html` direto via arquivo local (`file://`)
Navegadores bloqueiam a requisição `fetch('data.json')` por política de segurança se aberto como arquivo local. **Sempre utilize um servidor HTTP local** (`python3 server.py`) ou o link do GitHub Pages.

---

## ⚖️ Créditos e Licença

- **Autor do Projeto Brasil:** sarmelo / coach-sarmelo
- **Inspiração e Arquitetura:** Andrej Karpathy ([karpathy/jobs](https://github.com/karpathy/jobs))
- **Fonte dos Dados:** IBGE — Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD Contínua 2022) / Tabela 10287 (COD).
- **Licença:** MIT License
