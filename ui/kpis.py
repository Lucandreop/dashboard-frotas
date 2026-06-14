"""
Cards de KPI do topo do dashboard.
v2: 6 cards em 2 linhas, representando as 3 contas separadas.
"""

import streamlit as st
from core.metrics import fmt_brl, fmt_num


def renderizar_kpis(kpis: dict) -> None:
    """
    Exibe 6 cards de KPI em 2 linhas de 3 colunas cada.

    Linha 1 — Combustível: litros | R$ | km rodado
    Linha 2 — Eficiência + outras contas: km/L | R$ ARLA | R$ Pedágio
    """
    # --- Linha 1: conta de combustível ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">⛽ Litros de Diesel/Combustível</div>
            <div class="kpi-valor">{fmt_num(kpis['total_litros'], 2)} L</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">💰 R$ Combustível</div>
            <div class="kpi-valor">{fmt_brl(kpis['total_valor_comb'])}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">📍 Km Rodado (válido)</div>
            <div class="kpi-valor">{fmt_num(kpis['total_km'])} km</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # --- Linha 2: eficiência, ARLA e pedágio ---
    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🏎️ Média km/L (diesel)</div>
            <div class="kpi-valor">{fmt_num(kpis['media_kml'], 2)} km/L</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🧪 R$ ARLA 32</div>
            <div class="kpi-valor">{fmt_brl(kpis['total_valor_arla'])}</div>
            <div style="font-size:11px; color:#6B6B6B; margin-top:4px;">
                {fmt_num(kpis['total_litros_arla'], 2)} L
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🛣️ R$ Pedágio</div>
            <div class="kpi-valor">{fmt_brl(kpis['total_valor_pedagio'])}</div>
            <div style="font-size:11px; color:#6B6B6B; margin-top:4px;">
                {fmt_num(kpis['total_passagens_pedagio'])} passagens
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
