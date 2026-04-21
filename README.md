**Documento principal de apresentação**

Este README é a documentação principal do projeto: segue uma visão organizada (introdução/contextualização), metodologia de investigação, respostas às perguntas do case, análises, hipóteses testadas e conclusões.

**1) Introdução / Contextualização**

- NovaShop: e‑commerce com operações B2C e B2B; desafio: entender padrões de pedidos, sazonalidade e, principalmente, a alta taxa de cancelamento e devoluções.
- Objetivo do projeto: responder as perguntas do case (Q1–Q6), identificar padrões e investigar a causa do pico em Nov/2023 e por que `trafego_pago` tem taxa de cancelamento elevada.

**2) Estrutura do repositório (pontos importantes)**
- Código de análise reprodutível: [scripts/analise.py](scripts/analise.py) — gera CSV/JSON em `outputs/` e contém funções de auditoria e testes de hipótese (Q4 e Q5).
- Notebooks explicativos: [questões/](questões/) — exploração passo-a-passo e visualizações (úteis para apresentação e QA).
- Prints / evidências visuais: `img/` (já incluídos) — gráficos e tabelas que usei para a narrativa.

Nota importante: os notebooks são a fonte narrativa e de visualização; `scripts/analise.py` foi deliberadamente reduzido para um runner de testes de hipótese (Q4/Q5) — mantenha a exploração e plots nos notebooks.

**3) Como rodar (reprodução rápida)**
1. Criar e ativar ambiente e instalar dependências:

```bash
python -m venv venv
source "venv/Scripts/activate"   # Git Bash / WSL (PowerShell: venv\Scripts\Activate.ps1)
pip install -r requirements.txt
```

2. Rodar todas as análises (gera arquivos em `outputs/`):

```bash
source "venv/Scripts/activate"
python scripts/analise.py --all
```

3. Testes complementares (hipóteses):
- Q4 (hipóteses sobre Nov/2023): `python scripts/analise.py --q4-tests` (ou `--all` já executa os testes)
- Q5 (análises de cancelamento por canal e efeito de cupom): `python scripts/analise.py --q5-tests`

Saídas importantes de testes:
- `outputs/q4_hypotheses.json`, `outputs/q4_coupon_penetration.csv`, `outputs/q4_segment_share.csv`, `outputs/q4_status_distribution_by_month.csv`
- `outputs/q5_channel_tests.json`, `outputs/q5_channel_cancel_rates_full.csv`
- `outputs/analysis_summary.json` (resumo compacto gerado pelo runner)

**4) Resumo das respostas (Q1–Q6) — pesquisas e evidências**

- **Q1 — Volume de pedidos por status**
  - Síntese: Entregue ≈ 9.901 (66%), Cancelado ≈ 2.526 (17%), Em Trânsito ≈ 1.365 (9%) — ver figura abaixo.
  - Evidência: ![Pedidos por Status](img/Pedidos por Status.png)

- **Q2 — Top 10 produtos (por quantidade e receita)**
  - Síntese: tabela com top10; exemplo: `Acessórios 43` entre os mais vendidos.
  - Evidência: ![Top10 Produtos](img/Top10 Produtos.png)

- **Q3 — Ticket médio por segmento (B2C vs B2B)**
  - Síntese: B2B tem ticket médio muito maior que B2C (diferença estatisticamente significativa pelo Welch t‑test no notebook).
  - Evidência: ![Ticket Médio](img/Ticket Medio.png)

- **Q4 — Evolução mensal (sazonalidade e pico Nov/2023)**
  - Síntese: pico claro em 2023-11 com 2.309 pedidos; série mensal está no README. Hipóteses foram formuladas e testadas (ver seção seguintes).
  - Evidência: ![Volumes 2023-2024](img/Volumes de Pedidos 2023-2024.png)

- **Q5 — Canal com maior taxa de cancelamento**
  - Síntese: `trafego_pago` apresenta a maior taxa de cancelamento (~30%) e ticket médio elevado. É o principal canal de risco identificado.
  - Evidência: ![Rentabilidade vs Cancelamento](img/Rentabilidade vs Cancelamento.png)

- **Q6 — Inconsistências / ETL**
  - Síntese: pipeline de tratamento aplicado; principais tratamentos e resultados resumidos no notebook (tabela de tratamento).
  - Evidência: ![Tratamento de Dados](img/Tratamento de Dados.png)

**5) Análises e hipóteses (o que foi testado / o que falta)**

- Trabalho feito (automatizado e reproduzível):
  - Implementei testes reproduzíveis diretamente em `scripts/analise.py` para as hipóteses principais:
    - `q4_hypotheses`: compara penetração de cupom entre Nov/2023 e Nov/2024, participação B2B/B2C, distribuição de status e busca por duplicações. Resultados em `outputs/q4_hypotheses.json`.
    - `q5_tests`: compara taxas de cancelamento entre `trafego_pago` e outros canais (teste de duas proporções), e testa o efeito de cupom sobre taxa de cancelamento (geral e em Nov/2023). Resultados em `outputs/q5_channel_tests.json`.

- Principais hipóteses (e suas verificações):
  1. Hipótese: campanhas/promoções em Nov/2023 aumentaram penetração de cupom e, por consequência, cancelamentos.
     - Teste: comparador de penetração de cupom (Nov/2023 vs Nov/2024) — `q4_hypotheses`.
     - Resultado (resumido): penetração de cupom similar entre nov/23 e nov/24 nos dados analisados (hipótese refutada parcialmente).
  2. Hipótese: Nov/2023 é explicado por concentração atípica de B2B.
     - Teste: participação B2B/B2C por mês — `q4_hypotheses`.
     - Resultado: participação B2B similar entre meses (hipótese não suportada).
  3. Hipótese: ocorrência de problema operacional (ruptura) elevou taxa de cancelamento em Nov/2023.
     - Teste: comparação de distribuição de status entre meses — `q4_hypotheses`.
     - Resultado: taxa de cancelamento similar (hipótese não suportada).
  4. Hipótese: pico é um artefato de duplicação de dados.
     - Teste: checagem de duplicados em Nov/2023 — `q4_hypotheses`.
     - Resultado: nenhuma duplicação detectada no conjunto atual (hipótese refutada).

- Sobre `trafego_pago` (Q5): testes comparativos feitos em `q5_tests` indicam que a taxa de cancelamento de `trafego_pago` é estatisticamente maior que de outros canais (detalhes e p‑values em `outputs/q5_channel_tests.json`). Além disso, verifiquei o efeito de cupom sobre cancelamento (geral e para Nov/2023) — os resultados estão no JSON de saída.

- O que NÃO foi testado / limitações:
  - Análises mais granulares por campanha/UTM (não disponível nos dados fornecidos); isso é crítico para identificar anúncios específicos com baixa qualidade.
  - Logs de pagamento (autorização/recusa) e dados de entregas (tracking) não estavam disponíveis — esses são inputs necessários para confirmar causas técnicas.
  - Análise de fraude/perfil do usuário (assinatura comportamental) ficou fora do escopo pela falta de dados adicionais.

**6) Conclusões e recomendações**

- `trafego_pago` é o principal canal de risco: alto volume e alta taxa de cancelamento; priorizar investigação de campanhas/segmentação e validar qualidade do tráfego.
- Recomendação operacional imediata: pausar / revisar campanhas pagas com ROI fraco; auditar fluxo de pagamento e checkout; adicionar validações para pedidos de alto valor vindos do canal pago.
- Recomendação de dados: enriquecer `pedidos` com `utm_campaign`, `payment_status`, `payment_provider`, e logs de fulfillment/entrega para análises posteriores.