# 🇧🇷 Jobs BR — Exposição à Inteligência Artificial no Mercado de Trabalho Brasileiro (IBGE / COD)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![D3.js v7](https://img.shields.io/badge/D3.js-v7-orange.svg)](https://d3js.org/)
[![IBGE PNAD 2022](https://img.shields.io/badge/Dados-IBGE%20PNAD%202022-green.svg)](https://www.ibge.gov.br/)
[![LLM DeepSeek V4 Flash](https://img.shields.io/badge/LLM-DeepSeek%20V4%20Flash-purple.svg)](https://www.deepseek.com/)
[![GitHub Pages Status](https://img.shields.io/badge/Deploy-GitHub%20Pages-brightgreen.svg)](https://coach-sarmelo.github.io/jobs-brasil/)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](./LICENSE)

> **Inspirado no projeto [karpathy/jobs](https://github.com/karpathy/jobs) de Andrej Karpathy, adaptado para a economia e ocupações do Brasil utilizando os microdados da PNAD Contínua (IBGE 2022) e a classificação COD.**

Site estático, 100% open source, publicado como peça de portfólio.

---

## 🌐 Links do Projeto

- 🖥️ **Aplicação Web Interativa (Live Site):** [https://marcelo.ai/jobs/](https://marcelo.ai/jobs/) *(ou [coach-sarmelo.github.io/jobs-brasil](https://coach-sarmelo.github.io/jobs-brasil/))*
- 📦 **Repositório do Código-Fonte no GitHub:** [https://github.com/coach-sarmelo/jobs-brasil](https://github.com/coach-sarmelo/jobs-brasil)

---

## 📋 Tabela de Conteúdos

- [Visão Geral e Objetivos](#-visão-geral-e-objetivos)
- [Funcionalidades Principais](#-funcionalidades-principais)
- [Metodologia de Pontuação por IA](#-metodologia-de-pontuação-por-ia)
- [Transparência Metodológica](#-transparência-metodológica)
- [Pontuação via opencode + DeepSeek](#-pontuação-via-opencode--deepseek)
- [Relatório de Dados](#-relatório-de-dados)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Pré-requisitos](#-pré-requisitos)
- [Guia de Instalação e Execução](#-guia-de-instalação-e-execução)
- [Implantação e Publicação (CI/CD)](#-implantação-e-publicação-cicd)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Comandos e Scripts Disponíveis](#-comandos-e-scripts-disponíveis)
- [Testes e Qualidade de Código](#-testes-e-qualidade-de-código)
- [Créditos e Licença](#-créditos-e-licença)

---

## 🎯 Visão Geral e Objetivos

O **Jobs BR** quantifica e analisa a exposição do mercado de trabalho brasileiro às tecnologias de Inteligência Artificial Generativa e Automação de Dados.

Utilizando os dados oficiais da **PNAD Contínua 2022 (IBGE Tabela 10287)** e a **COD (Classificação de Ocupações para Pesquisas Domiciliares)**, o projeto mapeia os subgrupos ocupacionais do Brasil.

Cada subgrupo recebe uma nota de exposição de **0 a 10**, avaliada por um LLM (**DeepSeek V4 Flash**) com uma justificativa qualitativa (*rationale*), e um motor heurístico local é usado como fallback transparente quando nenhuma chave de API está configurada.

---

## ⚡ Funcionalidades Principais

- 🗺️ **Visualização em Treemap D3.js:** Área proporcional ao volume de trabalhadores ou massa salarial mensal de cada ocupação.
- 🎨 **4 Camadas de Cores Dinâmicas (*Color Layers*):**
  1. 🔴 **Exposição à IA (0 a 10):** Do azul/verde (trabalho manual) ao vermelho/roxo (trabalho digital em computador).
  2. 🟢 **Rendimento Médio Mensal (R$):** Escala de gradiente de salário médio.
  3. 🔵 **Número de Trabalhadores:** Concentração populacional da mão de obra.
  4. 🟣 **Massa Salarial Total (R$):** Volume financeiro total movimentado pela ocupação.
- 🔍 **Busca em Tempo Real:** Campo de pesquisa com filtro instantâneo por nome da profissão ou setor.
- 📱 **Painel Lateral Detalhado (*Side Drawer*):** Exibe a justificativa gerada pelo LLM, dados brutos do IBGE, renda média e contagem populacional ao clicar em qualquer nó.

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

**Nota metodológica:** essas âncoras servem tanto de fallback heurístico local (keyword matching) quanto de rubrica no prompt enviado ao LLM. Isso significa que o LLM está calibrado pelas mesmas referências, e não é uma fonte totalmente independente — é uma limitação conhecida e declarada, não um índice acadêmico validado (como Frey & Osborne ou AIOE). Trate os scores como uma primeira aproximação qualitativa, não como uma medida com validade externa comprovada.

---

## 🔍 Transparência Metodológica

Todo registro em `scores.json` grava **como o score foi gerado**, para que o dado publicado nunca alegue algo que não aconteceu:

```json
{
  "score": 8,
  "rationale": "...",
  "method": "llm",          // "llm" (gerado numa sessão opencode + DeepSeek) ou "heuristic-keyword-v1" (baseline local, sem LLM)
  "model": "deepseek-v4-flash",
  "generated_at": "2026-08-06T18:15:01+00:00"
}
```

`site/data.json` agrega essa informação em `meta.scoring_method_counts`, e cada ocupação carrega seu próprio `method` — o site e o README refletem exatamente qual proporção dos scores veio do LLM vs. do heurístico em cada geração, em vez de assumir que um LLM foi usado quando na verdade não foi.

---

## 🤖 Pontuação via opencode + DeepSeek

`score.py` só gera o baseline determinístico (heurística local, sem custo e
sem dependência externa). Os scores `"method": "llm"` publicados no site são
gerados manualmente numa sessão do [opencode](https://opencode.ai) — um
agente de codificação em terminal — configurada com **DeepSeek** como
provedor, que edita `scores.json` diretamente. Não há chamada de API dentro
do repositório para isso; o DeepSeek atua como o próprio agente.

### 1. Instalar o opencode

```bash
curl -fsSL https://opencode.ai/install | bash
# alternativas: npm install -g opencode-ai@latest  |  brew install sst/tap/opencode
```

> Consulte a [documentação oficial](https://opencode.ai/docs) para o método de
> instalação mais atual — pode variar entre versões.

### 2. Autenticar com DeepSeek

```bash
opencode auth login
# selecione "DeepSeek" na lista de provedores e cole sua API key
```

Dentro da sessão do opencode, selecione o modelo DeepSeek V4 Flash (rode
`/models` na TUI, ou `opencode models` no terminal, para confirmar o
identificador exato disponível na sua instalação).

### 3. Rodar a classificação

1. Garanta que `cod_subgroups.json` existe: `python3 scripts/extract_cod_subgroups.py`.
2. Abra o opencode na raiz deste repositório.
3. Cole o prompt de
   [`scripts/OPENCODE_SCORING_PROMPT.md`](scripts/OPENCODE_SCORING_PROMPT.md)
   — esse arquivo é a fonte da verdade do prompt usado; qualquer alteração
   nele deve ser seguida de uma nova rodada de scoring.
4. Após o opencode terminar e os testes passarem, rode:
   ```bash
   python3 build_site_data.py
   python3 scripts/generate_readme_report.py
   ```

---

## 📊 Relatório de Dados

<!-- AUTO-GENERATED-REPORT:START -->
<!-- Gerado automaticamente por scripts/generate_readme_report.py a partir de site/data.json. Não edite manualmente entre estes marcadores. -->

### Estatísticas Agregadas

- **Total de Ocupações (Subgrupos COD):** 87
- **Total de Trabalhadores:** 87,830,902
- **Massa Salarial Mensal Total:** R$ 250.37 Bi
- **Exposição Média Ponderada à IA:** **4.08/10**
- **Método de pontuação (contagem por origem):** llm: 87

### Distribuição por Tier de Exposição

| Tier | Ocupações | Empregos | % dos Empregos | Massa Salarial Mensal | Salário Médio |
|---|---|---|---|---|---|
| Minimal (0-1) | 5 | 12,965,685 | 14.8% | R$ 20.1 Bi | R$ 1,548 |
| Low (2-3) | 31 | 22,439,832 | 25.5% | R$ 51.6 Bi | R$ 2,300 |
| Moderate (4-5) | 24 | 33,929,757 | 38.6% | R$ 97.8 Bi | R$ 2,884 |
| High (6-7) | 20 | 16,021,436 | 18.2% | R$ 66.2 Bi | R$ 4,134 |
| Very high (8-10) | 7 | 2,474,192 | 2.8% | R$ 14.6 Bi | R$ 5,908 |

### Top 30 Ocupações por Exposição à IA

| Código | Ocupação | Setor | Renda (R$) | Trabalhadores | Exposição | Método | Justificativa |
|---|---|---|---|---|---|---|---|
| 10.62 | **Atividades dos serviços de tecnologia da informação** | Informação e comunicação | R$ 5,941 | 875,815 | **9/10** | llm | Programadores, analistas, testadores e administradores de sistemas executam praticamente todo o trabalho em computadores, de qualquer lugar, incluindo home office remoto. A IA atua como copiloto de código e automatiza tarefas de infraestrutura, colocando este subgrupo entre os mais expostos do mercado. |
| 11.64 | **Atividades de serviços financeiros** | Atividades financeiras, de seguros e serviços relacionados | R$ 6,382 | 827,661 | **8/10** | llm | Bancos e corretoras concentram análise de crédito, operações, gestão de investimentos e atendimento em sistemas digitais, com grande parte do trabalho remoto em computador. A IA já classifica risco, responde clientes e automatiza negociações, tornando o setor financeiro altamente exposto. |
| 13.73 | **Publicidade e pesquisas de mercado** | Atividades profissionais, científicas e técnicas | R$ 4,923 | 373,536 | **8/10** | llm | Criação publicitária, mídia, análise de audiência e pesquisas de mercado são feitas em computadores, com produção de peças, relatórios e campanhas digitais. A IA generativa já escreve anúncios, gera imagens e segmenta audiências, pressionando fortemente o subgrupo. |
| 11.66 | **Atividades auxiliares dos serviços financeiros, seguros, previdência complementar e planos de saúde** | Atividades financeiras, de seguros e serviços relacionados | R$ 5,938 | 171,014 | **8/10** | llm | Corretoras de câmbio, gestoras de cartões, análise de investimentos e back office processam dados financeiros em computadores com trabalho majoritariamente de escritório. A IA automatiza conciliação, análise de investimentos e suporte, elevando a substituibilidade do subgrupo. |
| 10.63 | **Atividades de prestação de serviços de informação** | Informação e comunicação | R$ 4,807 | 103,774 | **8/10** | llm | Portais, agências de notícias, processamento de dados e serviços de busca operam quase inteiramente em computadores, com produção e tratamento digital de informação. A IA generativa escreve notícias, agrega conteúdo e processa dados em escala, ameaçando diretamente grande parte dessas funções. |
| 13.70 | **Atividades de consultoria em gestão empresarial** | Atividades profissionais, científicas e técnicas | R$ 7,028 | 73,148 | **8/10** | llm | Consultores passam o dia analisando dados, construindo apresentações e recomendando estratégias em computadores, com reuniões remotas e entregas digitais. Ferramentas de IA generativa e análise aceleram o trabalho, pressionando funções de análise e elaboração de relatórios. |
| 13.72 | **Pesquisa e desenvolvimento científico** | Atividades profissionais, científicas e técnicas | R$ 5,368 | 49,244 | **8/10** | llm | Pesquisadores e cientistas dedicam grande parte do tempo à revisão de literatura, análise de dados, simulação e escrita de artigos em computadores, com laboratórios e campo complementando o trabalho. A IA automatiza a síntese de conhecimento e a análise de experimentos, aumentando a exposição das etapas cognitivas. |
| 16.85 | **Educação** | Educação | R$ 3,425 | 5,829,925 | **7/10** | llm | Professores e profissionais da educação preparam aulas, corrigem atividades e geram conteúdo em computadores, embora o ensino presencial em sala de aula continue dominante. Plataformas de ensino com IA personalizam atividades e avaliam redações, aumentando a exposição das tarefas pedagógicas digitais. |
| 13.69 | **Atividades jurídicas, de contabilidade e de auditoria** | Atividades profissionais, científicas e técnicas | R$ 5,867 | 1,749,567 | **7/10** | llm | Advogados, contadores e auditores produzem pareceres, demonstrações e relatórios em computadores, com revisão de documentos e análise de números como núcleo da rotina. A IA já pesquisa jurisprudência, concilia contas e redige documentos, elevando muito a exposição do subgrupo. |
| 14.82 | **Serviços de escritório, de apoio administrativo e outros serviços prestados a empresas** | Atividades administrativas e serviços complementares | R$ 2,006 | 1,033,243 | **7/10** | llm | Assistentes administrativos, recepcionistas e pessoal de apoio processam documentos, atendem telefone e alimentam planilhas em escritórios, com rotinas repetitivas em computador. A IA e a automação de processos já absorvem digitação, agendamento e atendimento, expondo fortemente o subgrupo. |
| 13.71 | **Serviços de arquitetura e engenharia; testes e análises técnicas** | Atividades profissionais, científicas e técnicas | R$ 5,856 | 620,102 | **7/10** | llm | Arquitetos e engenheiros projetam em CAD, calculam estruturas e emitem laudos em computadores, embora vistorias, obras e ensaios laboratoriais exijam presença física. A IA já gera plantas, simula estruturas e analisa ensaios, expondo fortemente a etapa de projeto e análise. |
| 11.65 | **Seguros, resseguros, previdência complementar e planos de saúde** | Atividades financeiras, de seguros e serviços relacionados | R$ 4,758 | 137,821 | **7/10** | llm | Seguradoras processam apólices, sinistros e análise de risco em sistemas informatizados, embora parte da venda e da vistoria exija presença no campo. Subscrição automatizada e chatbots de sinistro com IA reduzem a demanda de subscritores e atendentes administrativos. |
| 14.79 | **Agências de viagens, operadores turísticos e serviços de reservas** | Atividades administrativas e serviços complementares | R$ 3,663 | 127,011 | **7/10** | llm | Agentes de viagens e operadores turísticos fazem reservas, emitem bilhetes e montam roteiros em computadores, com atendimento presencial e por telefone. Plataformas de reserva com IA e chatbots já substituem a intermediação, tornando o subgrupo bastante exposto. |
| 10.58 | **Edição e edição integrada à de impressão** | Informação e comunicação | R$ 4,664 | 49,152 | **7/10** | llm | Editores, revisores e designers editoriais produzem livros, jornais e revistas em computadores, com escrita, diagramação e correção majoritariamente digitais. A IA generativa já redige, revisa e diagrama conteúdo, tornando este um dos subgrupos mais expostos do setor editorial. |
| 21.99 | **Organismos internacionais e outras instituições extraterritoriais** | Organismos internacionais e outras instituições extraterritoriais | R$ 9,087 | 2,105 | **7/10** | llm | Diplomatas, analistas e técnicos de organismos internacionais produzem relatórios, negociações e documentos em escritórios, com trabalho majoritariamente digital em computador. A IA já auxilia tradução, análise de políticas e redação oficial, expondo moderadamente o subgrupo. |
| 15.84 | **Administração pública, defesa e seguridade social** | Administração pública, defesa e seguridade social | R$ 4,929 | 4,101,378 | **6/10** | llm | Servidores públicos executam análise de processos, atendimento e gestão de políticas públicas em computadores, embora defesa e segurança pública exijam presença física. A digitalização do governo e a IA em análise documental crescem, expondo as funções administrativas do subgrupo. |
| 12.68 | **Atividades imobiliárias** | Atividades imobiliárias | R$ 4,648 | 473,598 | **6/10** | llm | Corretores e administradoras de imóveis dividem o tempo entre visitas e vistorias presenciais e negociação, contratos e marketing digital em computadores. Portais com IA, tour virtual e avaliação automatizada de imóveis reduzem etapas, mas a venda presencial ainda protege parte da função. |
| 13.74 | **Outras atividades profissionais, científicas e técnicas** | Atividades profissionais, científicas e técnicas | R$ 3,939 | 467,394 | **6/10** | llm | O subgrupo reúne tradutores, designers, fotógrafos e consultores técnicos diversos, com mistura de trabalho digital em computador e atendimento presencial ao cliente. Tradutores e designers estão entre os mais ameaçados pela IA generativa, enquanto serviços presenciais como fotografia mantêm barreiras. |
| 10.61 | **Telecomunicações** | Informação e comunicação | R$ 3,314 | 353,552 | **6/10** | llm | O setor de telecomunicações combina instalação e manutenção física de redes, antenas e cabos com operação de centrais, monitoramento de rede e atendimento em sistemas digitais. A IA já automatiza o atendimento e o diagnóstico de falhas, elevando a exposição das funções de suporte e operação. |
| 18.90 | **Atividades artísticas, criativas e de espetáculos** | Artes, cultura, esporte e recreação | R$ 3,422 | 352,100 | **6/10** | llm | Artistas plásticos, atores, músicos e criadores dividem apresentações presenciais com produção digital de obras e portfólios em computadores. A IA gera imagens, música e roteiros, pressionando o lado criativo digital, enquanto o espetáculo ao vivo preserva a presença física. |
| 19.94 | **Atividades de organizações associativas** | Outras atividades de serviços | R$ 2,999 | 282,234 | **6/10** | llm | Sindicatos, associações e entidades de classe mantêm equipes administrativas que produzem comunicados, controlam associados e organizam eventos com trabalho de escritório. A IA apoia a comunicação e a gestão de cadastros, enquanto a representação presencial dos associados permanece humana. |
| 3.26 | **Fabricação de equipamentos de informática, produtos eletrônicos e ópticos** | Indústrias de transformação | R$ 2,611 | 154,764 | **6/10** | llm | A montagem de placas, componentes eletrônicos e dispositivos ópticos combina linhas de produção automatizadas com teste e inspeção em salas limpas, enquanto engenheiros de produto trabalham em software. O projeto de circuitos e o teste automatizado com IA expõem a parte técnica do subgrupo, mas a manufatura segue presencial. |
| 10.59 | **Atividades cinematográficas, produção de vídeos e de programas de televisão; gravação de som e de música** | Informação e comunicação | R$ 4,482 | 73,159 | **6/10** | llm | A indústria audiovisual combina set de filmagem presencial com edição de vídeo, som e efeitos digitais feitos em estações de trabalho. A IA gera roteiros, edita imagens e compõe trilhas, aumentando a exposição das etapas de pós-produção, enquanto as gravações seguem físicas. |
| 14.77 | **Aluguéis não imobiliários e gestão de ativos intangíveis não financeiros** | Atividades administrativas e serviços complementares | R$ 3,723 | 66,758 | **6/10** | llm | A gestão de aluguel de máquinas, veículos e ativos intangíveis é feita em escritórios com contratos, faturas e sistemas de cobrança em computadores. A IA automatiza contratos e análise de inadimplência, enquanto visitas e vistorias pontuais mantêm parte da atividade presencial. |
| 10.60 | **Atividades de rádio e de televisão** | Informação e comunicação | R$ 4,040 | 63,097 | **6/10** | llm | Emissoras de rádio e TV unem estúdios e externas presenciais a redações onde jornalistas e editores trabalham em computadores com conteúdo digital. Apresentadores e repórteres seguem necessários, mas locução sintética, notícias geradas por IA e edição automatizada reduzem o trabalho humano nas redações. |
| 14.78 | **Seleção, agenciamento e locação de mão-de-obra** | Atividades administrativas e serviços complementares | R$ 3,172 | 52,619 | **6/10** | llm | Agências de emprego e headhunters triam currículos, cadastram candidatos e gerenciam contratos em sistemas digitais, com entrevistas também realizadas de forma remota. A IA já filtra currículos e conduz entrevistas iniciais, automatizando boa parte do recrutamento. |
| 18.92 | **Atividades de exploração de jogos de azar e apostas** | Artes, cultura, esporte e recreação | R$ 1,472 | 31,857 | **6/10** | llm | Cassinos, bingos e casas de aposta misturam atendimento presencial nas salas com operação de apostas online em plataformas digitais. A IA já opera odds, detecta fraudes e personaliza apostas online, expondo fortemente a parte digital do subgrupo. |
| 7.48 | **Comércio, exceto de veiculos automotores e motocicletas** | Comércio, reparação de veículos automotores e motocicletas | R$ 2,461 | 12,755,805 | **5/10** | llm | O varejo e o atacado empregam 12,7 milhões de vendedores, caixas e reposidores em lojas físicas, com atendimento direto ao cliente e rotinas presenciais. O comércio eletrônico e o marketing digital com IA crescem, mas a maior parte do subgrupo atua no balcão. |
| 22.00 | **Atividades maldefinidas** | Atividades maldefinidas | R$ 3,321 | 5,716,958 | **5/10** | llm | Este subgrupo residual reúne ocupações não classificadas e heterogêneas, sem rotina ocupacional definida, o que torna a avaliação de exposição incerta. A escala do contingente sugere presença de trabalho informal e manual, resultando em exposição moderada e conservadora. |
| 17.86 | **Atividades de atenção à saúde humana** | Saúde humana e serviços sociais | R$ 4,502 | 4,752,742 | **5/10** | llm | Médicos, enfermeiros e técnicos de saúde atuam presencialmente em hospitais, clínicas e prontos-socorros, com contato direto com pacientes e procedimentos físicos. A IA ajuda em diagnóstico por imagem e prontuários, mas o cuidado humano e a execução de procedimentos mantêm forte barreira física. |

<!-- AUTO-GENERATED-REPORT:END -->

---

## 🏗️ Arquitetura do Sistema

```
+------------------------------------+       +-----------------------------------+
|  IBGE Microdados PNAD 2022         |       |  opencode + DeepSeek (manual)     |
|  - Rendimento.csv                  |       |  (edita scores.json direto,       |
|  - numero-trabalhadores.csv        |       |   method="llm")                   |
+-----------------+------------------+       +-----------------+-----------------+
                  |                                            |
                  v                                            |
    +---------------------------+                              |
    | extract_cod_subgroups.py  |                              |
    | (Extrai os subgrupos COD) |                              |
    +--------------+------------+                              |
                   |                                           |
                   v                                           |
    +---------------------------+                              |
    | score.py                  |                              |
    | (baseline heurístico,     |                              |
    |  method="heuristic-...")  |                              |
    +--------------+------------+                              |
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
                           | marcelo.ai/jobs            |
                           +---------------------------+
```

---

## 📁 Estrutura do Repositório

```text
jobs-brasil/
├── .github/
│   └── workflows/
│       └── deploy.yml             # Workflow de CI/CD para deploy automático no GitHub Pages
├── data/
│   └── raw/
│       ├── Rendimento.csv         # Extrato IBGE PNAD 2022 (Tabela 10287) — renda média
│       └── numero-trabalhadores.csv # Extrato IBGE PNAD 2022 (Tabela 10287) — nº de trabalhadores
├── scripts/
│   ├── fetch_ibge_data.py         # Busca os CSVs brutos direto da API do SIDRA/IBGE
│   ├── extract_cod_subgroups.py  # Extrai e limpa os subgrupos da COD a partir dos CSVs do IBGE
│   ├── generate_readme_report.py # Atualiza a seção auto-gerada do README.md
│   └── OPENCODE_SCORING_PROMPT.md # Prompt versionado usado no opencode + DeepSeek
├── site/
│   ├── index.html                 # Aplicação web Treemap interativa (D3.js), site estático publicado
│   ├── style.css                  # Estilos CSS dark mode
│   └── data.json                  # Dataset final compilado com as pontuações e métricas IBGE
├── tests/
│   ├── test_extraction.py         # Teste unitário da extração de subgrupos
│   ├── test_score.py              # Teste unitário do schema e proveniência de scores.json
│   └── test_build_site_data.py    # Teste unitário da compilação do site/data.json
├── cod_subgroups.json             # Dados limpos dos subgrupos COD
├── score.py                       # Gera o baseline heurístico local de scores.json (sem LLM)
├── scores.json                    # Cache de notas, justificativas e proveniência dos subgrupos
├── build_site_data.py             # Compilador dos dados agregados para o site
├── server.py                      # Servidor HTTP leve em Python para desenvolvimento local
├── requirements.txt                # Dependências Python do pipeline
├── LICENSE                        # Licença MIT
└── README.md                      # Documentação completa do projeto
```

---

## 🛠️ Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina:

- **Python 3.10 ou superior**
- **pip** (Gerenciador de pacotes do Python)
- **[opencode](https://opencode.ai) configurado com DeepSeek** (Opcional; necessário apenas para gerar scores `"method": "llm"` — sem ele, `score.py` usa o motor heurístico local e registra isso explicitamente em `scores.json`)

---

## 🚀 Guia de Instalação e Execução

### 1. Clonar o Repositório

```bash
git clone https://github.com/coach-sarmelo/jobs-brasil.git
cd jobs-brasil
```

### 2. Instalar Dependências do Python

```bash
pip install -r requirements.txt
```

### 3. Executar o Pipeline de Dados (baseline heurístico)

Os CSVs brutos do IBGE (PNAD Contínua 2022, Tabela 10287) já estão incluídos em `data/raw/`. Para buscá-los novamente diretamente da [API do SIDRA/IBGE](https://apisidra.ibge.gov.br/) (sem download manual):

```bash
python3 scripts/fetch_ibge_data.py
```

> **Nota:** a Tabela 10287 do SIDRA só tem o período de **2022** publicado —
> o IBGE não lançou uma edição mais recente dessa tabela específica (outras
> tabelas do PNAD Contínua têm dados trimestrais até 2026, mas com uma
> granularidade ocupacional bem menor — só ~12 categorias amplas em vez dos
> 87 subgrupos COD detalhados usados aqui). O script já busca o período mais
> recente disponível (configurável via `IBGE_PERIOD`), então volta a
> funcionar automaticamente se o IBGE algum dia publicar um ano novo.

Para usar sua própria extração/arquivo, aponte `RENDIMENTO_CSV` e `WORKERS_CSV` para os arquivos desejados.

```bash
# Etapa 1: Extrair subgrupos da COD
python3 scripts/extract_cod_subgroups.py

# Etapa 2: Gerar scores.json com o motor heurístico local (sem LLM, sem custo)
python3 score.py

# Etapa 3: Compilar dados agregados para o site
python3 build_site_data.py

# Etapa 4 (opcional): Atualizar a seção de relatório deste README
python3 scripts/generate_readme_report.py
```

Para substituir os scores heurísticos por scores gerados por LLM, siga a
seção [Pontuação via opencode + DeepSeek](#-pontuação-via-opencode--deepseek)
antes da Etapa 3.

### 4. Iniciar o Servidor Web Local

```bash
python3 server.py
```

---

## 🌐 Implantação e Publicação (CI/CD)

O projeto possui um workflow configurado no **GitHub Actions** (`.github/workflows/deploy.yml`).

### Como Funciona o Deploy Automático:
1. Cada `git push` na branch `master` ou `main` dispara o workflow de implantação.
2. O GitHub Actions faz o upload automático dos arquivos estáticos da pasta `site/`.
3. A aplicação entra no ar instantaneamente em **`https://marcelo.ai/jobs/`** (via GitHub Pages / custom domain).

---

## 🔑 Variáveis de Ambiente

| Variável | Descrição | Exemplo | Obrigatório |
|---|---|---|---|
| `RENDIMENTO_CSV` | Caminho alternativo para o CSV de renda do IBGE | `./data/raw/Rendimento.csv` | Não |
| `WORKERS_CSV` | Caminho alternativo para o CSV de trabalhadores do IBGE | `./data/raw/numero-trabalhadores.csv` | Não |

A chave de API do DeepSeek é configurada dentro do próprio opencode (`opencode auth login`), não como variável de ambiente deste repositório — veja [Pontuação via opencode + DeepSeek](#-pontuação-via-opencode--deepseek).

---

## 📜 Comandos e Scripts Disponíveis

| Comando | Descrição |
|---|---|
| `python3 scripts/fetch_ibge_data.py` | Busca os CSVs brutos direto da API do SIDRA/IBGE (Tabela 10287), sobrescrevendo `data/raw/`. |
| `python3 scripts/extract_cod_subgroups.py` | Extrai os subgrupos da COD dos CSVs em `data/raw/`. |
| `python3 score.py` | Gera/reseta `scores.json` com o baseline heurístico local (sem LLM). |
| *(manual, via opencode)* [`scripts/OPENCODE_SCORING_PROMPT.md`](scripts/OPENCODE_SCORING_PROMPT.md) | Prompt para gerar scores `method: "llm"` numa sessão opencode + DeepSeek, editando `scores.json` diretamente. |
| `python3 build_site_data.py` | Cruza as estatísticas e gera o arquivo `site/data.json`. |
| `python3 scripts/generate_readme_report.py` | Atualiza apenas a seção auto-gerada deste README com os dados atuais. |
| `python3 server.py` | Inicia o servidor HTTP local em `http://0.0.0.0:3015`. |
| `python3 -m pytest tests/` | Executa a suíte de testes automatizados do projeto. |

---

## 🧪 Testes e Qualidade de Código

O projeto possui uma suíte de testes automatizados com `pytest`:

```bash
python3 -m pytest tests/ -v
```

### Testes Incluídos:
- `tests/test_extraction.py`: Valida se os subgrupos da COD são extraídos com valores de renda e trabalhadores > 0.
- `tests/test_score.py`: Valida o schema de `scores.json`, incluindo os campos de proveniência (`method`, `model`, `generated_at`).
- `tests/test_build_site_data.py`: Valida os cálculos agregados da população e massa salarial do Brasil.

---

## ⚖️ Créditos e Licença

- **Autor do Projeto Brasil:** Marcelo (marcelo.ai)
- **Inspiração e Arquitetura:** Andrej Karpathy ([karpathy/jobs](https://github.com/karpathy/jobs))
- **Fonte dos Dados:** IBGE — Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD Contínua 2022) / [Tabela 10287 (SIDRA)](https://sidra.ibge.gov.br/tabela/10287), buscável automaticamente via `scripts/fetch_ibge_data.py`.
- **Licença:** [MIT License](./LICENSE)
