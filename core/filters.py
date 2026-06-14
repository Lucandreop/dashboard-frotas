"""
Aplica os filtros selecionados na sidebar ao DataFrame principal.
Filtros são combinados com AND lógico: cada filtro restringe ainda mais os dados.
"""

import pandas as pd
from typing import List


def aplicar_filtros(
    df: pd.DataFrame,
    categorias: List[str],
    tipos: List[str],
    postos: List[str],
    placas: List[str],
    mes_nome: str = '',
) -> pd.DataFrame:
    """
    Filtra o DataFrame conforme as seleções da sidebar.

    Listas vazias ou string vazia significam 'sem filtro para esse campo'.
    O filtro de mês aceita 'Ano inteiro' como valor especial (não filtra).
    """
    df_filtrado = df.copy()

    if categorias:
        df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(categorias)]

    if tipos:
        df_filtrado = df_filtrado[df_filtrado['Tipo/Modelo'].isin(tipos)]

    if postos:
        df_filtrado = df_filtrado[df_filtrado['Posto'].isin(postos)]

    if placas:
        df_filtrado = df_filtrado[df_filtrado['Placa'].isin(placas)]

    # Filtro de mês: 'Ano inteiro' ou vazio = sem filtro
    if mes_nome and mes_nome != 'Ano inteiro':
        df_filtrado = df_filtrado[df_filtrado['mes_nome'] == mes_nome]

    return df_filtrado
