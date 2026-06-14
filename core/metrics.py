"""
Funções de cálculo de KPIs, agregações e rankings.
Toda a lógica de negócio fica aqui — separada da interface visual.

v2: separa combustível, ARLA e pedágio em contas independentes.
"""

import pandas as pd
import numpy as np
from typing import Dict, List

# Metas de eficiência por categoria — fonte única de verdade
METAS_CATEGORIA: Dict[str, float] = {
    'Leve':        8.0,
    'Média':       5.5,
    'Pesada Leve': 4.0,
    'Pesada':      3.4,
}

# Ordem dos meses para exibição no consolidado anual
ORDEM_MESES = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]


# ─── FORMATADORES PADRÃO BRASILEIRO ──────────────────────────────────────────

def fmt_brl(v: float) -> str:
    """Formata como moeda BR. Ex: 310390.87 → 'R$ 310.390,87'"""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "R$ 0,00"
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_num(v: float, decimais: int = 0) -> str:
    """Formata número BR. Ex: 43861.38 com decimais=2 → '43.861,38'"""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "0"
    s = f"{v:,.{decimais}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ─── KPIs GERAIS (3 CONTAS SEPARADAS) ────────────────────────────────────────

def calcular_kpis_gerais(df: pd.DataFrame) -> Dict:
    """
    Calcula os 6 indicadores principais, separados pelas 3 contas.

    COMBUSTÍVEL: litros, R$, km percorrido, média km/L
    ARLA: R$ (litros são informativos mas não entram nos KPIs de eficiência)
    PEDÁGIO: R$ (a Qtde=1 por passagem não representa litros — ignorada nos KPIs)
    """
    # Filtra cada conta separadamente
    df_comb = df[df['TipoProduto'] == 'COMBUSTIVEL']
    df_arla = df[df['TipoProduto'] == 'ARLA']
    df_ped  = df[df['TipoProduto'] == 'PEDAGIO']

    # Combustível: totais gerais (todas as linhas de comb)
    total_litros = df_comb['Qtde'].sum()
    total_valor_comb = df_comb['Valor.total'].sum()

    # Km rodado: soma bruta — reflete o total da planilha
    total_km = df_comb['Km Perc.'].sum()

    # Média km/L: usa só linhas km_valido para evitar leituras anômalas
    df_comb_val = df_comb[df_comb['km_valido'] == True]
    litros_validos = df_comb_val['Qtde'].sum()
    km_valido_sum = df_comb_val['Km Perc.'].sum()
    media_kml = km_valido_sum / litros_validos if litros_validos > 0 else 0.0

    return {
        # Combustível
        'total_litros':    total_litros,
        'total_valor_comb': total_valor_comb,
        'total_km':        total_km,
        'media_kml':       media_kml,
        # ARLA
        'total_valor_arla':   df_arla['Valor.total'].sum(),
        'total_litros_arla':  df_arla['Qtde'].sum(),
        # Pedágio
        'total_valor_pedagio':    df_ped['Valor.total'].sum(),
        'total_passagens_pedagio': int(df_ped['Qtde'].sum()),
        # Contagens gerais
        'n_abastecimentos': len(df_comb),
        'n_placas':         df['Placa'].nunique(),
    }


# ─── CONSOLIDADO MENSAL (JAN A DEZ) ──────────────────────────────────────────

def consolidado_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega os dados por mês, separando as 3 contas.

    Retorna um DataFrame com uma linha por mês (apenas meses presentes nos dados).
    Colunas: mes_nome, Litros, Km, R_Comb, R_Arla, R_Pedagio, MediaKmL
    """
    df_comb = df[df['TipoProduto'] == 'COMBUSTIVEL'].copy()
    df_arla = df[df['TipoProduto'] == 'ARLA'].copy()
    df_ped  = df[df['TipoProduto'] == 'PEDAGIO'].copy()

    # Agrega combustível por mês
    agg_comb = df_comb.groupby('mes_nome').agg(
        Litros=('Qtde', 'sum'),
        R_Comb=('Valor.total', 'sum'),
        Km=('Km Perc.', 'sum'),       # km bruto — reflete a planilha
    ).reset_index()

    # Litros e km válidos (só para calcular a média km/L)
    df_comb_val = df_comb[df_comb['km_valido'] == True]
    agg_km = df_comb_val.groupby('mes_nome').agg(
        LitrosValidos=('Qtde', 'sum'),
        KmValido=('Km Perc.', 'sum'),
    ).reset_index()

    # ARLA por mês
    agg_arla = df_arla.groupby('mes_nome').agg(
        R_Arla=('Valor.total', 'sum'),
    ).reset_index()

    # Pedágio por mês
    agg_ped = df_ped.groupby('mes_nome').agg(
        R_Pedagio=('Valor.total', 'sum'),
    ).reset_index()

    # Junta tudo num único DataFrame com todos os 12 meses como base
    base = pd.DataFrame({'mes_nome': ORDEM_MESES})
    resultado = base.merge(agg_comb, on='mes_nome', how='left')
    resultado = resultado.merge(agg_km,   on='mes_nome', how='left')
    resultado = resultado.merge(agg_arla, on='mes_nome', how='left')
    resultado = resultado.merge(agg_ped,  on='mes_nome', how='left')

    # Preenche NaN com zero (meses sem dados ficam zerados)
    for col in ['Litros', 'R_Comb', 'Km', 'LitrosValidos', 'KmValido', 'R_Arla', 'R_Pedagio']:
        resultado[col] = resultado[col].fillna(0.0)

    # Média ponderada por mês usa km e litros das linhas válidas
    resultado['MediaKmL'] = (
        resultado['KmValido'] / resultado['LitrosValidos'].replace(0.0, float('nan'))
    ).fillna(0.0)

    return resultado


# ─── ARLA POR PLACA ──────────────────────────────────────────────────────────

def arla_por_placa(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega o consumo de ARLA 32 por placa.
    Retorna: Placa, LitrosArla, ValorArla — ordenado por valor decrescente.
    """
    df_arla = df[df['TipoProduto'] == 'ARLA']

    if df_arla.empty:
        return pd.DataFrame(columns=['Placa', 'LitrosArla', 'ValorArla'])

    agg = df_arla.groupby('Placa').agg(
        LitrosArla=('Qtde', 'sum'),
        ValorArla=('Valor.total', 'sum'),
    ).reset_index()

    return agg.sort_values('ValorArla', ascending=False).reset_index(drop=True)


# ─── PEDÁGIO POR PLACA ────────────────────────────────────────────────────────

def pedagio_por_placa(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega o custo de pedágio por placa.
    Retorna: Placa, Passagens, ValorPedagio — ordenado por valor decrescente.

    Cada linha de PEDAGIO tem Qtde=1 (uma passagem).
    """
    df_ped = df[df['TipoProduto'] == 'PEDAGIO']

    if df_ped.empty:
        return pd.DataFrame(columns=['Placa', 'Passagens', 'ValorPedagio'])

    agg = df_ped.groupby('Placa').agg(
        Passagens=('Qtde', 'sum'),
        ValorPedagio=('Valor.total', 'sum'),
    ).reset_index()

    return agg.sort_values('ValorPedagio', ascending=False).reset_index(drop=True)


# ─── MELHOR MÉDIA POR TIPO DE VEÍCULO ────────────────────────────────────────

def melhor_media_por_tipo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada tipo de veículo, retorna a placa com a melhor média km/L no período.

    Retorna: Tipo, Placa, MediaKmL, Meta, Status
    Só considera TipoProduto==COMBUSTIVEL e km_valido==True.
    """
    df_comb = df[(df['TipoProduto'] == 'COMBUSTIVEL') & (df['km_valido'] == True)]

    if df_comb.empty:
        return pd.DataFrame(columns=['Tipo', 'Placa', 'MediaKmL', 'Meta', 'Status'])

    # Média ponderada por placa
    def moda_str(s):
        m = s.dropna()
        m = m[m != '']
        return m.mode().iloc[0] if len(m.mode()) > 0 else ''

    def moda_num(s):
        m = s.dropna()
        return m.mode().iloc[0] if len(m.mode()) > 0 else float('nan')

    agg = df_comb.groupby('Placa').agg(
        TotalKm=('Km Perc.', 'sum'),
        LitrosValidos=('Qtde', 'sum'),
        Tipo=('Tipo/Modelo', moda_str),
        Meta=('MetaNum', moda_num),
    ).reset_index()

    agg['MediaKmL'] = (
        agg['TotalKm'] / agg['LitrosValidos'].replace(0.0, float('nan'))
    ).fillna(0.0)

    # Filtra só placas com tipo definido e com km real
    agg = agg[(agg['Tipo'] != '') & (agg['Tipo'] != 'nan') & (agg['MediaKmL'] > 0)]

    if agg.empty:
        return pd.DataFrame(columns=['Tipo', 'Placa', 'MediaKmL', 'Meta', 'Status'])

    # Para cada tipo, pega a placa com maior média
    idx_melhores = agg.groupby('Tipo')['MediaKmL'].idxmax()
    melhores = agg.loc[idx_melhores].copy()

    # Status vs meta
    def calcular_status(row) -> str:
        if pd.isna(row['Meta']) or row['Meta'] == 0:
            return '—'
        return '✅ Acima' if row['MediaKmL'] >= row['Meta'] else '❌ Abaixo'

    melhores['Status'] = melhores.apply(calcular_status, axis=1)

    return melhores[['Tipo', 'Placa', 'MediaKmL', 'Meta', 'Status']].sort_values('Tipo').reset_index(drop=True)


# ─── AGREGAÇÃO POR PLACA (COMBUSTÍVEL) ───────────────────────────────────────

def agregar_por_placa(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega dados de COMBUSTÍVEL por placa.

    ARLA e PEDÁGIO são excluídos aqui — têm suas próprias funções.
    A média km/L usa MÉDIA PONDERADA: Σ(km válido) / Σ(litros válidos).
    """
    # Só combustível entra na agregação de placa (eficiência)
    df_comb = df[df['TipoProduto'] == 'COMBUSTIVEL']
    df_comb_val = df_comb[df_comb['km_valido'] == True]

    def moda_segura(serie):
        s = serie.dropna()
        return s.mode().iloc[0] if not s.empty else ''

    # Totais de combustível por placa (todas as linhas) — inclui km bruto
    agg_geral = df_comb.groupby('Placa').agg(
        Tipo=('Tipo/Modelo', moda_segura),
        Categoria=('Categoria', 'first'),
        MetaNum=('MetaNum', 'first'),
        TotalLitros=('Qtde', 'sum'),
        TotalValor=('Valor.total', 'sum'),
        TotalKm=('Km Perc.', 'sum'),       # km bruto para exibição
        QtdAbastecimentos=('Nº', 'count'),
    ).reset_index()

    # Km e litros válidos (só para calcular a média km/L)
    if not df_comb_val.empty:
        agg_km = df_comb_val.groupby('Placa').agg(
            KmValido=('Km Perc.', 'sum'),
            LitrosValidos=('Qtde', 'sum'),
        ).reset_index()
    else:
        agg_km = pd.DataFrame(columns=['Placa', 'KmValido', 'LitrosValidos'])

    resultado = agg_geral.merge(agg_km, on='Placa', how='left')

    resultado['TotalKm']       = pd.to_numeric(resultado['TotalKm'],       errors='coerce').fillna(0.0)
    resultado['LitrosValidos'] = pd.to_numeric(resultado['LitrosValidos'], errors='coerce').fillna(0.0)
    if 'KmValido' not in resultado.columns:
        resultado['KmValido'] = 0.0
    resultado['KmValido']      = pd.to_numeric(resultado['KmValido'],      errors='coerce').fillna(0.0)

    resultado['MediaKmL'] = (
        resultado['KmValido'] / resultado['LitrosValidos'].replace(0.0, float('nan'))
    ).fillna(0.0)

    resultado['AtiugiuMeta'] = resultado.apply(
        lambda r: (r['MediaKmL'] >= r['MetaNum']) if pd.notna(r['MetaNum']) else None,
        axis=1
    )

    return resultado


# ─── CUSTO POR POSTO (COMBUSTÍVEL) ───────────────────────────────────────────

def calcular_custo_por_posto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preço médio PONDERADO por litro em cada posto — apenas combustível.
    ARLA e PEDÁGIO são excluídos (têm preços incomparáveis com diesel/gasolina).
    """
    df_comb = df[df['TipoProduto'] == 'COMBUSTIVEL']

    if df_comb.empty:
        return pd.DataFrame(columns=['Posto', 'TotalValor', 'TotalLitros',
                                     'QtdAbastecimentos', 'PrecoMedio'])

    agg = df_comb.groupby('Posto').agg(
        TotalValor=('Valor.total', 'sum'),
        TotalLitros=('Qtde', 'sum'),
        QtdAbastecimentos=('Nº', 'count'),
    ).reset_index()

    agg['PrecoMedio'] = (
        agg['TotalValor'] / agg['TotalLitros'].replace(0.0, float('nan'))
    ).fillna(0.0)

    return agg.sort_values('PrecoMedio').reset_index(drop=True)


# ─── RANKING TOP 3 ────────────────────────────────────────────────────────────

def ranking_top3(df_placas: pd.DataFrame) -> Dict[str, List[Dict]]:
    """
    Top 3 de eficiência (km/L) para cada categoria de meta.
    Retorna dict: {'Leve': [...], 'Média': [...], 'Pesada Leve': [...], 'Pesada': [...]}
    """
    categorias = ['Leve', 'Média', 'Pesada Leve', 'Pesada']
    resultado = {}

    for categoria in categorias:
        df_cat = df_placas[
            (df_placas['Categoria'] == categoria) &
            (df_placas['MediaKmL'] > 0)
        ].sort_values('MediaKmL', ascending=False)

        top3 = []
        for i, (_, row) in enumerate(df_cat.head(3).iterrows()):
            top3.append({
                'posicao': i + 1,
                'placa': row['Placa'],
                'media_kml': row['MediaKmL'],
                'meta': row['MetaNum'],
                'tipo': row.get('Tipo', ''),
            })

        resultado[categoria] = top3

    return resultado
