"""
Dashboard TNORTE — Gestão de Combustível da Frota
Ponto de entrada da aplicação Streamlit.

Como rodar:
    streamlit run app.py
"""

import io
import streamlit as st
import pandas as pd

# st.set_page_config DEVE ser a PRIMEIRA chamada Streamlit do script
st.set_page_config(
    page_title="TNORTE — Gestão de Frota",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Importa os módulos do projeto (ordem importa: theme antes de header)
from core.data_loader import carregar_planilha, detectar_periodo
from core.metrics import (
    calcular_kpis_gerais, agregar_por_placa, calcular_custo_por_posto,
    ranking_top3, fmt_brl, fmt_num, METAS_CATEGORIA
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
)
from export.pptx_export import gerar_pptx, PPTX_DISPONIVEL

# Aplica o CSS da identidade visual TNORTE
injetar_css()

# Configuração do botão de download de imagem nos gráficos Plotly
# (aparece quando o usuário passa o mouse sobre o gráfico)
_CFG_PLOTLY = {
    'displaylogo': False,
    'toImageButtonOptions': {'format': 'png', 'scale': 2},
    'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
}


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

def renderizar_sidebar(df: pd.DataFrame):
    """
    Renderiza os filtros na barra lateral e retorna os valores selecionados.

    Quando nenhuma opção é selecionada em um filtro, ele não é aplicado
    (equivale a "mostrar tudo").
    """
    with st.sidebar:
        # Mini logo na sidebar
        st.markdown(f"""
        <div style="text-align:center; padding: 8px 0 18px 0;">
            <span style="font-size:26px; font-weight:900; color:{COR_AZUL_PRIMARIO};">T</span><span
                  style="font-size:26px; font-weight:900; color:#C81D25;">NORTE</span>
            <div style="font-size:9px; color:#6B6B6B; letter-spacing:2px; margin-top:2px;">
                GESTÃO DE FROTA
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🔍 Filtros")

        # st.session_state guarda dados entre re-execuções do Streamlit.
        # Usamos um contador para "resetar" os widgets de filtro quando o
        # usuário clica em "Limpar Filtros" — mudar a key força o Streamlit
        # a criar um novo widget com valor padrão (lista vazia).
        if 'reset_counter' not in st.session_state:
            st.session_state.reset_counter = 0
        k = st.session_state.reset_counter  # sufixo das keys dos widgets

        # Listas de opções disponíveis (valores únicos do DataFrame)
        cats_disp = sorted(df['Categoria'].dropna().unique().tolist())
        tipos_disp = sorted(df['Tipo/Modelo'].dropna().unique().tolist())
        postos_disp = sorted(df['Posto'].dropna().unique().tolist())
        placas_disp = sorted(df['Placa'].unique().tolist())
        conds_disp  = sorted(df['Condutor'].dropna().unique().tolist())

        cats_sel = st.multiselect(
            "Categoria de Meta", options=cats_disp, default=[],
            key=f"cat_{k}",
            help="Leve / Média / Pesada Leve / Pesada / Sem Meta"
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
        conds_sel = st.multiselect(
            "Condutor", options=conds_disp, default=[], key=f"cond_{k}"
        )

        if st.button("🔄 Limpar Filtros", use_container_width=True):
            # Incrementar o contador força todos os multiselects a reiniciar
            st.session_state.reset_counter += 1
            st.rerun()

        # Prévia de quantos registros passam pelos filtros ativos
        n_filtrado = len(aplicar_filtros(df, cats_sel, tipos_sel, postos_sel, placas_sel, conds_sel))
        total = len(df)
        pct = n_filtrado / total * 100 if total > 0 else 0
        st.caption(f"📋 {n_filtrado}/{total} abastecimentos ({pct:.0f}%)")

    return cats_sel, tipos_sel, postos_sel, placas_sel, conds_sel


# ─── SEÇÃO: CUSTO POR POSTO ───────────────────────────────────────────────────

def renderizar_analise_postos(df: pd.DataFrame) -> None:
    """Exibe cards de preço médio ponderado por posto e gráfico comparativo."""
    st.subheader("⛽ Análise de Custo por Rede")

    # Usa a função centralizada de metrics.py — evita duplicação de lógica
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
    # Passa o df já agregado para o gráfico — sem recalcular
    st.plotly_chart(grafico_custo_por_posto(agg), use_container_width=True, config=_CFG_PLOTLY)


# ─── SEÇÃO: ANÁLISE POR CATEGORIA ─────────────────────────────────────────────

def renderizar_analise_categorias(df_placas: pd.DataFrame) -> None:
    """
    4 abas (uma por categoria de meta), cada uma com 3 gráficos lado a lado:
    distância, investimento e eficiência.
    """
    st.subheader("📈 Análise por Categoria de Veículo")

    # Metas vêm de METAS_CATEGORIA (fonte única em core/metrics.py)
    abas = st.tabs(list(METAS_CATEGORIA.keys()))

    for aba, (categoria, meta) in zip(abas, METAS_CATEGORIA.items()):
        with aba:
            df_cat = df_placas[df_placas['Categoria'] == categoria]

            if df_cat.empty:
                st.info(f"Nenhuma placa na categoria '{categoria}' com os filtros atuais.")
                continue

            # Três colunas: km | R$ | km/L
            c1, c2, c3 = st.columns(3)

            cfg = dict(_CFG_PLOTLY)
            cfg['toImageButtonOptions'] = {
                'format': 'png', 'scale': 2,
                'filename': f'tnorte_{categoria.lower().replace(" ", "_")}'
            }

            with c1:
                st.plotly_chart(grafico_km_por_placa(df_cat),
                                use_container_width=True, config=cfg)
            with c2:
                st.plotly_chart(grafico_valor_por_placa(df_cat),
                                use_container_width=True, config=cfg)
            with c3:
                st.plotly_chart(grafico_eficiencia_por_placa(df_cat, meta),
                                use_container_width=True, config=cfg)


# ─── SEÇÃO: TABELA DETALHADA ──────────────────────────────────────────────────

def renderizar_tabela(df_placas: pd.DataFrame) -> None:
    """Tabela expansível com resumo por placa e status vs. meta."""
    with st.expander("📋 Ver detalhamento por placa", expanded=False):
        df_exib = df_placas[[
            'Placa', 'Tipo', 'Categoria', 'MetaNum',
            'TotalLitros', 'TotalValor', 'TotalKm', 'MediaKmL',
        ]].copy()

        # Coluna de status: compara a média calculada com a meta
        def status(row):
            if pd.isna(row['MetaNum']):
                return "—"
            return "✅ Acima" if row['MediaKmL'] >= row['MetaNum'] else "❌ Abaixo"

        df_exib['Status'] = df_exib.apply(status, axis=1)

        # Arredonda para leitura mais limpa
        df_exib['MediaKmL']   = df_exib['MediaKmL'].round(2)
        df_exib['TotalLitros']= df_exib['TotalLitros'].round(2)
        df_exib['TotalValor'] = df_exib['TotalValor'].round(2)

        df_exib.columns = [
            'Placa', 'Tipo', 'Categoria', 'Meta (km/L)',
            'Litros', 'Valor (R$)', 'Km Total', 'Média km/L', 'Status'
        ]

        st.dataframe(
            df_exib.sort_values('Km Total', ascending=False),
            use_container_width=True,
            hide_index=True,
        )


# ─── SEÇÃO: DRILL-DOWN POR PLACA ──────────────────────────────────────────────

def renderizar_drilldown(df: pd.DataFrame) -> None:
    """Permite selecionar uma placa e ver seu histórico detalhado."""
    st.subheader("🔎 Análise Individual por Placa")

    placas = sorted(df['Placa'].unique().tolist())
    placa_sel = st.selectbox("Selecione a placa:", options=placas, key="drilldown_placa")

    if not placa_sel:
        return

    df_p = df[df['Placa'] == placa_sel]

    col_info, col_graf = st.columns([1, 2])

    with col_info:
        def moda_col(col):
            s = df_p[col].dropna()
            return s.mode().iloc[0] if not s.empty else "—"

        meta_val = df_p['MetaNum'].dropna()
        meta_str = f"{fmt_num(float(meta_val.iloc[0]), 1)} km/L" if not meta_val.empty else "Sem meta definida"

        # Calcula a média ponderada desta placa
        df_p_valido = df_p[df_p['km_valido'] == True]
        if not df_p_valido.empty and df_p_valido['Qtde'].sum() > 0:
            media_real = df_p_valido['Km Perc.'].sum() / df_p_valido['Qtde'].sum()
            media_str = f"{fmt_num(media_real, 2)} km/L"
        else:
            media_str = "Sem km válido"

        # Cada campo usa \n\n (linha em branco) entre si.
        # Em CommonMark (padrão do Streamlit), um \n simples vira espaço.
        # Dois \n criam um novo parágrafo — cada campo fica em sua própria linha.
        campos = [
            f"**Placa:** {placa_sel}",
            f"**Tipo:** {moda_col('Tipo/Modelo')}",
            f"**Categoria:** {df_p['Categoria'].iloc[0]}",
            f"**Meta:** {meta_str}",
            f"**Condutor principal:** {moda_col('Condutor')}",
            f"**Abastecimentos:** {len(df_p)}",
            f"**Eficiência real:** {media_str}",
            f"**Total abastecido:** {fmt_num(df_p['Qtde'].sum(), 2)} L",
            f"**Total gasto:** {fmt_brl(df_p['Valor.total'].sum())}",
        ]
        st.markdown("\n\n".join(campos))

    with col_graf:
        st.plotly_chart(
            grafico_evolucao_placa(df_p, placa_sel),
            use_container_width=True,
            config=_CFG_PLOTLY
        )

    with st.expander("Ver todos os abastecimentos desta placa"):
        colunas_exib = ['Data Abast', 'Posto', 'Condutor', 'Qtde',
                        'Vlr. litro', 'Valor.total', 'Km Perc.', 'Média', 'km_valido']
        st.dataframe(
            df_p[colunas_exib].sort_values('Data Abast'),
            use_container_width=True,
            hide_index=True,
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
        # Exporta dois sheets: dados brutos + resumo por placa
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


# ─── TELA INICIAL (sem planilha carregada) ────────────────────────────────────

def renderizar_tela_inicial() -> None:
    """Tela de boas-vindas exibida antes de qualquer upload."""
    st.markdown("""
    <div style="text-align:center; padding: 50px 20px 30px 20px;">
        <div style="font-size: 64px; margin-bottom: 16px;">🚛</div>
        <h1 style="color: #1E295C; font-size: 30px; margin-bottom: 8px;">
            TNORTE — Gestão de Frota
        </h1>
        <p style="color: #6B6B6B; font-size: 15px; max-width: 520px; margin: 0 auto 24px auto;">
            Faça upload da planilha mensal de abastecimentos para visualizar
            KPIs, rankings de eficiência e gráficos interativos.
        </p>
        <p style="color: #C81D25; font-size: 13px;">
            ⬆️ Clique em <strong>Browse files</strong> acima para carregar o .xlsx
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("ℹ️ Como usar o dashboard"):
        st.markdown("""
        1. **Carregue a planilha** `.xlsx` com os abastecimentos do mês
        2. O dashboard **detecta automaticamente** o período (mês/ano)
        3. Use a **sidebar** para filtrar por categoria, posto, placa ou condutor
        4. Navegue pelas **abas** para ver a análise por categoria de veículo
        5. **Baixe** a apresentação PPTX ou o Excel processado no final da página

        **Formato esperado:** aba `Planilha1` com as colunas:
        `Placa`, `Data Abast`, `Qtde`, `Valor.total`, `Km Perc.`, `MetaMédia`, etc.
        """)


# ─── FUNÇÃO PRINCIPAL ─────────────────────────────────────────────────────────

def main() -> None:
    """
    Controla o fluxo completo do dashboard:
    upload → carga → filtros → visualizações → exportação.
    """
    # Upload — aceita apenas .xlsx
    arquivo = st.file_uploader(
        "📁 Carregar planilha de abastecimentos (.xlsx)",
        type=['xlsx'],
        help="Planilha Excel mensal — aba 'Planilha1'"
    )

    if arquivo is None:
        renderizar_tela_inicial()
        return

    # Carrega e valida a planilha (com cache — só lê o arquivo uma vez).
    # carregar_planilha levanta ValueError se o arquivo for inválido.
    # Capturamos aqui (fora do cache) para garantir que o st.error() sempre aparece.
    try:
        df = carregar_planilha(arquivo)
    except ValueError as e:
        st.error(f"❌ {e}")
        return

    # Detecta o período automaticamente
    periodo = detectar_periodo(df)

    st.success(f"✅ {len(df)} abastecimentos carregados — {periodo}")

    # Sidebar com filtros — retorna os valores selecionados
    cats, tipos, postos, placas, conds = renderizar_sidebar(df)

    # Aplica os filtros ao DataFrame
    df_f = aplicar_filtros(df, cats, tipos, postos, placas, conds)

    if df_f.empty:
        st.warning("⚠️ Nenhum registro com os filtros atuais. Remova alguns filtros para ver dados.")
        return

    # Calcula todas as métricas sobre os dados filtrados
    kpis      = calcular_kpis_gerais(df_f)
    df_placas = agregar_por_placa(df_f)
    ranking   = ranking_top3(df_placas)

    # ── Renderiza cada seção em ordem ────────────────────────────────────────
    renderizar_header(periodo, kpis['n_abastecimentos'], kpis['n_placas'])

    renderizar_kpis(kpis)

    renderizar_analise_postos(df_f)

    st.markdown("---")

    renderizar_ranking(ranking)

    st.markdown("---")

    renderizar_analise_categorias(df_placas)

    st.markdown("---")

    renderizar_tabela(df_placas)

    st.markdown("---")

    renderizar_drilldown(df_f)

    st.markdown("---")

    renderizar_exportacao(kpis, df_placas, df_f, periodo)


# Streamlit executa o script inteiro a cada interação do usuário,
# por isso chamamos main() diretamente no nível do módulo.
main()
