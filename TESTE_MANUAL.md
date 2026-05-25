# Teste Manual — Dashboard TNORTE

Siga os passos em ordem. Cada passo tem critério claro de aprovação.

---

## Preparação

```
1. Abrir terminal na pasta do projeto
2. Executar: pip install -r requirements.txt
3. Executar: streamlit run app.py
4. Aguardar abrir o browser em http://localhost:8501
```
✅ **Passou:** página exibe logo TNORTE e campo de upload  
❌ **Falhou:** erro no terminal ou tela em branco

---

## Bloco A — Upload e KPIs

```
A1. Clicar em "Browse files" e selecionar data/Abastecimentos_abril_2026.xlsx
```
✅ Mensagem verde: "✅ 256 abastecimentos carregados — Abril/2026"  
❌ Mensagem de erro ou nada acontece

```
A2. Verificar os 4 cards de KPI no topo
```
✅ Volume = **43.861,38 L**  
✅ Investimento = **R$ 310.390,87**  
✅ Distância = **151.632 km**  
✅ Preço médio = **R$ 7,08**  
❌ Qualquer valor diferente desses

```
A3. Verificar a seção "Análise de Custo por Rede"
```
✅ 3 cards aparecem (Bomba interna / Vôlus / Auto Posto Vulcão)  
✅ Bomba interna tem badge "🟢 Mais econômico"  
✅ Auto Posto Vulcão tem badge "🔴 Mais caro"  
✅ Gráfico de barras verticais aparece abaixo dos cards  
❌ Erro ou layout quebrado

---

## Bloco B — Ranking

```
B1. Rolar até a seção "🏆 Ranking de Eficiência"
```
✅ 4 colunas (Leve / Média / Pesada Leve / Pesada)  
✅ Cada coluna tem cabeçalho azul com emoji e meta  
✅ Top 3 com medalhas 🥇🥈🥉 em cada coluna  
✅ Placas acima da meta têm borda verde; abaixo, borda vermelha  
❌ Coluna vazia sem mensagem ou crash

---

## Bloco C — Análise por Categoria (abas)

```
C1. Rolar até "📈 Análise por Categoria de Veículo"
C2. Clicar na aba "Leve"
```
✅ 3 gráficos aparecem: Distância / Investimento / Eficiência  
✅ Gráfico de Eficiência tem linha tracejada vermelha com "Meta: 8,0 km/L"  
✅ Barras verdes = acima da meta; vermelhas = abaixo  
✅ Barras ordenadas (maior em cima)  
✅ Hover mostra valor da placa  
❌ Gráfico vazio sem motivo ou crash

```
C3. Passar o mouse sobre uma barra do gráfico
```
✅ Tooltip aparece com nome da placa e valor  

```
C4. Clicar no ícone de câmera (🔲) no canto do gráfico
```
✅ Faz download de um arquivo .png  

```
C5. Repetir C2-C4 para abas "Média", "Pesada Leve" e "Pesada"
```
✅ Cada aba mostra suas placas e sua meta específica  
✅ Linha tracejada em posição diferente em cada aba  

---

## Bloco D — Filtros da Sidebar

```
D1. Na sidebar, em "Categoria de Meta", selecionar apenas "Leve"
```
✅ Caption abaixo dos filtros atualiza (ex: "53/256 abastecimentos")  
✅ KPIs mudam para refletir só as placas Leve  
✅ Ranking mostra apenas categoria Leve com dados; outros mostram "Sem dados suficientes"  
✅ Abas "Média", "Pesada Leve", "Pesada" mostram "Nenhuma placa..."  

```
D2. Clicar em "🔄 Limpar Filtros"
```
✅ Todos os multiselects voltam a zero (nada selecionado)  
✅ KPIs voltam aos valores originais (43.861,38 L etc.)  

```
D3. Em "Posto / Rede", selecionar apenas "Bomba interna"
```
✅ Seção de custo por rede mostra apenas 1 card (Bomba interna)  
✅ KPIs refletem apenas abastecimentos na Bomba interna  

```
D4. Em "Placa", selecionar "EMPILHADEIRA" (placa sem km válido)
```
✅ App NÃO crasha (⚠️ este cenário pode cravar se o bug crítico não foi corrigido)  
✅ KPIs mostram litros e valor da EMPILHADEIRA  
✅ Ranking vazio ("Sem dados suficientes")  
✅ Gráfico de eficiência vazio com mensagem  

---

## Bloco E — Tabela e Drill-down

```
E1. Clicar em "📋 Ver detalhamento por placa"
```
✅ Tabela expansível aparece com colunas: Placa / Tipo / Categoria / Meta / Litros / Valor / Km Total / Média km/L / Status  
✅ Status mostra ✅ Acima ou ❌ Abaixo  
✅ Clique no cabeçalho das colunas ordena a tabela  

```
E2. Na seção "🔎 Análise Individual por Placa", selecionar uma placa no dropdown
```
✅ Gráfico de linha aparece com a evolução da eficiência ao longo do mês  
✅ Linha tracejada horizontal com a meta da placa  
✅ Painel de informações mostra Placa / Tipo / Meta / Condutor / Eficiência  

```
E3. Expandir "Ver todos os abastecimentos desta placa"
```
✅ Tabela completa dos registros da placa  
✅ Coluna km_valido mostra True/False  

---

## Bloco F — Exportação

```
F1. Clicar em "📊 Baixar Apresentação PPTX"
```
✅ Download de arquivo .pptx inicia  
✅ Arquivo abre no PowerPoint com 3 slides (Capa / KPIs / Top 5)  

```
F2. Clicar em "📥 Baixar Excel Processado"
```
✅ Download de arquivo .xlsx inicia  
✅ Arquivo tem 2 abas: "Abastecimentos" e "Resumo_por_Placa"  
✅ Aba "Resumo_por_Placa" tem colunas MediaKmL, km_valido, Categoria  

```
F3. Clicar em "📄 Baixar CSV Resumo"
```
✅ Download de arquivo .csv inicia  
✅ Separador é ponto-e-vírgula (;), decimal é vírgula (,)  

---

## Bloco G — Casos Extremos

```
G1. Subir um arquivo .xlsx com nome errado (ex: uma planilha qualquer sem as colunas certas)
```
✅ Mensagem vermelha listando quais colunas estão faltando  
✅ App NÃO mostra stacktrace  
✅ App NÃO trava  

```
G2. Com planilha carregada, ativar filtros até não restar nenhum registro
   (ex: Posto = "Bomba interna" E Placa = uma placa que só abasteceu na Vôlus)
```
✅ Mensagem amarela: "Nenhum registro com os filtros atuais"  
✅ App NÃO trava nem mostra zeros sem explicação  

---

## Critério de aprovação geral

| Bloco | Resultado |
|---|---|
| A — Upload e KPIs | ✅ / ❌ |
| B — Ranking | ✅ / ❌ |
| C — Análise por categoria | ✅ / ❌ |
| D — Filtros | ✅ / ❌ |
| E — Tabela e drill-down | ✅ / ❌ |
| F — Exportação | ✅ / ❌ |
| G — Casos extremos | ✅ / ❌ |

**Aprovado para uso:** todos os blocos A–G marcados como ✅
