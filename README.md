# AI Exposure of the Brazilian Job Market (IBGE COD)

> **Réplica exata do projeto [karpathy/jobs](https://github.com/karpathy/jobs) de Andrej Karpathy adaptado para os microdados da PNAD Contínua / IBGE (2022).**

## Aggregate Statistics

- **Total Occupations (COD Subgroups):** 87
- **Total Jobs:** 87,830,902
- **Total Monthly Wages:** R$ 250.4B
- **Job-weighted Average AI Exposure:** **4.03/10**

---

## Breakdown by Exposure Tier

| Tier | Occupations | Jobs | % of Jobs | Monthly Wages | Avg Pay |
|---|---|---|---|---|---|
| Minimal (0-1) | 0 | 0 | 0.0% | R$ 0.0B | R$ 0 |
| Low (2-3) | 12 | 18,700,971 | 21.3% | R$ 40.5B | R$ 2,165 |
| Moderate (4-5) | 71 | 61,287,174 | 69.8% | R$ 182.1B | R$ 2,972 |
| High (6-7) | 2 | 6,863,168 | 7.8% | R$ 22.0B | R$ 3,211 |
| Very high (8-10) | 2 | 979,589 | 1.1% | R$ 5.7B | R$ 5,821 |

---

## All Occupations (Sorted by AI Exposure)

| Code | Occupation | Section | Pay (R$) | Jobs | AI Exposure | Rationale |
|---|---|---|---|---|---|---|
| 10.62 | **Atividades dos serviços de tecnologia da informação** | Alojamento e alimentação | R$ 5,941 | 875,815 | **9/10** | Trabalho 100% digital em computador focado em código, análise de dados e arquitetura, áreas em rápida evolução por IA. |
| 10.63 | **Atividades de prestação de serviços de informação** | Alojamento e alimentação | R$ 4,807 | 103,774 | **8/10** | Processamento de informação digital, redação e suporte técnico altamente expostos a LLMs. |
| 14.82 | **Serviços de escritório, de apoio administrativo e outros serviços prestados a empresas** | Alojamento e alimentação | R$ 2,006 | 1,033,243 | **7/10** | Rotinas de escritório, fluxo de documentos e atendimento ao cliente suscetíveis à automação por agentes de IA. |
| 16.85 | **Educação** | Alojamento e alimentação | R$ 3,425 | 5,829,925 | **6/10** | Ensino e criação de conteúdo instrucional com alto potencial de suporte por IA, mantendo interação humana. |
| 7.48 | **Comércio, exceto de veiculos automotores e motocicletas** | Comércio, reparação de veículos automotores e motocicletas | R$ 2,461 | 12,755,805 | **5/10** | Vendas e atendimento com mix de atendimento presencial e automação e-commerce. |
| 7.45 | **Comércio e reparação de veículos automotores e motocicletas** | Comércio, reparação de veículos automotores e motocicletas | R$ 2,474 | 2,278,879 | **5/10** | Vendas e atendimento com mix de atendimento presencial e automação e-commerce. |
| 22.00 | **Atividades maldefinidas** | Alojamento e alimentação | R$ 3,321 | 5,716,958 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 17.86 | **Atividades de atenção à saúde humana** | Alojamento e alimentação | R$ 4,502 | 4,752,742 | **4/10** | Atendimento presencial e cuidados médicos com barreira física, combinando diagnósticos digitais. |
| 15.84 | **Administração pública, defesa e seguridade social** | Alojamento e alimentação | R$ 4,929 | 4,101,378 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 20.97 | **Serviços domésticos** | Alojamento e alimentação | R$ 1,060 | 3,734,805 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 9.56 | **Alimentação** | Alojamento e alimentação | R$ 1,909 | 3,478,312 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 19.96 | **Outras atividades de serviços pessoais** | Alojamento e alimentação | R$ 1,764 | 2,585,171 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 14.81 | **Serviços para edificios e atividades paisagisticas** | Alojamento e alimentação | R$ 1,531 | 2,473,148 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 13.69 | **Atividades jurídicas, de contabilidade e de auditoria** | Alojamento e alimentação | R$ 5,867 | 1,749,567 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 3.32 | **Fabricação de produtos diversos** | Indústrias de transformação | R$ 2,663 | 1,738,168 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 3.14 | **Confecção de artigos do vestuário e acessórios** | Indústrias de transformação | R$ 1,612 | 1,286,582 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 3.10 | **Fabricação de produtos alimenticios e bebidas** | Indústrias de transformação | R$ 2,245 | 1,069,673 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 3.25 | **Fabricação de produtos de metal, exceto máquinas e equipamentos** | Indústrias de transformação | R$ 2,758 | 1,020,804 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 14.80 | **Atividades de vigilância, segurança e investigação** | Alojamento e alimentação | R$ 2,124 | 835,384 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 11.64 | **Atividades de serviços financeiros** | Alojamento e alimentação | R$ 6,382 | 827,661 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 13.71 | **Serviços de arquitetura e engenharia; testes e análises técnicas** | Alojamento e alimentação | R$ 5,856 | 620,102 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 3.31 | **Fabricação de móveis** | Indústrias de transformação | R$ 2,411 | 564,227 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 5.38 | **Coleta, tratamento e disposição de resíduos; recuperação de materiais** | Água, esgoto, atividades de gestão de resíduos e descontaminação | R$ 1,511 | 558,633 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 17.87 | **Atividades de atenção à saúde humana integradas com assistência social, inclusive prestadas em residências coletivas e particulares** | Alojamento e alimentação | R$ 1,988 | 522,637 | **4/10** | Atendimento presencial e cuidados médicos com barreira física, combinando diagnósticos digitais. |
| 12.68 | **Atividades imobiliárias** | Alojamento e alimentação | R$ 4,648 | 473,598 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 13.74 | **Outras atividades profissionais, científicas e técnicas** | Alojamento e alimentação | R$ 3,939 | 467,394 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 19.95 | **Reparação e manutenção de equipamentos de informatica e comunicação e de objetos pessoais e domésticos** | Alojamento e alimentação | R$ 2,106 | 458,005 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 3.13 | **Fabricação de produtos têxteis** | Indústrias de transformação | R$ 2,009 | 437,610 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 18.93 | **Atividades esportivas e de recreação e lazer** | Alojamento e alimentação | R$ 2,950 | 433,225 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
| 13.73 | **Publicidade e pesquisas de mercado** | Alojamento e alimentação | R$ 4,923 | 373,536 | **4/10** | Ocupação com combinação de tarefas físicas presenciais e rotinas administrativas moderadas. |
