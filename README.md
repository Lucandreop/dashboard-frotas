# Dashboard TNORTE — Gestão de Frota

Dashboard web em Streamlit para acompanhamento mensal do consumo de combustível da frota TNORTE. O gestor faz upload da planilha Excel do mês e o sistema gera KPIs, rankings de eficiência, gráficos interativos e exportação para PPTX.

**Repositório:** [github.com/Lucandreop/dashboard-frotas](https://github.com/Lucandreop/dashboard-frotas)

---

## O que o dashboard mostra

- **4 KPIs** — volume (L), investimento (R$), distância (km), preço médio/litro
- **Análise de custo por rede** — comparação de preço médio ponderado entre Bomba interna, Vôlus e Auto Posto Vulcão
- **Ranking Top 3** — eficiência km/L por categoria de veículo (Leve / Média / Pesada Leve / Pesada)
- **Gráficos por categoria** — distância, investimento e eficiência com linha de meta
- **Drill-down por placa** — evolução da eficiência ao longo do mês
- **Exportação** — apresentação PPTX, Excel processado e CSV

---

## Rodar localmente

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Iniciar o dashboard
streamlit run app.py
```

Abre em `http://localhost:8501`. Faça upload da planilha `.xlsx` pelo botão na tela.

---

## Atualizar todo mês

1. Receba a planilha do mês no formato `.xlsx` com a aba `Planilha1`
2. Abra o dashboard (`streamlit run app.py`) ou acesse o link do Streamlit Cloud
3. Clique em **Browse files** e selecione a planilha
4. O dashboard detecta o período (mês/ano) automaticamente
5. Use os **filtros da sidebar** para explorar por categoria, posto, placa ou condutor
6. Baixe a **apresentação PPTX** ou o **Excel processado** no final da página

> A planilha **não é salva** no servidor — fica apenas na sessão do navegador.

---

## Publicar atualização de código no GitHub

```bash
# Na pasta do projeto:
git add app.py core/ ui/ export/
git commit -m "descricao da mudanca"
git push
```

O Streamlit Cloud atualiza automaticamente em ~30 segundos após o push.

> **Nunca faça `git add data/`** — a pasta `data/` está no `.gitignore` para proteger os dados da empresa.

---

## Estrutura de arquivos

```
├── app.py                    # ponto de entrada — rode este arquivo
├── core/
│   ├── data_loader.py        # carrega e valida a planilha Excel
│   ├── metrics.py            # KPIs, rankings, METAS_CATEGORIA, formatadores BR
│   └── filters.py            # aplica filtros da sidebar
├── ui/
│   ├── theme.py              # cores e CSS da identidade TNORTE
│   ├── header.py             # cabeçalho com logo
│   ├── kpis.py               # cards de KPI
│   ├── ranking.py            # pódio Top 3
│   └── charts.py             # gráficos Plotly
├── export/
│   └── pptx_export.py        # gera a apresentação PowerPoint
├── data/                     # planilhas locais (ignoradas pelo git)
├── requirements.txt          # dependências Python
├── TESTE_MANUAL.md           # roteiro de validação passo a passo
└── .streamlit/config.toml    # tema visual (cores TNORTE)
```

---

## Formato esperado da planilha

- **Aba:** `Planilha1`
- **Colunas obrigatórias:**

| Coluna | Tipo | Observação |
|---|---|---|
| `Nº` | inteiro | sequência do lançamento |
| `Data Abast` | data | data do abastecimento |
| `Placa` | texto | pode ter espaços extras — o sistema limpa automaticamente |
| `Tipo/Modelo` | texto | Furgão, 3/4, Truck, etc. |
| `Posto` | texto | Bomba interna / Vôlus / Auto Posto Vulcão |
| `Condutor` | texto | nome completo |
| `Produto` | texto | ex: DIESEL S10 |
| `Vlr. litro` | decimal | preço unitário |
| `Qtde` | decimal | litros abastecidos |
| `Valor.total` | decimal | total pago |
| `Km/Hs anterior` | inteiro | hodômetro antes do abastecimento |
| `Km/Hs abast` | inteiro | hodômetro no abastecimento (999999 = sem hodômetro) |
| `Km Perc.` | inteiro | distância percorrida |
| `Média` | decimal | km/L calculado |
| `MetaMédia` | misto | número (ex: 5.5) ou texto "Sem meta Def" |

---

## Categorias de meta

| Categoria | Meta km/L | Tipos típicos |
|---|---|---|
| Leve | 8,0 | Furgões |
| Média | 5,5 | Caminhonetes 3/4 |
| Pesada Leve | 3,8 ou 4,0 | Toco, Microônibus |
| Pesada | 2,5, 3,2 ou 3,4 | Cavalo Mecânico, Truck |
| Sem Meta | — | Equipamentos e outros |

---

## Regras de negócio

**km válido** — linha só entra no cálculo de eficiência se:
- `Km/Hs anterior > 0` (não é o primeiro abastecimento da placa)
- `Km/Hs abast ≠ 999999` (hodômetro funcionando)
- `Km Perc. > 0` (rodou alguma distância)
- `Km Perc. ≤ 3.000` (não é erro de digitação)

**Média km/L** — calculada como média ponderada:
```
média = Σ(km percorrido válido) / Σ(litros das linhas válidas)
```

**Volume e valor** — contam todos os registros, inclusive sem km válido.

---

## KPIs de referência — Abril/2026

| KPI | Valor |
|---|---|
| Volume total | 43.861,38 L |
| Investimento total | R$ 310.390,87 |
| Distância percorrida | 151.632 km |
| Preço médio/litro | R$ 7,08 |
| Bomba interna | R$ 6,93/L |
| Vôlus | R$ 7,25/L |
| Auto Posto Vulcão | R$ 7,49/L |
