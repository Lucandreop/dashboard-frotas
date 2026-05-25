"""
Componente do ranking Top 3 de eficiência por categoria.
"""

import math
import streamlit as st
from typing import Dict, List
from core.metrics import fmt_num, METAS_CATEGORIA
from ui.theme import COR_AZUL_PRIMARIO, COR_VERDE_OK, COR_VERMELHO_RUIM, COR_CINZA_FUNDO


# Emoji de medalha conforme posição no ranking
MEDALHAS = {1: "🥇", 2: "🥈", 3: "🥉"}

# Informações de cada categoria para o cabeçalho do podium.
# Os valores de 'meta' vêm de METAS_CATEGORIA (fonte única de verdade).
INFO_CATEGORIAS = {
    'Leve':        {'meta': METAS_CATEGORIA['Leve'],        'emoji': '🚐', 'tipos': 'Furgões'},
    'Média':       {'meta': METAS_CATEGORIA['Média'],       'emoji': '🛻', 'tipos': 'Caminhonetes 3/4'},
    'Pesada Leve': {'meta': METAS_CATEGORIA['Pesada Leve'], 'emoji': '🚚', 'tipos': 'Toco / Microônibus'},
    'Pesada':      {'meta': METAS_CATEGORIA['Pesada'],      'emoji': '🚛', 'tipos': 'Cavalo / Truck'},
}


def renderizar_ranking(ranking: Dict[str, List[Dict]]) -> None:
    """
    Exibe o podium Top 3 por categoria de meta lado a lado.

    ranking: dicionário retornado por metrics.ranking_top3()
    Cada chave é uma categoria; o valor é lista de dicts com os dados.
    """
    st.subheader("🏆 Ranking de Eficiência — Top 3 por Categoria")

    colunas = st.columns(4)

    for col, (categoria, info) in zip(colunas, INFO_CATEGORIAS.items()):
        with col:
            # Cabeçalho da coluna de categoria
            st.markdown(f"""
            <div style="background: {COR_AZUL_PRIMARIO}; color: white;
                        padding: 10px 12px; border-radius: 8px;
                        text-align: center; margin-bottom: 10px;">
                <div style="font-size: 22px;">{info['emoji']}</div>
                <div style="font-size: 14px; font-weight: 800; letter-spacing: 0.5px;">
                    {categoria}
                </div>
                <div style="font-size: 11px; opacity: 0.75; margin-top: 2px;">
                    Meta: {info['meta']} km/L
                </div>
                <div style="font-size: 10px; opacity: 0.6;">
                    {info['tipos']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Lista os 3 primeiros
            top3 = ranking.get(categoria, [])

            if not top3:
                st.markdown(
                    f"<div style='color: #6B6B6B; font-size: 13px; text-align: center; "
                    f"padding: 20px 0;'>Sem dados suficientes</div>",
                    unsafe_allow_html=True
                )
                continue

            for entrada in top3:
                medalha = MEDALHAS.get(entrada['posicao'], "")
                media_fmt = fmt_num(entrada['media_kml'], 2)
                meta = entrada.get('meta')

                # Cor da borda: verde se atingiu a meta, vermelho se ficou abaixo
                if meta and not (isinstance(meta, float) and math.isnan(meta)):
                    acima = entrada['media_kml'] >= meta
                    cor_borda = COR_VERDE_OK if acima else COR_VERMELHO_RUIM
                    icone_status = "✅" if acima else "⚠️"
                else:
                    cor_borda = COR_AZUL_PRIMARIO
                    icone_status = ""

                tipo_txt = str(entrada.get('tipo', '')).strip()
                tipo_html = f"<div style='font-size:10px; color:#6B6B6B;'>{tipo_txt}</div>" if tipo_txt else ""

                st.markdown(f"""
                <div style="border-left: 4px solid {cor_borda};
                            background: {COR_CINZA_FUNDO};
                            padding: 8px 12px; border-radius: 6px;
                            margin-bottom: 8px;">
                    <div style="font-size: 13px; font-weight: 600;">
                        {medalha} {entrada['placa']}
                    </div>
                    <div style="font-size: 19px; font-weight: 800;
                                color: {COR_AZUL_PRIMARIO}; line-height: 1.2;">
                        {media_fmt} <span style="font-size:12px;">km/L</span>
                        <span style="font-size:14px;">{icone_status}</span>
                    </div>
                    {tipo_html}
                </div>
                """, unsafe_allow_html=True)
