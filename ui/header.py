"""
Componente do cabeçalho do dashboard TNORTE.
"""

import streamlit as st
from ui.theme import COR_VERMELHO


def renderizar_header(periodo: str, n_abast: int, n_placas: int) -> None:
    """
    Exibe o cabeçalho com logo TNORTE, título, período e totalizador.

    periodo : string como 'Abril/2026'
    n_abast : número de abastecimentos carregados (após filtros)
    n_placas: número de placas únicas (após filtros)
    """
    st.markdown(f"""
    <div class="tnorte-header">
        <div style="display: flex; justify-content: space-between;
                    align-items: center; flex-wrap: wrap; gap: 12px;">
            <!-- Lado esquerdo: logo e slogan -->
            <div>
                <div style="font-size: 36px; font-weight: 900; letter-spacing: 3px;">
                    T<span style="color: {COR_VERMELHO};">NORTE</span>
                </div>
                <div style="font-size: 10px; opacity: 0.65; letter-spacing: 2.5px; margin-top: 2px;">
                    Controle e Análise de Abastecimentos
                </div>
            </div>
            <!-- Lado direito: título e resumo -->
            <div style="text-align: right;">
                <div style="font-size: 19px; font-weight: 700; margin-bottom: 4px;">
                    Gestão de Frota — Resultados Mensais
                </div>
                <div style="font-size: 13px; opacity: 0.80;">
                    📅 Período: <strong>{periodo}</strong>
                    &nbsp;|&nbsp;
                    ⛽ {n_abast:,} abastecimentos
                    &nbsp;|&nbsp;
                    🚛 {n_placas} placas
                </div>
            </div>
        </div>
    </div>
    <div style="height: 4px; background: {COR_VERMELHO};
                border-radius: 2px; margin-bottom: 20px;"></div>
    """, unsafe_allow_html=True)
