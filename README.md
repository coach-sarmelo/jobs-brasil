# 🇧🇷 Jobs BR — Panorama do Mercado de Trabalho & Simulador de IA

[![React 19](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg)](https://vitejs.dev/)
[![D3.js](https://img.shields.io/badge/D3.js-7.0-F9A03C.svg)](https://d3js.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-06B6D4.svg)](https://tailwindcss.com/)

> **Visualizador interativo do mercado de trabalho brasileiro inspirado no projeto [karpathy/jobs](https://github.com/karpathy/jobs) de Andrej Karpathy.**

O **Jobs BR** transforma os microdados oficiais da **PNAD Contínua (Tabela 10287 do IBGE 2022)** em uma aplicação web de alto rendimento visual, combinando engenharia de dados em Python e visualização analítica interativa em D3.js.

---

## ⚡ Funcionalidades Principais

- 📊 **Gráfico de Dispersão Log-Log (D3.js):** Rendimento Médio ($Y$) vs. Nº de Trabalhadores ($X$) em escala logarítmica com suporte a zoom e pan suave.
- 🤖 **Simulador de Disrupção por IA:** Motor de simulação em tempo real para avaliar o impacto da inteligência artificial sobre a massa salarial e ocupações no Brasil.
- 🔍 **Busca & Filtros Inteligentes:** Pesquisa instantânea por ocupação, filtro por Seção da CNAE e faixas salariais.
- 🎨 **Design Moderno:** Interface escura com suporte a glassmorphism e responsividade completa.

---

## 🧮 Modelação Matemática do Simulador de IA

O motor de simulação computa o impacto dinâmico da Inteligência Artificial sobre cada ocupação $i$ e sobre a economia agregada através das seguintes equações:

1. **Rendimento Médio Ajustado da Ocupação $i$:**
   $$W_i' = W_i \cdot (1 - S \cdot A_i)$$
   *Onde:*
   - $W_i$: Rendimento mensal médio inicial da ocupação.
   - $A_i \in [0, 1]$: Índice de Automação/Exposição da ocupação à IA.
   - $S \in [0, 1]$: Fator de Severidade global ajustado pelo usuário na interface.

2. **Massa Salarial Total Ajustada da Ocupação $i$:**
   $$M_i' = N_i \cdot W_i' = N_i \cdot W_i \cdot (1 - S \cdot A_i)$$
   *Onde:*
   - $N_i$: Total de trabalhadores ocupados na profissão $i$.

3. **Massa Salarial Agregada Nacional Ajustada:**
   $$M_{\text{total}}' = \sum_{i} N_i \cdot W_i \cdot (1 - S \cdot A_i)$$

4. **Redução Total da Massa Salarial Nacional ($\Delta M$):**
   $$\Delta M = M_{\text{total}} - M_{\text{total}}' = S \cdot \sum_{i} N_i \cdot W_i \cdot A_i$$

---

## 🛠️ Tecnologias Utilizadas

### Pipeline de Dados (Python ETL)
- Python 3.10+
- Pandas, Regex, JSON parser
- Processamento e estruturação hierárquica dos microdados IBGE em `src/data/jobs_br.json`.

### Frontend Web
- **React 19** + **Vite**
- **D3.js** (`d3-scale`, `d3-zoom`, `d3-selection`)
- **Tailwind CSS v4**
- **Lucide Icons** & **Fuse.js**

---

## 🚀 Como Rodar Localmente

```bash
# 1. Clonar o repositório
git clone https://github.com/seu-usuario/jobs-brasil.git
cd jobs-brasil

# 2. Executar o ETL em Python (opcional, JSON pré-gerado já incluso)
python3 scripts/etl.py

# 3. Instalar dependências e iniciar o servidor dev
npm install
npm run dev
```

Abra no seu navegador: `http://localhost:3000` (ou porta exibida pelo Vite).

---

## 🐳 Executando via Docker

```bash
# Subir o container em segundo plano
docker-compose up -d --build
```

Acesse em: `http://localhost:3005`

Para encerrar o container:
```bash
docker-compose down
```

---

## 📜 Créditos & Referências

- **Projeto Original:** [karpathy/jobs](https://github.com/karpathy/jobs) por Andrej Karpathy.
- **Fonte de Dados:** IBGE — Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD Contínua 2022, Tabela 10287).
