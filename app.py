"""
Dashboard TNORTE — Gestão de Combustível da Frota v2
Ponto de entrada da aplicação Streamlit.

Como rodar:
    streamlit run app.py
"""

import io
import streamlit as st
import pandas as pd

# set_page_config DEVE ser a PRIMEIRA chamada Streamlit do script
st.set_page_config(
    page_title="TNORTE — Gestão de Frota",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.data_loader import (
    carregar_planilha, detectar_periodo, listar_meses_disponiveis
)
from core.metrics import (
    calcular_kpis_gerais, agregar_por_placa, calcular_custo_por_posto,
    ranking_top3, consolidado_mensal, arla_por_placa, pedagio_por_placa,
    melhor_media_por_tipo, fmt_brl, fmt_num, METAS_CATEGORIA
)
from core.filters import aplicar_filtros
from ui.theme import injetar_css, COR_AZUL_PRIMARIO, COR_VERDE_OK, COR_VERMELHO_RUIM
from ui.header import renderizar_header
from ui.kpis import renderizar_kpis
from ui.ranking import renderizar_ranking
from ui.charts import (
    grafico_km_por_placa, grafico_valor_por_placa,
    grafico_eficiencia_por_placa, grafico_custo_por_posto,
    grafico_evolucao_placa,
    grafico_consolidado_litros, grafico_consolidado_km,
    grafico_consolidado_custos, grafico_consolidado_media,
    grafico_arla_por_placa, grafico_pedagio_por_placa,
)
from export.pptx_export import gerar_pptx, PPTX_DISPONIVEL

injetar_css()

_CFG_PLOTLY = {
    'displaylogo': False,
    'toImageButtonOptions': {'format': 'png', 'scale': 2},
    'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
}


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

def renderizar_sidebar(df: pd.DataFrame):
    """
    Renderiza filtros na barra lateral.
    Retorna: categorias, tipos, postos, placas, mes_selecionado.
    """
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding: 8px 0 18px 0;">
            <span style="font-size:26px; font-weight:900; color:{COR_AZUL_PRIMARIO};">T</span><span
                  style="font-size:26px; font-weight:900; color:#C81D25;">NORTE</span>
            <div style="font-size:9px; color:#6B6B6B; letter-spacing:2px; margin-top:2px;">
                GESTÃO DE FROTA
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🗓️ Período")

        # Seletor de mês — aparece quando a planilha tem mais de 1 mês
        meses_disponiveis = listar_meses_disponiveis(df)
        opcoes_mes = ['Ano inteiro'] + meses_disponiveis

        mes_anterior = st.session_state.get('mes_anterior', opcoes_mes[0])
        mes_sel = st.selectbox(
            "Mês de análise",
            options=opcoes_mes,
            index=0,
            help="'Ano inteiro' agrega todos os meses. Selecione um mês para filtrar as seções mensais."
        )

        # Ao trocar o mês, reseta os filtros para evitar seleções inválidas
        if mes_sel != mes_anterior:
            st.session_state.mes_anterior = mes_sel
            st.session_state.reset_counter += 1
            st.rerun()

        st.markdown("### 🔍 Filtros")

        if 'reset_counter' not in st.session_state:
            st.session_state.reset_counter = 0
        k = st.session_state.reset_counter

        # Opções dos filtros vêm do mês selecionado, não do ano inteiro.
        # Assim, se Janeiro está selecionado, só aparecem placas/postos de Janeiro.
        df_base = df if mes_sel == 'Ano inteiro' else df[df['mes_nome'] == mes_sel]

        cats_disp   = sorted(df_base['Categoria'].dropna().unique().tolist())
        tipos_disp  = sorted(df_base['Tipo/Modelo'].dropna().unique().tolist())
        postos_disp = sorted(df_base['Posto'].dropna().unique().tolist())
        placas_disp = sorted(df_base['Placa'].unique().tolist())

        cats_sel = st.multiselect(
            "Categoria de Meta", options=cats_disp, default=[],
            key=f"cat_{k}", help="Leve / Média / Pesada Leve / Pesada / Sem Meta"
        )
        tipos_sel = st.multiselect(
            "Tipo de Veículo", options=tipos_disp, default=[], key=f"tipo_{k}"
        )
        postos_sel = st.multiselect(
            "Posto / Rede", options=postos_disp, default=[], key=f"posto_{k}"
        )
        placas_sel = st.multiselect(
            "Placa", options=placas_disp, default=[], key=f"placa_{k}"
        )

        if st.button("🔄 Limpar Filtros", use_container_width=True):
            st.session_state.reset_counter += 1
            st.rerun()

        # Aplica filtros SEM o filtro de mês para contar o total do período
        df_pre = aplicar_filtros(df, cats_sel, tipos_sel, postos_sel, placas_sel)
        df_mes = aplicar_filtros(df, cats_sel, tipos_sel, postos_sel, placas_sel, mes_sel)
        n_filtrado = len(df_mes[df_mes['TipoProduto'] == 'COMBUSTIVEL'])
        total = len(df_pre[df_pre['TipoProduto'] == 'COMBUSTIVEL'])
        pct = n_filtrado / total * 100 if total > 0 else 0
        st.caption(f"📋 {n_filtrado}/{total} abastecimentos de combustível ({pct:.0f}%)")

    return cats_sel, tipos_sel, postos_sel, placas_sel, mes_sel


# ─── SEÇÃO: CUSTO POR POSTO ───────────────────────────────────────────────────

def renderizar_analise_postos(df: pd.DataFrame) -> None:
    """Cards de preço médio ponderado por posto + gráfico comparativo."""
    st.subheader("⛽ Análise de Custo por Rede (Combustível)")

    agg = calcular_custo_por_posto(df)

    if agg.empty:
        st.info("Sem dados de posto para a seleção atual.")
        return

    idx_min = int(agg['PrecoMedio'].idxmin())
    idx_max = int(agg['PrecoMedio'].idxmax())

    cols = st.columns(len(agg))
    for col, (idx, row) in zip(cols, agg.iterrows()):
        if idx == idx_min:
            badge, cor = "🟢 Mais econômico", COR_VERDE_OK
        elif idx == idx_max:
            badge, cor = "🔴 Mais caro", COR_VERMELHO_RUIM
        else:
            badge, cor = "", "#4A7BC9"

        with col:
            st.markdown(f"""
            <div style="border: 2px solid {cor}; border-radius: 10px;
                        padding: 16px 10px; text-align: center; background: #F9F9F9;">
                <div style="font-size:13px; font-weight:700; color:{COR_AZUL_PRIMARIO};
                            margin-bottom:6px;">{row['Posto']}</div>
                <div style="font-size:30px; font-weight:800; color:{cor}; line-height:1.1;">
                    {fmt_brl(row['PrecoMedio'])}
                </div>
                <div style="font-size:11px; color:#6B6B6B; margin-top:4px;">/litro</div>
                <div style="font-size:11px; color:#6B6B6B; margin-top:8px;">
                    {fmt_num(row['TotalLitros'], 0)} L comprados<br>
                    {row['QtdAbastecimentos']} abastecimentos
                </div>
                {f'<div style="margin-top:10px; font-size:11px; font-weight:bold; color:{cor};">{badge}</div>' if badge else ''}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.plotly_chart(grafico_custo_por_posto(agg), use_container_width=True, config=_CFG_PLOTLY)


# ─── SEÇÃO: CONSOLIDADO MENSAL ────────────────────────────────────────────────

def renderizar_consolidado_mensal(df: pd.DataFrame) -> None:
    """
    Tabela jan-dez com as 3 contas + 4 gráficos de evolução mensal.
    Esta seção usa TODOS os meses do DataFrame — ignora o filtro de mês.
    """
    st.subheader("🗓️ Consolidado Anual (Jan a Dez)")
    st.caption("Esta seção sempre mostra todos os meses disponíveis, independente do filtro de mês.")

    df_cons = consolidado_mensal(df)

    # Tabela resumo com apenas os meses que têm dados
    df_exib = df_cons[
        (df_cons['R_Comb'] > 0) | (df_cons['R_Arla'] > 0) | (df_cons['R_Pedagio'] > 0)
    ].copy()

    if df_exib.empty:
        st.info("Sem dados para o consolidado.")
        return

    # Formata para exibição
    df_tabela = pd.DataFrame({
        'Mês':           df_exib['mes_nome'],
        'Litros Diesel': df_exib['Litros'].apply(lambda v: fmt_num(v, 0) + ' L'),
        'Km Rodado':     df_exib['Km'].apply(lambda v: fmt_num(v, 0) + ' km'),
        'R$ Combustível': df_exib['R_Comb'].apply(fmt_brl),
        'R$ ARLA':        df_exib['R_Arla'].apply(fmt_brl),
        'R$ Pedágio':     df_exib['R_Pedagio'].apply(fmt_brl),
        'Média km/L':    df_exib['MediaKmL'].apply(lambda v: fmt_num(v, 2) if v > 0 else '—'),
    })

    # Linha de totais
    totais = {
        'Mês': '**TOTAL**',
        'Litros Diesel': fmt_num(df_exib['Litros'].sum(), 0) + ' L',
        'Km Rodado':     fmt_num(df_exib['Km'].sum(), 0) + ' km',
        'R$ Combustível': fmt_brl(df_exib['R_Comb'].sum()),
        'R$ ARLA':        fmt_brl(df_exib['R_Arla'].sum()),
        'R$ Pedágio':     fmt_brl(df_exib['R_Pedagio'].sum()),
        'Média km/L': fmt_num(
            df_exib['Km'].sum() / df_exib['LitrosValidos'].sum(), 2
        ) if df_exib['LitrosValidos'].sum() > 0 else '—',
    }
    df_tabela = pd.concat(
        [df_tabela, pd.DataFrame([totais])], ignore_index=True
    )

    st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # 4 gráficos de evolução mensal em 2x2
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(grafico_consolidado_litros(df_cons), use_container_width=True, config=_CFG_PLOTLY)
    with col2:
        st.plotly_chart(grafico_consolidado_km(df_cons), use_container_width=True, config=_CFG_PLOTLY)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(grafico_consolidado_custos(df_cons), use_container_width=True, config=_CFG_PLOTLY)
    with col4:
        st.plotly_chart(grafico_consolidado_media(df_cons), use_container_width=True, config=_CFG_PLOTLY)


# ─── SEÇÃO: MELHOR MÉDIA POR TIPO ────────────────────────────────────────────

def renderizar_melhor_media_por_tipo(df: pd.DataFrame, periodo_label: str) -> None:
    """
    Quadro de campeões de km/L por tipo de veículo no período selecionado.
    """
    st.subheader(f"🏆 Melhor Média km/L por Tipo de Veículo — {periodo_label}")

    df_melhores = melhor_media_por_tipo(df)

    if df_melhores.empty:
        st.info("Sem dados de eficiência para exibir.")
        return

    # Exibe como cards lado a lado (até 4 por linha)
    n = len(df_melhores)
    colunas_por_linha = min(n, 4)
    cols = st.columns(colunas_por_linha)

    for i, (_, row) in enumerate(df_melhores.iterrows()):
        col_idx = i % colunas_por_linha
        meta_str = fmt_num(float(row['Meta']), 1) if pd.notna(row['Meta']) and row['Meta'] != '' else '—'
        status = row['Status']
        cor_status = COR_VERDE_OK if '✅' in status else ('#C81D25' if '❌' in status else '#999')

        with cols[col_idx]:
            st.markdown(f"""
            <div style="border: 2px solid {cor_status}; border-radius: 10px;
                        padding: 14px 10px; text-align: center; background: #F9F9F9; margin-bottom:8px;">
                <div style="font-size:12px; color:#6B6B6B; margin-bottom:4px;">{row['Tipo']}</div>
                <div style="font-size:17px; font-weight:800; color:{COR_AZUL_PRIMARIO};">{row['Placa']}</div>
                <div style="font-size:26px; font-weight:800; color:{cor_status}; line-height:1.2;">
                    {fmt_num(row['MediaKmL'], 2)} km/L
                </div>
                <div style="font-size:11px; color:#6B6B6B; margin-top:4px;">Meta: {meta_str} km/L</div>
                <div style="font-size:12px; font-weight:700; color:{cor_status}; margin-top:6px;">{status}</div>
            </div>
            """, unsafe_allow_html=True)


# ─── SEÇÃO: ARLA 32 ──────────────────────────────────────────────────────────

def renderizar_arla(df_mes: pd.DataFrame, df_total: pd.DataFrame) -> None:
    """
    Seção de ARLA 32: gasto por placa (mês filtrado) + evolução mensal.
    """
    st.subheader("🧪 ARLA 32")

    col_tab, col_graf = st.columns([1, 2])

    with col_tab:
        df_a = arla_por_placa(df_mes)
        if df_a.empty:
            st.info("Sem ARLA no período selecionado.")
        else:
            df_exib = df_a.copy()
            df_exib['LitrosArla'] = df_exib['LitrosArla'].apply(lambda v: fmt_num(v, 2) + ' L')
            df_exib['ValorArla']  = df_exib['ValorArla'].apply(fmt_brl)
            df_exib.columns = ['Placa', 'Litros ARLA', 'R$ ARLA']
            st.dataframe(df_exib, use_container_width=True, hide_index=True)

    with col_graf:
        df_a_graf = arla_por_placa(df_mes)
        st.plotly_chart(grafico_arla_por_placa(df_a_graf), use_container_width=True, config=_CFG_PLOTLY)

    # Evolução mensal de ARLA (usa df_total — todos os meses)
    df_cons = consolidado_mensal(df_total)
    df_arla_mensal = df_cons[df_cons['R_Arla'] > 0]

    if len(df_arla_mensal) > 1:
        st.markdown("**Evolução mensal de ARLA:**")
        import plotly.graph_objects as go
        from ui.theme import COR_AZUL_PRIMARIO
        from core.metrics import ORDEM_MESES

        fig = go.Figure(go.Bar(
            x=df_arla_mensal['mes_nome'],
            y=df_arla_mensal['R_Arla'],
            marker_color='#2ECC71',
            text=[fmt_brl(v) for v in df_arla_mensal['R_Arla']],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>',
        ))
        fig.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(categoryorder='array', categoryarray=ORDEM_MESES),
            yaxis=dict(showgrid=True, gridcolor='#EEEEEE', showticklabels=False),
            height=260,
        )
        st.plotly_chart(fig, use_container_width=True, config=_CFG_PLOTLY)


# ─── SEÇÃO: PEDÁGIO ──────────────────────────────────────────────────────────

def renderizar_pedagio(df_mes: pd.DataFrame, df_total: pd.DataFrame) -> None:
    """
    Seção de Pedágio: gasto por placa (mês filtrado) + evolução mensal.
    """
    st.subheader("🛣️ Pedágio")

    col_tab, col_graf = st.columns([1, 2])

    with col_tab:
        df_p = pedagio_por_placa(df_mes)
        if df_p.empty:
            st.info("Sem pedágio no período selecionado.")
        else:
            df_exib = df_p.copy()
            df_exib['Passagens']    = df_exib['Passagens'].apply(lambda v: fmt_num(v, 0))
            df_exib['ValorPedagio'] = df_exib['ValorPedagio'].apply(fmt_brl)
            df_exib.columns = ['Placa', 'Passagens', 'R$ Pedágio']
            st.dataframe(df_exib, use_container_width=True, hide_index=True)

    with col_graf:
        df_p_graf = pedagio_por_placa(df_mes)
        st.plotly_chart(grafico_pedagio_por_placa(df_p_graf), use_container_width=True, config=_CFG_PLOTLY)

    # Evolução mensal de pedágio (usa df_total — todos os meses)
    df_cons = consolidado_mensal(df_total)
    df_ped_mensal = df_cons[df_cons['R_Pedagio'] > 0]

    if len(df_ped_mensal) > 1:
        st.markdown("**Evolução mensal de Pedágio:**")
        import plotly.graph_objects as go
        from ui.theme import COR_VERMELHO
        from core.metrics import ORDEM_MESES

        fig = go.Figure(go.Bar(
            x=df_ped_mensal['mes_nome'],
            y=df_ped_mensal['R_Pedagio'],
            marker_color=COR_VERMELHO,
            text=[fmt_brl(v) for v in df_ped_mensal['R_Pedagio']],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>',
        ))
        fig.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(categoryorder='array', categoryarray=ORDEM_MESES),
            yaxis=dict(showgrid=True, gridcolor='#EEEEEE', showticklabels=False),
            height=260,
        )
        st.plotly_chart(fig, use_container_width=True, config=_CFG_PLOTLY)


# ─── SEÇÃO: ANÁLISE POR CATEGORIA ─────────────────────────────────────────────

def renderizar_analise_categorias(df_placas: pd.DataFrame) -> None:
    """4 abas (uma por categoria) com 3 gráficos lado a lado."""
    st.subheader("📈 Análise por Categoria de Veículo")

    abas = st.tabs(list(METAS_CATEGORIA.keys()))

    for aba, (categoria, meta) in zip(abas, METAS_CATEGORIA.items()):
        with aba:
            df_cat = df_placas[df_placas['Categoria'] == categoria]

            if df_cat.empty:
                st.info(f"Nenhuma placa na categoria '{categoria}' com os filtros atuais.")
                continue

            c1, c2, c3 = st.columns(3)

            cfg = dict(_CFG_PLOTLY)
            cfg['toImageButtonOptions'] = {
                'format': 'png', 'scale': 2,
                'filename': f'tnorte_{categoria.lower().replace(" ", "_")}'
            }

            with c1:
                st.plotly_chart(grafico_km_por_placa(df_cat), use_container_width=True, config=cfg)
            with c2:
                st.plotly_chart(grafico_valor_por_placa(df_cat), use_container_width=True, config=cfg)
            with c3:
                st.plotly_chart(grafico_eficiencia_por_placa(df_cat, meta), use_container_width=True, config=cfg)


# ─── SEÇÃO: TABELA DETALHADA ──────────────────────────────────────────────────

def renderizar_tabela(df_placas: pd.DataFrame) -> None:
    """Tabela expansível com resumo por placa e status vs. meta."""
    with st.expander("📋 Ver detalhamento por placa (combustível)", expanded=False):
        df_exib = df_placas[[
            'Placa', 'Tipo', 'Categoria', 'MetaNum',
            'TotalLitros', 'TotalValor', 'TotalKm', 'MediaKmL',
        ]].copy()

        def status(row):
            if pd.isna(row['MetaNum']):
                return "—"
            return "✅ Acima" if row['MediaKmL'] >= row['MetaNum'] else "❌ Abaixo"

        df_exib['Status'] = df_exib.apply(status, axis=1)
        df_exib['MediaKmL']    = df_exib['MediaKmL'].round(2)
        df_exib['TotalLitros'] = df_exib['TotalLitros'].round(2)
        df_exib['TotalValor']  = df_exib['TotalValor'].round(2)

        df_exib.columns = [
            'Placa', 'Tipo', 'Categoria', 'Meta (km/L)',
            'Litros', 'Valor (R$)', 'Km Total', 'Média km/L', 'Status'
        ]

        st.dataframe(
            df_exib.sort_values('Km Total', ascending=False),
            use_container_width=True, hide_index=True,
        )


# ─── SEÇÃO: DRILL-DOWN POR PLACA ──────────────────────────────────────────────

def renderizar_drilldown(df: pd.DataFrame) -> None:
    """Seleciona uma placa e exibe seu histórico de combustível."""
    st.subheader("🔎 Análise Individual por Placa")

    # Só mostra placas com abastecimento de combustível
    df_comb = df[df['TipoProduto'] == 'COMBUSTIVEL']
    placas = sorted(df_comb['Placa'].unique().tolist())

    if not placas:
        st.info("Sem dados de combustível para as placas nesta seleção.")
        return

    placa_sel = st.selectbox("Selecione a placa:", options=placas, key="drilldown_placa")

    if not placa_sel:
        return

    df_p = df_comb[df_comb['Placa'] == placa_sel]

    col_info, col_graf = st.columns([1, 2])

    with col_info:
        def moda_col(col):
            s = df_p[col].dropna()
            return s.mode().iloc[0] if not s.empty else "—"

        meta_val = df_p['MetaNum'].dropna()
        meta_str = f"{fmt_num(float(meta_val.iloc[0]), 1)} km/L" if not meta_val.empty else "Sem meta definida"

        df_p_val = df_p[df_p['km_valido'] == True]
        if not df_p_val.empty and df_p_val['Qtde'].sum() > 0:
            media_real = df_p_val['Km Perc.'].sum() / df_p_val['Qtde'].sum()
            media_str = f"{fmt_num(media_real, 2)} km/L"
        else:
            media_str = "Sem km válido"

        campos = [
            f"**Placa:** {placa_sel}",
            f"**Tipo:** {moda_col('Tipo/Modelo')}",
            f"**Categoria:** {df_p['Categoria'].iloc[0]}",
            f"**Meta:** {meta_str}",
            f"**Abastecimentos:** {len(df_p)}",
            f"**Eficiência real:** {media_str}",
            f"**Total abastecido:** {fmt_num(df_p['Qtde'].sum(), 2)} L",
            f"**Total gasto:** {fmt_brl(df_p['Valor.total'].sum())}",
        ]
        st.markdown("\n\n".join(campos))

    with col_graf:
        st.plotly_chart(
            grafico_evolucao_placa(df_p, placa_sel),
            use_container_width=True, config=_CFG_PLOTLY
        )

    with st.expander("Ver todos os abastecimentos desta placa"):
        colunas_exib = ['Data Abast', 'Posto', 'Produto', 'Qtde',
                        'Vlr. litro', 'Valor.total', 'Km Perc.', 'Média', 'km_valido']
        st.dataframe(
            df_p[colunas_exib].sort_values('Data Abast'),
            use_container_width=True, hide_index=True,
        )


# ─── SEÇÃO: EXPORTAÇÃO ────────────────────────────────────────────────────────

def renderizar_exportacao(kpis: dict, df_placas: pd.DataFrame,
                          df: pd.DataFrame, periodo: str) -> None:
    """Botões para baixar PPTX, Excel processado e CSV."""
    st.subheader("📤 Exportar Dados")

    col1, col2, col3 = st.columns(3)

    with col1:
        if PPTX_DISPONIVEL:
            dados_pptx = gerar_pptx(kpis, df_placas, periodo)
            if dados_pptx:
                st.download_button(
                    label="📊 Baixar Apresentação PPTX",
                    data=dados_pptx,
                    file_name=f"TNORTE_Frota_{periodo.replace('/', '_')}.pptx",
                    mime="application/vnd.openxmlformats-officedocument"
                         ".presentationml.presentation",
                    use_container_width=True,
                )
        else:
            st.info("Instale python-pptx para habilitar o export PPTX.")

    with col2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Abastecimentos', index=False)
            df_placas.to_excel(writer, sheet_name='Resumo_por_Placa', index=False)
        buf.seek(0)

        st.download_button(
            label="📥 Baixar Excel Processado",
            data=buf.getvalue(),
            file_name=f"TNORTE_Processado_{periodo.replace('/', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col3:
        csv = df_placas.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig')
        st.download_button(
            label="📄 Baixar CSV Resumo",
            data=csv.encode('utf-8-sig'),
            file_name=f"TNORTE_Resumo_{periodo.replace('/', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ─── TELA INICIAL ────────────────────────────────────────────────────────────

def renderizar_tela_inicial() -> None:
    """Tela de boas-vindas antes do upload."""
    st.markdown("""
    <div style="text-align:center; padding: 50px 20px 30px 20px;">
        <div style="font-size: 64px; margin-bottom: 16px;">🚛</div>
        <h1 style="color: #1E295C; font-size: 30px; margin-bottom: 8px;">
            TNORTE — Gestão de Frota v2
        </h1>
        <p style="color: #6B6B6B; font-size: 15px; max-width: 560px; margin: 0 auto 24px auto;">
            Faça upload da planilha de abastecimentos para visualizar KPIs,
            consolidado anual e análise separada de Combustível, ARLA e Pedágio.
        </p>
        <p style="color: #C81D25; font-size: 13px;">
            ⬆️ Clique em <strong>Browse files</strong> para carregar um ou vários .xlsx de uma vez
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("ℹ️ Como usar o dashboard"):
        st.markdown("""
        1. **Carregue uma ou várias planilhas** `.xlsx` de uma vez (ex: Janeiro, Fevereiro, Março)
        2. O dashboard **empilha os meses automaticamente** e detecta o período
        3. Use o **seletor de mês** na sidebar para filtrar as seções mensais
        4. O **Consolidado Anual** sempre mostra todos os meses carregados
        5. **3 contas separadas**: Combustível | ARLA 32 | Pedágio — nunca misturadas
        6. **Km/L calculado apenas sobre diesel** — ARLA e Pedágio não entram

        **Formatos aceitos:** planilha com colunas `Coluna1` (tipo) ou `Tipo/Modelo`,
        `Posto` ou `Histórico/estabelecimento`.
        """)


# ─── FUNÇÃO PRINCIPAL ─────────────────────────────────────────────────────────

def main() -> None:
    """Controla o fluxo completo: upload → filtros → visualizações → exportação."""
    arquivos = st.file_uploader(
        "📁 Carregar planilha(s) de abastecimentos (.xlsx)",
        type=['xlsx'],
        accept_multiple_files=True,
        help="Selecione um ou vários arquivos mensais — o dashboard empilha e consolida automaticamente."
    )

    if not arquivos:
        renderizar_tela_inicial()
        return

    # Carrega cada arquivo e empilha num único DataFrame
    dfs = []
    erros = []
    for arq in arquivos:
        try:
            dfs.append(carregar_planilha(arq))
        except ValueError as e:
            erros.append(f"**{arq.name}:** {e}")

    if erros:
        for msg in erros:
            st.error(f"❌ {msg}")
        if not dfs:
            return

    if not dfs:
        renderizar_tela_inicial()
        return

    # pd.concat empilha os meses; reset_index evita índices duplicados
    df = pd.concat(dfs, ignore_index=True)

    periodo = detectar_periodo(df)
    n_comb = len(df[df['TipoProduto'] == 'COMBUSTIVEL'])
    n_arquivos = len(dfs)

    # Detalha quantas linhas cada arquivo contribuiu para facilitar diagnóstico
    detalhes = " | ".join(
        f"{arq.name}: {len(d)} linhas"
        for arq, d in zip(arquivos[:len(dfs)], dfs)
    )
    st.success(f"✅ {n_arquivos} arquivo(s) carregado(s) — {len(df)} lançamentos ({n_comb} combustível) — {periodo}")
    st.caption(f"📂 {detalhes}")

    # Sidebar: retorna filtros + mês selecionado
    cats, tipos, postos, placas, mes_sel = renderizar_sidebar(df)

    # df_f: dados filtrados pelo mês + outros filtros (usado nas seções mensais)
    df_f = aplicar_filtros(df, cats, tipos, postos, placas, mes_sel)
    # df_ano: dados do ano inteiro (sem filtro de mês — para consolidado e evoluções)
    df_ano = aplicar_filtros(df, cats, tipos, postos, placas)

    if df_f.empty:
        st.warning("⚠️ Nenhum registro com os filtros atuais.")
        return

    # Label do período exibido nas seções mensais
    periodo_label = mes_sel if mes_sel != 'Ano inteiro' else periodo

    # Métricas sobre o período filtrado (mês ou ano inteiro)
    kpis      = calcular_kpis_gerais(df_f)
    df_placas = agregar_por_placa(df_f)
    ranking   = ranking_top3(df_placas)

    # ── Renderiza seções ────────────────────────────────────────────────────
    renderizar_header(periodo_label, kpis['n_abastecimentos'], kpis['n_placas'])

    renderizar_kpis(kpis)

    st.markdown("---")

    renderizar_consolidado_mensal(df_ano)

    st.markdown("---")

    renderizar_melhor_media_por_tipo(df_f, periodo_label)

    st.markdown("---")

    renderizar_analise_postos(df_f)

    st.markdown("---")

    renderizar_ranking(ranking)

    st.markdown("---")

    renderizar_analise_categorias(df_placas)

    st.markdown("---")

    renderizar_arla(df_f, df_ano)

    st.markdown("---")

    renderizar_pedagio(df_f, df_ano)

    st.markdown("---")

    renderizar_tabela(df_placas)

    st.markdown("---")

    renderizar_drilldown(df_f)

    st.markdown("---")

    renderizar_exportacao(kpis, df_placas, df_f, periodo_label)


main()
