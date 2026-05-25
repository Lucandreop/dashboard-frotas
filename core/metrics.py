"""
Funções de cálculo de KPIs, agregações e rankings.
Toda a lógica de negócio fica aqui — separada da interface visual.
"""

import pandas as pd
import numpy as np
from typing import Dict, List

# Fonte única de verdade para as metas de eficiência por categoria.
# Importar daqui em qualquer módulo que precise das metas — nunca hardcode.
METAS_CATEGORIA: Dict[str, float] = {
    'Leve':        8.0,
    'Média':       5.5,
    'Pesada Leve': 4.0,
    'Pesada':      3.4,
}


# ─── FORMATADORES DE NÚMERO NO PADRÃO BRASILEIRO ─────────────────────────────
# O Brasil usa ponto como separador de milhar e vírgula como decimal.
# Exemplo inglês: 1,234.56  →  Exemplo BR: 1.234,56

def fmt_brl(v: float) -> str:
    """
    Formata valor como moeda brasileira.
    Exemplo: 310390.87 → 'R$ 310.390,87'
    """
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "R$ 0,00"
    # f"{v:,.2f}" → "310,390.87" (padrão americano com vírgula)
    # Trocamos: vírgula → X (marcador temporário), ponto → vírgula, X → ponto
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_num(v: float, decimais: int = 0) -> str:
    """
    Formata número no padrão brasileiro.
    Exemplo: 43861.38 com decimais=2 → '43.861,38'
    Exemplo: 151632 com decimais=0  → '151.632'
    """
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "0"
    s = f"{v:,.{decimais}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ─── KPIs GERAIS ──────────────────────────────────────────────────────────────

def calcular_kpis_gerais(df: pd.DataFrame) -> Dict:
    """
    Calcula os 4 indicadores principais do dashboard.

    REGRA IMPORTANTE:
    - Volume (L) e Valor (R$): contam TODOS os registros
    - Distância (km) e Eficiência (km/L): contam APENAS km_valido=True

    Isso evita que registros com hodômetro quebrado distorçam a eficiência.
    """
    # Totais gerais — todas as linhas, inclusive sem hodômetro
    total_litros = df['Qtde'].sum()
    total_valor = df['Valor.total'].sum()

    # Distância — apenas registros com km válido
    df_valido = df[df['km_valido'] == True]
    total_km = df_valido['Km Perc.'].sum()

    # Preço médio ponderado: total gasto ÷ total de litros
    # (não é a média simples da coluna Vlr.litro, que ignoraria volume comprado)
    preco_medio = total_valor / total_litros if total_litros > 0 else 0.0

    return {
        'total_litros': total_litros,
        'total_valor': total_valor,
        'total_km': total_km,
        'preco_medio': preco_medio,
        'n_abastecimentos': len(df),
        'n_placas': df['Placa'].nunique(),
    }


# ─── AGREGAÇÃO POR PLACA ──────────────────────────────────────────────────────

def agregar_por_placa(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega os dados por placa, calculando totais e a média km/L correta.

    A média km/L usa MÉDIA PONDERADA (não média simples das linhas):
        media = Σ(km percorrido válido) / Σ(litros das linhas válidas)

    Por que ponderada? Se uma placa abasteceu 50L em um trecho e 200L em outro,
    a média simples trata os dois iguais — a ponderada considera o volume real.
    """
    # Separa registros com km válido para o cálculo de eficiência
    df_valido = df[df['km_valido'] == True]

    # Função auxiliar para pegar o valor mais frequente sem explodir em erros
    def moda_segura(serie):
        s = serie.dropna()
        return s.mode().iloc[0] if not s.empty else ''

    # Agrega totais gerais (todas as linhas da placa)
    agg_geral = df.groupby('Placa').agg(
        Tipo=('Tipo/Modelo', moda_segura),
        Categoria=('Categoria', 'first'),
        MetaNum=('MetaNum', 'first'),
        TotalLitros=('Qtde', 'sum'),
        TotalValor=('Valor.total', 'sum'),
        QtdAbastecimentos=('Nº', 'count'),
        Condutor=('Condutor', moda_segura),
    ).reset_index()

    # Agrega km e litros VÁLIDOS separadamente
    if not df_valido.empty:
        agg_km = df_valido.groupby('Placa').agg(
            TotalKm=('Km Perc.', 'sum'),
            LitrosValidos=('Qtde', 'sum'),
        ).reset_index()
    else:
        # Caso extremo: nenhum registro com km válido
        agg_km = pd.DataFrame(columns=['Placa', 'TotalKm', 'LitrosValidos'])

    # Junta os dois DataFrames pela placa (left join: mantém todas as placas)
    resultado = agg_geral.merge(agg_km, on='Placa', how='left')

    # Garante dtype float após o merge (merge com df vazio produz dtype object)
    resultado['TotalKm']       = pd.to_numeric(resultado['TotalKm'],       errors='coerce').fillna(0.0)
    resultado['LitrosValidos'] = pd.to_numeric(resultado['LitrosValidos'], errors='coerce').fillna(0.0)

    # Divisão segura: substitui 0 por NaN antes de dividir, depois preenche com 0.
    # np.where avalia AMBOS os lados antes de escolher — por isso não usamos ele aqui.
    # Se LitrosValidos for 0 (nenhum km válido para a placa), MediaKmL fica 0.
    resultado['MediaKmL'] = (
        resultado['TotalKm'] / resultado['LitrosValidos'].replace(0.0, float('nan'))
    ).fillna(0.0)

    # Status vs meta: True = atingiu, False = abaixo, None = sem meta
    resultado['AtiugiuMeta'] = resultado.apply(
        lambda r: (r['MediaKmL'] >= r['MetaNum']) if pd.notna(r['MetaNum']) else None,
        axis=1
    )

    return resultado


# ─── ANÁLISE POR POSTO ────────────────────────────────────────────────────────

def calcular_custo_por_posto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o preço médio PONDERADO por litro em cada posto.

    Por que ponderado e não média simples de Vlr.litro?
    Porque o volume comprado varia: 200L a R$6,93 pesa mais do que 50L.
    Preço ponderado = total gasto ÷ total de litros comprados no posto.
    """
    agg = df.groupby('Posto').agg(
        TotalValor=('Valor.total', 'sum'),
        TotalLitros=('Qtde', 'sum'),
        QtdAbastecimentos=('Nº', 'count'),
    ).reset_index()

    # Divisão segura (evita ZeroDivisionError se um posto tiver Qtde = 0)
    agg['PrecoMedio'] = (
        agg['TotalValor'] / agg['TotalLitros'].replace(0.0, float('nan'))
    ).fillna(0.0)

    return agg.sort_values('PrecoMedio').reset_index(drop=True)


# ─── RANKING TOP 3 ────────────────────────────────────────────────────────────

def ranking_top3(df_placas: pd.DataFrame) -> Dict[str, List[Dict]]:
    """
    Retorna o Top 3 de eficiência (km/L) para cada categoria de meta.

    Retorna dicionário: {'Leve': [...], 'Média': [...], 'Pesada Leve': [...], 'Pesada': [...]}
    Cada lista contém dicts com: posicao, placa, media_kml, meta, tipo.
    """
    categorias = ['Leve', 'Média', 'Pesada Leve', 'Pesada']
    resultado = {}

    for categoria in categorias:
        # Filtra pela categoria e descarta placas sem dados de km
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
