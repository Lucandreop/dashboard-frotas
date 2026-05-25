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
    condutores: List[str],
) -> pd.DataFrame:
    """
    Filtra o DataFrame conforme as seleções da sidebar.

    Listas vazias significam "sem filtro para esse campo" (mostra tudo).
    Cada filtro preenchido reduz o conjunto de dados (operação AND).
    """
    df_filtrado = df.copy()

    # Cada bloco 'if' só filtra se o usuário realmente selecionou algo
    if categorias:
        df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(categorias)]

    if tipos:
        df_filtrado = df_filtrado[df_filtrado['Tipo/Modelo'].isin(tipos)]

    if postos:
        df_filtrado = df_filtrado[df_filtrado['Posto'].isin(postos)]

    if placas:
        df_filtrado = df_filtrado[df_filtrado['Placa'].isin(placas)]

    if condutores:
        df_filtrado = df_filtrado[df_filtrado['Condutor'].isin(condutores)]

    return df_filtrado
