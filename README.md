**📊 Desafio Técnico: Análise de Dados - NovaShop (Peers Group)**

Este repositório contém a resolução do case técnico de análise de dados da NovaShop. O objetivo deste projeto é auditar a base de dados do e-commerce, realizar o tratamento de inconsistências e extrair insights estratégicos sobre vendas, clientes e produtos.

**⚙️ Como Executar o Projeto**

1. Clone o repositório e acesse a pasta raiz:

```bash
git clone https://github.com/gustavobione/NovaShop.git
cd "NovaShop"
```

2. Crie e ative um ambiente virtual:

- No Git Bash / macOS / Linux:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

- No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Execute os scripts em ordem, começando obrigatoriamente pela Questão 6 (ETL), pois ela gera os arquivos limpos (_limpo.csv) necessários para as demais análises.

**🧹 Passo 0: Data Quality & ETL (Resposta da Questão 6)**

Antes de qualquer análise de negócios, foi construído um pipeline de Qualidade de Dados. A base original continha ruídos que comprometeriam o cálculo de faturamento e métricas de clientes.

**Principais Tratamentos Realizados:**

- **Pedidos:** Remoção de 79 registros sem valor de faturamento (impossível inferir receita) e exclusão de linhas com datas corrompidas.
- **Itens do Pedido:** Conversão de valores numéricos negativos (quantidades e preços) para absolutos (`abs()`), corrigindo erros de digitação. Imputação de `0.0` para descontos nulos.
- **Tickets de Suporte:** Campos `date_resolucao` vazios foram mantidos, pois representam uma regra de negócio válida (tickets ainda em aberto). Status legados (resolvido, escalado) foram padronizados.
- **Global:** Remoção de duplicatas exatas e aplicação de `strip()` e `snake_case` para padronização de chaves de cruzamento.

[📸 INSERIR PRINT DA TABELA "RELATÓRIO DE AUDITORIA E TRATAMENTOS" AQUI]

**📈 Análise de Negócios e Insights**

1. **Distribuição de Pedidos por Status**

	A análise de status revela a saúde da operação logística da NovaShop.

	[📸 INSERIR PRINT DA TABELA DE DISTRIBUIÇÃO E DO GRÁFICO DE PIZZA AQUI]

	**Conclusão:** Foi possível mapear com precisão o funil de entrega, identificando o percentual de sucesso ("Entregue") frente aos gargalos operacionais ("Cancelado" e "Devolvido").

2. **Top 10 Produtos Mais Vendidos**

	Cruzamento da base de `itens_pedido` com o catálogo de `produtos` para identificar a curva A de vendas, ordenando pelo volume de saída e calculando a receita real gerada por item (`quantidade * preco_praticado`).

	[📸 INSERIR PRINT DA TABELA "TOP 10 PRODUTOS" AQUI]

3. **Comportamento de Compra: B2C vs B2B**

	Foi realizada uma análise para verificar se o tipo de cliente dita o poder de compra. Para garantir rigor analítico, além da média aplicou-se um Teste de Hipótese Estatística (Welch's T-Test) para comparar tickets médios entre segmentos.

	[📸 INSERIR PRINT DA TABELA "TICKET MÉDIO POR SEGMENTO" E DO "RESULTADO DO TESTE ESTATÍSTICO" AQUI]

	**Conclusão Estratégica:** O p-valor indicou relevância estatística na diferença dos tickets médios entre B2B e B2C, justificando políticas segmentadas de precificação e marketing.

4. **Sazonalidade e Validação de Hipóteses**

	Ao plotar a evolução temporal de vendas entre 2023 e 2024, identificou-se um pico anormal em Novembro de 2023. Foram testadas 4 hipóteses:

	- Black Friday/Descontos? Refutada.
	- Contratos B2B Atípicos? Refutada.
	- Ruptura de Estoque (Falsas Vendas)? Refutada.
	- Erro de Engenharia de Dados? Confirmada. Diagnóstico: pico fruto de duplicação de IDs de pedidos.

	[📸 INSERIR PRINT DO GRÁFICO DE LINHA "EVOLUÇÃO MENSAL" E DO CONSOLE COM O ALERTA DE DUPLICAÇÃO AQUI]

5. **Eficiência por Canal de Aquisição (Rentabilidade vs. Risco)**

	Cruzamento dos canais de entrada com faturamento e taxa de desistência. A análise mostra que alguns canais, apesar de gerar ticket médio competitivo, apresentam taxas de cancelamento elevadas, indicando tráfego desqualificado ou risco de fraude.

	[📸 INSERIR PRINT DA TABELA "PERFORMANCE POR CANAL" E DO GRÁFICO DE BARRAS/LINHAS AQUI]

Projeto desenvolvido como parte do processo seletivo da Peers Group