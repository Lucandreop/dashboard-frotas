# Dashboard TNORTE — Gestão de Frota

Dashboard web para acompanhamento mensal do consumo de combustível da frota TNORTE.

## Como instalar

```bash
pip install -r requirements.txt
```

## Como rodar

```bash
streamlit run app.py
```

O browser abre automaticamente em `http://localhost:8501`.

## Como usar todo mês

1. Exporte a planilha do mês no formato `.xlsx` com a aba `Planilha1`
2. Abra o dashboard (`streamlit run app.py`)
3. Clique em **Browse files** e selecione a planilha
4. O dashboard detecta o período automaticamente
5. Use os filtros na sidebar para explorar os dados
6. Baixe a apresentação PPTX ou o Excel processado no final da página

## Estrutura de arquivos

```
├── app.py                   # ponto de entrada — rode este arquivo
├── core/
│   ├── data_loader.py       # carrega e valida a planilha Excel
│   ├── metrics.py           # KPIs, rankings, formatadores BR
│   └── filters.py           # aplica filtros da sidebar
├── ui/
│   ├── theme.py             # cores e CSS da identidade TNORTE
│   ├── header.py            # cabeçalho com logo
│   ├── kpis.py              # cards de KPI
│   ├── ranking.py           # podium Top 3
│   └── charts.py            # gráficos Plotly
├── export/
│   └── pptx_export.py       # gera a apresentação PowerPoint
├── data/                    # coloque aqui as planilhas de referência
├── requirements.txt
└── .streamlit/config.toml   # tema visual do Streamlit
```

## Formato esperado da planilha

- Aba: `Planilha1`
- Colunas obrigatórias: `Nº`, `Data Abast`, `Placa`, `Tipo/Modelo`, `Posto`,
  `Condutor`, `Produto`, `Vlr. litro`, `Qtde`, `Valor.total`,
  `Km/Hs anterior`, `Km/Hs abast`, `Km Perc.`, `Média`, `MetaMédia`

## Categorias de meta

| Categoria    | Meta km/L      | Tipos típicos              |
|--------------|----------------|----------------------------|
| Leve         | 8.0            | Furgões                    |
| Média        | 5.5            | Caminhonetes 3/4           |
| Pesada Leve  | 3.8 ou 4.0     | Toco, Microônibus          |
| Pesada       | 2.5, 3.2, 3.4  | Cavalo Mecânico, Truck     |
| Sem Meta     | —              | Equipamentos e outros      |

## KPIs esperados para Abril/2026

| KPI                | Valor           |
|--------------------|-----------------|
| Volume             | 43.861,38 L     |
| Investimento       | R$ 310.390,87   |
| Distância          | ~151.632 km     |
| Preço médio/litro  | ~R$ 7,08        |
