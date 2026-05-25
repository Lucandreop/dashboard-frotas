"""
Funções que geram gráficos Plotly com a identidade visual da TNORTE.
Cada função recebe um DataFrame e retorna um objeto plotly.graph_objects.Figure.
O Streamlit renderiza esse objeto com st.plotly_chart().
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from core.metrics import fmt_brl, fmt_num
from ui.theme import (
    COR_AZUL_PRIMARIO, COR_VERMELHO, COR_AZUL_CLARO,
    COR_VERMELHO_CLARO, COR_VERDE_OK, COR_TEXTO_PRINCIPAL
)

# Configuração de layout aplicada a todos os gráficos (evita repetição)
_LAYOUT_BASE = dict(
    font=dict(family="Calibri, Segoe UI, sans-serif", size=12, color=COR_TEXTO_PRINCIPAL),
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=10, r=80, t=45, b=10),
    hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#CCCCCC"),
)


def _altura_dinamica(n_itens: int, min_px: int = 280) -> int:
    """Calcula a altura do gráfico conforme a quantidade de barras."""
    return max(min_px, n_itens * 30 + 60)


# ─── GRÁFICOS DA ANÁLISE POR CATEGORIA ────────────────────────────────────────

def grafico_km_por_placa(df_placas: pd.DataFrame) -> go.Figure:
    """
    Barras horizontais: distância total (km) por placa.
    Ordenado do maior para o menor.
    """
    df = df_placas[df_placas['TotalKm'] > 0].sort_values('TotalKm', ascending=True)

    if df.empty:
        return _grafico_vazio("Sem dados de distância para esta seleção")

    fig = go.Figure(go.Bar(
        x=df['TotalKm'],
        y=df['Placa'],
        orientation='h',
        marker_color=COR_AZUL_PRIMARIO,
        # Rótulo na ponta da barra com o valor formatado
        text=[fmt_num(v) + ' km' for v in df['TotalKm']],
        textposition='outside',
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>%{x:,.0f} km<extra></extra>',
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="📍 Distância Total (km)", font=dict(size=13, color=COR_AZUL_PRIMARIO)),
        xaxis=dict(showgrid=True, gridcolor='#EEEEEE', showticklabels=False),
        yaxis=dict(tickfont=dict(size=11)),
        showlegend=False,
        height=_altura_dinamica(len(df)),
    )
    return fig


def grafico_valor_por_placa(df_placas: pd.DataFrame) -> go.Figure:
    """
    Barras horizontais: investimento total (R$) por placa.
    """
    df = df_placas[df_placas['TotalValor'] > 0].sort_values('TotalValor', ascending=True)

    if df.empty:
        return _grafico_vazio("Sem dados de valor para esta seleção")

    fig = go.Figure(go.Bar(
        x=df['TotalValor'],
        y=df['Placa'],
        orientation='h',
        marker_color=COR_VERMELHO_CLARO,
        text=[fmt_brl(v) for v in df['TotalValor']],
        textposition='outside',
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>',
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="💰 Investimento Total (R$)", font=dict(size=13, color=COR_AZUL_PRIMARIO)),
        xaxis=dict(showgrid=True, gridcolor='#EEEEEE', showticklabels=False),
        yaxis=dict(tickfont=dict(size=11)),
        showlegend=False,
        height=_altura_dinamica(len(df)),
    )
    return fig


def grafico_eficiencia_por_placa(df_placas: pd.DataFrame, meta: float) -> go.Figure:
    """
    Barras horizontais: eficiência (km/L) por placa.

    Barras verdes = acima da meta  |  Barras vermelhas = abaixo da meta
    Linha tracejada vermelha = a meta de referência da categoria
    """
    df = df_placas[df_placas['MediaKmL'] > 0].sort_values('MediaKmL', ascending=True)

    if df.empty:
        return _grafico_vazio("Sem dados de eficiência para esta seleção")

    # Cor individual por barra: verde se ≥ meta, vermelho se < meta
    cores = [COR_VERDE_OK if v >= meta else COR_VERMELHO for v in df['MediaKmL']]

    fig = go.Figure(go.Bar(
        x=df['MediaKmL'],
        y=df['Placa'],
        orientation='h',
        marker_color=cores,
        text=[fmt_num(v, 2) + ' km/L' for v in df['MediaKmL']],
        textposition='outside',
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>%{x:.2f} km/L<extra></extra>',
    ))

    # Linha vertical tracejada indicando a meta da categoria
    fig.add_vline(
        x=meta,
        line_dash="dash",
        line_color=COR_VERMELHO,
        line_width=2,
        annotation_text=f"  Meta: {fmt_num(meta, 1)} km/L",
        annotation_position="top right",
        annotation_font=dict(color=COR_VERMELHO, size=11),
    )

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="⚡ Eficiência (km/L)", font=dict(size=13, color=COR_AZUL_PRIMARIO)),
        xaxis=dict(showgrid=True, gridcolor='#EEEEEE', showticklabels=False),
        yaxis=dict(tickfont=dict(size=11)),
        showlegend=False,
        height=_altura_dinamica(len(df)),
    )
    return fig


# ─── GRÁFICO DE CUSTO POR POSTO ───────────────────────────────────────────────

def grafico_custo_por_posto(agg_posto: pd.DataFrame) -> go.Figure:
    """
    Barras verticais comparando preço médio ponderado (R$/L) por posto.
    Recebe o DataFrame já agregado retornado por metrics.calcular_custo_por_posto().
    Verde = mais barato  |  Vermelho = mais caro  |  Azul = intermediário
    """
    agg = agg_posto  # renomeia para clareza interna

    if agg.empty:
        return _grafico_vazio("Sem dados de posto")

    # Identifica o mais barato e o mais caro
    idx_min = agg['PrecoMedio'].idxmin()
    idx_max = agg['PrecoMedio'].idxmax()

    cores = []
    for idx in agg.index:
        if idx == idx_min:
            cores.append(COR_VERDE_OK)
        elif idx == idx_max:
            cores.append(COR_VERMELHO)
        else:
            cores.append(COR_AZUL_CLARO)

    hover = [
        f"<b>{p}</b><br>Preço médio: R$ {pm:.2f}<br>Volume: {fmt_num(vol, 0)} L"
        for p, pm, vol in zip(agg['Posto'], agg['PrecoMedio'], agg['TotalLitros'])
    ]

    fig = go.Figure(go.Bar(
        x=agg['Posto'],
        y=agg['PrecoMedio'],
        marker_color=cores,
        text=[f"R$ {v:.2f}".replace('.', ',') for v in agg['PrecoMedio']],
        textposition='outside',
        customdata=list(zip(agg['TotalLitros'], hover)),
        hovertemplate='%{customdata[1]}<extra></extra>',
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="⛽ Preço Médio por Rede de Posto (R$/L)",
                   font=dict(size=13, color=COR_AZUL_PRIMARIO)),
        yaxis=dict(title='R$/Litro', showgrid=True, gridcolor='#EEEEEE'),
        xaxis=dict(title=''),
        height=350,
    )
    return fig


# ─── DRILL-DOWN: EVOLUÇÃO DE UMA PLACA ────────────────────────────────────────

def grafico_evolucao_placa(df_placa: pd.DataFrame, placa: str) -> go.Figure:
    """
    Linha temporal mostrando a eficiência (km/L) ao longo do mês para uma placa.
    Inclui linha horizontal tracejada com a meta da placa.
    """
    # Apenas registros com km válido, ordenados por data
    df_valido = df_placa[df_placa['km_valido'] == True].sort_values('Data Abast')

    if df_valido.empty:
        return _grafico_vazio(f"Sem km válido registrado para {placa}")

    fig = go.Figure(go.Scatter(
        x=df_valido['Data Abast'],
        y=df_valido['Média'],
        mode='lines+markers',
        line=dict(color=COR_AZUL_PRIMARIO, width=2.5),
        marker=dict(size=9, color=COR_VERMELHO, line=dict(color='white', width=1.5)),
        hovertemplate='<b>%{x|%d/%m}</b><br>%{y:.2f} km/L<extra></extra>',
        name='km/L',
    ))

    # Linha da meta (se existir)
    metas_validas = df_placa['MetaNum'].dropna()
    if not metas_validas.empty:
        meta = float(metas_validas.iloc[0])
        fig.add_hline(
            y=meta,
            line_dash="dash",
            line_color=COR_VERMELHO,
            line_width=1.5,
            annotation_text=f"  Meta: {fmt_num(meta, 1)} km/L",
            annotation_position="right",
            annotation_font=dict(color=COR_VERMELHO, size=11),
        )

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(
            text=f"📈 Evolução da Eficiência — {placa}",
            font=dict(size=13, color=COR_AZUL_PRIMARIO)
        ),
        xaxis=dict(title='', showgrid=True, gridcolor='#EEEEEE'),
        yaxis=dict(title='km/L', showgrid=True, gridcolor='#EEEEEE'),
        height=330,
    )
    return fig


# ─── AUXILIAR ─────────────────────────────────────────────────────────────────

def _grafico_vazio(mensagem: str) -> go.Figure:
    """Retorna uma figura vazia com mensagem informativa."""
    fig = go.Figure()
    fig.add_annotation(
        text=mensagem, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=13, color="#6B6B6B")
    )
    fig.update_layout(**_LAYOUT_BASE, height=200)
    return fig
