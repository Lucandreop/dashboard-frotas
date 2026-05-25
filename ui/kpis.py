"""
Componente dos 4 cards de KPI do topo do dashboard.
"""

import streamlit as st
from core.metrics import fmt_brl, fmt_num


def renderizar_kpis(kpis: dict) -> None:
    """
    Exibe os 4 cards de KPI lado a lado usando st.columns.

    No desktop ficam em 4 colunas; no celular o Streamlit empilha automaticamente.
    Os valores usam formatação brasileira (ponto milhar, vírgula decimal).
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">⛽ Volume Abastecido</div>
            <div class="kpi-valor">{fmt_num(kpis['total_litros'], 2)} L</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">💰 Investimento Total</div>
            <div class="kpi-valor">{fmt_brl(kpis['total_valor'])}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">📍 Distância Percorrida</div>
            <div class="kpi-valor">{fmt_num(kpis['total_km'])} km</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🏷️ Preço Médio / Litro</div>
            <div class="kpi-valor">{fmt_brl(kpis['preco_medio'])}</div>
        </div>
        """, unsafe_allow_html=True)

    # Linha separadora após os KPIs
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
