"""
Módulo responsável por carregar e validar a planilha de abastecimentos.
Suporta dois formatos: planilha mensal (um mês) e planilha geral (ano inteiro empilhado).
"""

import math
import pandas as pd
import streamlit as st
from typing import Optional

# Meses em português — usado para criar a coluna mes_nome
MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

# Colunas mínimas sem as quais o dashboard não consegue funcionar
COLUNAS_MINIMAS = ['Data Abast', 'Placa', 'Produto', 'Qtde', 'Valor.total',
                   'Km/Hs anterior', 'Km/Hs abast', 'Km Perc.', 'MetaMédia']


@st.cache_data
def carregar_planilha(arquivo) -> pd.DataFrame:
    """
    Lê a planilha Excel e retorna um DataFrame pronto para uso.

    Aceita dois formatos:
    - Formato antigo (v1): tem Nº, Tipo/Modelo, Condutor, Posto
    - Formato novo (v2): tem Coluna1 (tipo), Posto ou Histórico/estabelecimento,
      sem Nº e sem Condutor

    Lança ValueError com mensagem amigável se o arquivo for inválido.
    """
    try:
        # Tenta ler aba 'Planilha1'; se não existir, lê a primeira aba
        try:
            df = pd.read_excel(arquivo, sheet_name='Planilha1', engine='openpyxl')
        except Exception:
            df = pd.read_excel(arquivo, sheet_name=0, engine='openpyxl')

        # Remove linhas completamente em branco
        df = df.dropna(how='all').reset_index(drop=True)

        # Garante que nomes de colunas não têm espaços extras
        df.columns = [c.strip() for c in df.columns]

        # --- Normalização de nomes de colunas ---

        # Estabelecimento: aceita 'Histórico/estabelecimento' ou 'Posto'
        if 'Histórico/estabelecimento' in df.columns and 'Posto' not in df.columns:
            df = df.rename(columns={'Histórico/estabelecimento': 'Posto'})

        # Tipo de veículo: aceita 'Coluna1' (formato novo) ou 'Tipo/Modelo' (formato antigo)
        if 'Coluna1' in df.columns and 'Tipo/Modelo' not in df.columns:
            df = df.rename(columns={'Coluna1': 'Tipo/Modelo'})

        # Normaliza nome da coluna MetaMédia — variações de encoding
        for variante in ['MetaMédia', 'MetaMedia', 'Meta Média', 'Meta Media',
                         'Metamédia', 'Metamedia']:
            if variante in df.columns and 'MetaMédia' not in df.columns:
                df = df.rename(columns={variante: 'MetaMédia'})
                break

        # Verifica colunas mínimas obrigatórias
        faltando = [c for c in COLUNAS_MINIMAS if c not in df.columns]
        if faltando:
            raise ValueError(
                f"Planilha inválida! Colunas faltando: **{', '.join(faltando)}**\n\n"
                "Verifique se o arquivo correto foi enviado."
            )

        # Colunas opcionais: cria vazias se não existirem
        if 'Condutor' not in df.columns:
            df['Condutor'] = ''
        # 'Nº' pode ser lido como 'N°' ou sem o símbolo dependendo da planilha
        col_n = next((c for c in df.columns if c.startswith('N') and len(c) <= 2), None)
        if col_n and col_n != 'Nº':
            df = df.rename(columns={col_n: 'Nº'})
        if 'Nº' not in df.columns:
            df['Nº'] = range(1, len(df) + 1)
        if 'Tipo/Modelo' not in df.columns:
            df['Tipo/Modelo'] = 'Não Cadastrado'

        # --- Limpeza de dados ---

        # Placas com espaços extras: "RWV8B89 " → "RWV8B89"
        df['Placa'] = df['Placa'].astype(str).str.strip()

        # Condutor e Tipo/Modelo também podem ter espaços
        df['Condutor'] = df['Condutor'].astype(str).str.strip()
        df['Tipo/Modelo'] = df['Tipo/Modelo'].astype(str).str.strip()

        # Data em formato datetime
        df['Data Abast'] = pd.to_datetime(df['Data Abast'], errors='coerce')

        # MetaMédia: mistura números e texto ("Sem meta Def") → converte para float
        df['MetaNum'] = pd.to_numeric(df['MetaMédia'], errors='coerce')

        # Colunas numéricas que podem chegar como texto (ex: "40.195,73")
        for col in ['Qtde', 'Valor.total', 'Km/Hs anterior', 'Km/Hs abast',
                    'Km Perc.', 'Média', 'Vlr. litro']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # --- Classificação por tipo de produto (ponto central da v2) ---
        df['TipoProduto'] = df['Produto'].apply(classificar_produto)

        # --- Colunas de período (derivadas da data) ---
        df['ano'] = df['Data Abast'].dt.year
        df['mes'] = df['Data Abast'].dt.month
        df['mes_nome'] = df['mes'].map(MESES_PT)

        # --- Flag de km válido (só faz sentido para COMBUSTIVEL) ---
        # Linhas de ARLA e PEDAGIO sempre ficam com km_valido=False
        df['km_valido'] = (
            (df['TipoProduto'] == 'COMBUSTIVEL') &
            (df['Km/Hs anterior'] > 0) &
            (df['Km/Hs abast'] != 999999) &
            (df['Km Perc.'] > 0) &
            (df['Km Perc.'] <= 3000)
        )

        # --- Categoria por meta (baseada em MetaNum) ---
        df['Categoria'] = df['MetaNum'].apply(classificar_categoria)

        # Aviso se houver placas sem tipo definido
        sem_tipo = df[df['Tipo/Modelo'].isin(['Não Cadastrado', 'nan', ''])]['Placa'].unique()
        if len(sem_tipo) > 0:
            st.warning(
                f"⚠️ {len(sem_tipo)} placa(s) sem Tipo de Veículo definido: "
                f"{', '.join(sem_tipo[:10])}{'...' if len(sem_tipo) > 10 else ''}. "
                "Preencha o arquivo `data/cadastro_veiculos.csv` para corrigir."
            )

        return df

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Erro ao ler o arquivo: {str(e)}")


def classificar_produto(produto: str) -> str:
    """
    Classifica o lançamento em COMBUSTIVEL, ARLA ou PEDAGIO.

    PEDAGIO: 'VALE PEDAGIO' — Qtde=1, Vlr.litro = valor da passagem, Km=0
    ARLA: 'ARLA 32' — litros e R$, mas não move o veículo (sem km/L)
    COMBUSTIVEL: todo o resto (DIESEL S10, GASOLINA COMUM, ETANOL, etc.)
    """
    p = str(produto).upper()
    if 'PEDAGIO' in p or 'PEDÁGIO' in p:
        return 'PEDAGIO'
    if 'ARLA' in p:
        return 'ARLA'
    return 'COMBUSTIVEL'


def classificar_categoria(meta: float) -> str:
    """
    Converte o valor numérico da meta em nome de categoria TNORTE.
    Placas sem meta numérica ficam em 'Sem Meta'.
    """
    if meta is None:
        return 'Sem Meta'
    try:
        if math.isnan(float(meta)):
            return 'Sem Meta'
    except (TypeError, ValueError):
        return 'Sem Meta'

    meta = float(meta)
    if meta == 8.0:
        return 'Leve'
    elif meta == 5.5:
        return 'Média'
    elif meta in (3.8, 4.0):
        return 'Pesada Leve'
    elif meta in (2.5, 3.2, 3.4):
        return 'Pesada'
    else:
        return 'Sem Meta'


def detectar_periodo(df: pd.DataFrame) -> str:
    """
    Identifica o período do dataset.
    Retorna 'Abril/2026' para planilha mensal ou '2026' para planilha anual.
    """
    if df is None or df.empty:
        return 'Desconhecido'

    datas_validas = df['Data Abast'].dropna()
    if datas_validas.empty:
        return 'Desconhecido'

    meses_unicos = datas_validas.dt.to_period('M').nunique()

    if meses_unicos > 1:
        # Planilha com múltiplos meses: retorna só o ano
        ano = datas_validas.dt.year.mode().iloc[0]
        return str(ano)

    # Planilha de um único mês
    data_ref = datas_validas.dt.to_period('M').mode().iloc[0].to_timestamp()
    mes_nome = MESES_PT.get(data_ref.month, str(data_ref.month))
    return f"{mes_nome}/{data_ref.year}"


def listar_meses_disponiveis(df: pd.DataFrame) -> list[str]:
    """
    Retorna lista ordenada dos meses presentes no DataFrame.
    Exemplo: ['Janeiro', 'Fevereiro', 'Março']
    """
    if df is None or df.empty:
        return []

    meses_presentes = (
        df[['mes', 'mes_nome']]
        .drop_duplicates()
        .dropna()
        .sort_values('mes')
    )
    return meses_presentes['mes_nome'].tolist()
