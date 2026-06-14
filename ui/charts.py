"""
Funções que geram gráficos Plotly com a identidade visual da TNORTE.
Cada função recebe um DataFrame e retorna um objeto plotly.graph_objects.Figure.
O Streamlit renderiza esse objeto com st.plotly_chart().
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from core.metrics import fmt_brl, fmt_num, ORDEM_MESES
from ui.theme import (
    COR_AZUL_PRIMARIO, COR_VERMELHO, COR_AZUL_CLARO,
    COR_VERMELHO_CLARO, COR_VERDE_OK, COR_TEXTO_PRINCIPAL
)

# Configuração de layout aplicada a todos os gráficos
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
    """Barras horizontais: distância total (km) por placa."""
    df = df_placas[df_placas['TotalKm'] > 0].sort_values('TotalKm', ascending=True)

    if df.empty:
        return _grafico_vazio("Sem dados de distância para esta seleção")

    fig = go.Figure(go.Bar(
        x=df['TotalKm'],
        y=df['Placa'],
        orientation='h',
        marker_color=COR_AZUL_PRIMARIO,
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
    """Barras horizontais: investimento total (R$) por placa."""
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
    Verde = acima da meta | Vermelho = abaixo da meta.
    """
    df = df_placas[df_placas['MediaKmL'] > 0].sort_values('MediaKmL', ascending=True)

    if df.empty:
        return _grafico_vazio("Sem dados de eficiência para esta seleção")

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


# ─── CUSTO POR POSTO ──────────────────────────────────────────────────────────

def grafico_custo_por_posto(agg_posto: pd.DataFrame) -> go.Figure:
    """
    Barras verticais: preço médio ponderado (R$/L) por posto.
    Verde = mais barato | Vermelho = mais caro | Azul = intermediário.
    """
    agg = agg_posto
    if agg.empty:
        return _grafico_vazio("Sem dados de posto")

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
    """Linha temporal de eficiência (km/L) para uma placa no período."""
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


# ─── CONSOLIDADO MENSAL ────────────────────────────────────────────────────────

def grafico_consolidado_litros(df_cons: pd.DataFrame) -> go.Figure:
    """Barras: litros de diesel por mês (jan a dez)."""
    # Filtra apenas meses com dados para não poluir o gráfico com zeros
    df = df_cons[df_cons['Litros'] > 0]

    fig = go.Figure(go.Bar(
        x=df['mes_nome'],
        y=df['Litros'],
        marker_color=COR_AZUL_PRIMARIO,
        text=[fmt_num(v, 0) + ' L' for v in df['Litros']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>%{y:,.0f} L<extra></extra>',
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="⛽ Litros de Diesel por Mês",
                   font=dict(size=13, color=COR_AZUL_PRIMARIO)),
        xaxis=dict(categoryorder='array', categoryarray=ORDEM_MESES),
        yaxis=dict(showgrid=True, gridcolor='#EEEEEE', showticklabels=False),
        height=320,
    )
    return fig


def grafico_consolidado_km(df_cons: pd.DataFrame) -> go.Figure:
    """Barras: km rodado por mês (jan a dez)."""
    df = df_cons[df_cons['Km'] > 0]

    fig = go.Figure(go.Bar(
        x=df['mes_nome'],
        y=df['Km'],
        marker_color=COR_AZUL_CLARO,
        text=[fmt_num(v, 0) + ' km' for v in df['Km']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>%{y:,.0f} km<extra></extra>',
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="📍 Km Rodado por Mês",
                   font=dict(size=13, color=COR_AZUL_PRIMARIO)),
        xaxis=dict(categoryorder='array', categoryarray=ORDEM_MESES),
        yaxis=dict(showgrid=True, gridcolor='#EEEEEE', showticklabels=False),
        height=320,
    )
    return fig


def grafico_consolidado_custos(df_cons: pd.DataFrame) -> go.Figure:
    """
    Barras agrupadas: R$ Combustível, R$ ARLA e R$ Pedágio por mês.
    Só exibe meses que têm pelo menos um valor > 0.
    """
    # Filtra meses com qualquer dado
    df = df_cons[(df_cons['R_Comb'] > 0) | (df_cons['R_Arla'] > 0) | (df_cons['R_Pedagio'] > 0)]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Combustível',
        x=df['mes_nome'],
        y=df['R_Comb'],
        marker_color=COR_AZUL_PRIMARIO,
        hovertemplate='<b>%{x}</b><br>Combustível: R$ %{y:,.2f}<extra></extra>',
    ))

    fig.add_trace(go.Bar(
        name='ARLA 32',
        x=df['mes_nome'],
        y=df['R_Arla'],
        marker_color='#2ECC71',
        hovertemplate='<b>%{x}</b><br>ARLA: R$ %{y:,.2f}<extra></extra>',
    ))

    fig.add_trace(go.Bar(
        name='Pedágio',
        x=df['mes_nome'],
        y=df['R_Pedagio'],
        marker_color=COR_VERMELHO,
        hovertemplate='<b>%{x}</b><br>Pedágio: R$ %{y:,.2f}<extra></extra>',
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="💰 Custo por Mês — 3 Contas Separadas",
                   font=dict(size=13, color=COR_AZUL_PRIMARIO)),
        barmode='group',
        xaxis=dict(categoryorder='array', categoryarray=ORDEM_MESES),
        yaxis=dict(showgrid=True, gridcolor='#EEEEEE', showticklabels=False),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=350,
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def grafico_consolidado_media(df_cons: pd.DataFrame) -> go.Figure:
    """Linha com marcadores: média km/L por mês (jan a dez)."""
    df = df_cons[df_cons['MediaKmL'] > 0]

    fig = go.Figure(go.Scatter(
        x=df['mes_nome'],
        y=df['MediaKmL'],
        mode='lines+markers',
        line=dict(color=COR_AZUL_PRIMARIO, width=2.5),
        marker=dict(size=10, color=COR_VERMELHO, line=dict(color='white', width=1.5)),
        text=[fmt_num(v, 2) + ' km/L' for v in df['MediaKmL']],
        textposition='top center',
        hovertemplate='<b>%{x}</b><br>%{y:.2f} km/L<extra></extra>',
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="🏎️ Média km/L por Mês (só diesel)",
                   font=dict(size=13, color=COR_AZUL_PRIMARIO)),
        xaxis=dict(categoryorder='array', categoryarray=ORDEM_MESES,
                   showgrid=True, gridcolor='#EEEEEE'),
        yaxis=dict(title='km/L', showgrid=True, gridcolor='#EEEEEE'),
        height=320,
    )
    return fig


# ─── ARLA E PEDÁGIO POR PLACA ─────────────────────────────────────────────────

def grafico_arla_por_placa(df_arla: pd.DataFrame) -> go.Figure:
    """Barras horizontais: R$ de ARLA 32 por placa."""
    if df_arla.empty:
        return _grafico_vazio("Sem lançamentos de ARLA 32 nesta seleção")

    df = df_arla.sort_values('ValorArla', ascending=True)

    fig = go.Figure(go.Bar(
        x=df['ValorArla'],
        y=df['Placa'],
        orientation='h',
        marker_color='#2ECC71',
        text=[fmt_brl(v) for v in df['ValorArla']],
        textposition='outside',
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>',
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="🧪 R$ ARLA 32 por Placa",
                   font=dict(size=13, color=COR_AZUL_PRIMARIO)),
        xaxis=dict(showgrid=True, gridcolor='#EEEEEE', showticklabels=False),
        yaxis=dict(tickfont=dict(size=11)),
        showlegend=False,
        height=_altura_dinamica(len(df)),
    )
    return fig


def grafico_pedagio_por_placa(df_ped: pd.DataFrame) -> go.Figure:
    """Barras horizontais: R$ de pedágio por placa."""
    if df_ped.empty:
        return _grafico_vazio("Sem lançamentos de pedágio nesta seleção")

    df = df_ped.sort_values('ValorPedagio', ascending=True)

    fig = go.Figure(go.Bar(
        x=df['ValorPedagio'],
        y=df['Placa'],
        orientation='h',
        marker_color=COR_VERMELHO,
        text=[fmt_brl(v) for v in df['ValorPedagio']],
        textposition='outside',
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>',
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="🛣️ R$ Pedágio por Placa",
                   font=dict(size=13, color=COR_AZUL_PRIMARIO)),
        xaxis=dict(showgrid=True, gridcolor='#EEEEEE', showticklabels=False),
        yaxis=dict(tickfont=dict(size=11)),
        showlegend=False,
        height=_altura_dinamica(len(df)),
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
