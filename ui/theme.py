"""
Identidade visual da TNORTE: cores, fontes e CSS injetado no Streamlit.
Centralizar aqui facilita ajustes futuros — basta mudar neste arquivo.
"""

import streamlit as st

# ─── PALETA DE CORES TNORTE ───────────────────────────────────────────────────
COR_AZUL_PRIMARIO  = "#1E295C"   # azul marinho — cor principal da marca
COR_VERMELHO       = "#C81D25"   # vermelho — destaque, alertas, KPIs críticos
COR_CINZA_FUNDO    = "#F5F5F7"   # cinza claro — fundos de cards secundários
COR_VERDE_OK       = "#2E7D32"   # verde — placa acima da meta
COR_VERMELHO_RUIM  = "#C81D25"   # vermelho — placa abaixo da meta
COR_TEXTO_PRINCIPAL= "#1A1A1A"   # quase-preto — texto principal
COR_TEXTO_SEC      = "#6B6B6B"   # cinza médio — legendas e textos secundários
COR_AZUL_CLARO     = "#4A7BC9"   # azul médio — gráficos de km
COR_VERMELHO_CLARO = "#CC4E5C"   # vermelho suave — gráficos de valor


def injetar_css() -> None:
    """
    Injeta CSS personalizado para aplicar a identidade TNORTE ao Streamlit.

    st.markdown com unsafe_allow_html=True renderiza HTML/CSS real.
    Usamos isso apenas para estilizar elementos que o Streamlit não expõe
    diretamente (como cards e badges personalizados).
    """
    css = f"""
    <style>
        /* Fonte Calibri com fallback para o sans-serif do sistema */
        html, body, [class*="css"] {{
            font-family: 'Calibri', 'Segoe UI', 'Arial', sans-serif;
        }}

        /* Remove padding excessivo do topo da página */
        .block-container {{
            padding-top: 1rem;
        }}

        /* ── Cards de KPI ── */
        .kpi-card {{
            background-color: {COR_AZUL_PRIMARIO};
            color: white;
            padding: 22px 18px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .kpi-label {{
            font-size: 12px;
            color: rgba(255,255,255,0.75);
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        .kpi-valor {{
            font-size: 26px;
            font-weight: 800;
            color: white;
            line-height: 1.1;
        }}

        /* ── Header TNORTE ── */
        .tnorte-header {{
            background: linear-gradient(135deg, {COR_AZUL_PRIMARIO} 0%, #2d3f80 100%);
            padding: 22px 30px;
            border-radius: 10px;
            margin-bottom: 6px;
            color: white;
        }}

        /* ── Card de posto (análise de rede) ── */
        .posto-card {{
            border-radius: 8px;
            padding: 16px;
            text-align: center;
            background: {COR_CINZA_FUNDO};
            margin-bottom: 8px;
        }}

        /* ── Tags de status meta ── */
        .badge-ok {{
            background-color: {COR_VERDE_OK};
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            display: inline-block;
        }}
        .badge-ruim {{
            background-color: {COR_VERMELHO_RUIM};
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            display: inline-block;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
