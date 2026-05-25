"""
Módulo responsável por carregar e validar a planilha de abastecimentos.
Separa a lógica de leitura de arquivo do restante do dashboard.
"""

import math
import pandas as pd
import streamlit as st
from typing import Optional

# Todas as colunas que o dashboard espera encontrar na planilha
COLUNAS_OBRIGATORIAS = [
    'Nº', 'Data Abast', 'Placa', 'Tipo/Modelo', 'Posto',
    'Condutor', 'Produto', 'Vlr. litro', 'Qtde', 'Valor.total',
    'Km/Hs anterior', 'Km/Hs abast', 'Km Perc.', 'Média', 'MetaMédia'
]


# @st.cache_data: guarda o resultado na memória do Streamlit.
# Quando o usuário interage com filtros, a planilha NÃO é relida do disco —
# o Streamlit retorna a versão em cache. Isso torna o dashboard muito mais rápido.
#
# IMPORTANTE: st.error() NÃO deve ser chamado dentro de funções cacheadas.
# O cache armazena apenas o valor de retorno; efeitos colaterais (como mostrar
# mensagens na tela) não são repetidos em cache hits. Por isso, erros são
# sinalizados via ValueError — o app.py captura e exibe a mensagem ao usuário.
@st.cache_data
def carregar_planilha(arquivo) -> pd.DataFrame:
    """
    Lê a planilha Excel, valida colunas e aplica tratamentos.

    Retorna um DataFrame pronto para uso.
    Lança ValueError com mensagem amigável se houver problema de formato.
    """
    try:
        # Tenta ler a aba 'Planilha1'; se não existir, lê a primeira aba
        try:
            df = pd.read_excel(arquivo, sheet_name='Planilha1', engine='openpyxl')
        except Exception:
            df = pd.read_excel(arquivo, sheet_name=0, engine='openpyxl')

        # Remove linhas completamente em branco (comum em planilhas Excel reais)
        df = df.dropna(how='all').reset_index(drop=True)

        # Verifica se todas as colunas obrigatórias existem
        colunas_faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
        if colunas_faltando:
            raise ValueError(
                f"Planilha inválida! Colunas faltando: **{', '.join(colunas_faltando)}**\n\n"
                "Verifique se o arquivo correto foi enviado e se os nomes das colunas estão certos."
            )

        # --- Tratamento de dados sujos ---

        # Placas frequentemente chegam com espaços extras: "RWV8B89 " → "RWV8B89"
        df['Placa'] = df['Placa'].astype(str).str.strip()

        # Condutor também pode ter espaços extras
        df['Condutor'] = df['Condutor'].astype(str).str.strip()

        # Garante que a data está em formato datetime (facilita filtros e exibição)
        df['Data Abast'] = pd.to_datetime(df['Data Abast'], errors='coerce')

        # MetaMédia é mista: números (5.5, 8.0) e texto ("Sem meta Def")
        # pd.to_numeric com errors='coerce' converte textos para NaN automaticamente
        df['MetaNum'] = pd.to_numeric(df['MetaMédia'], errors='coerce')

        # Garante que colunas numéricas são mesmo numéricas
        for col in ['Qtde', 'Valor.total', 'Km/Hs anterior', 'Km/Hs abast', 'Km Perc.', 'Média', 'Vlr. litro']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # --- Flag de km válido (regra de negócio crítica da TNORTE) ---
        # Apenas linhas com km_valido=True entram no cálculo de eficiência (km/L).
        # Linhas inválidas ainda contam para volume (L) e valor (R$).
        df['km_valido'] = (
            (df['Km/Hs anterior'] > 0) &    # não é o primeiro lançamento da placa
            (df['Km/Hs abast'] != 999999) &  # placa tem hodômetro funcionando
            (df['Km Perc.'] > 0) &           # rodou alguma distância
            (df['Km Perc.'] <= 3000)         # não é erro de digitação (nenhum caminhão roda 3000km entre abastecimentos)
        )

        # Classifica cada linha na categoria de eficiência da TNORTE
        df['Categoria'] = df['MetaNum'].apply(classificar_categoria)

        return df

    except ValueError:
        raise  # repassa erros de validação — app.py vai capturar e exibir
    except Exception as e:
        raise ValueError(f"Erro ao ler o arquivo: {str(e)}")


def classificar_categoria(meta: float) -> str:
    """
    Converte o valor numérico da meta em um nome de categoria.

    As categorias são definidas pela TNORTE conforme o tipo de veículo.
    Placas com meta NaN (texto "Sem meta Def") ficam em 'Sem Meta'.
    """
    # Verifica se é NaN (math.isnan está importado no topo do arquivo)
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
    Identifica o mês/ano do lote de dados pela coluna de data.
    Retorna string formatada como 'Abril/2026'.
    """
    if df is None or df.empty:
        return 'Desconhecido'

    datas_validas = df['Data Abast'].dropna()
    if datas_validas.empty:
        return 'Desconhecido'

    # Pega o MÊS mais frequente (não a data individual).
    # dt.to_period('M') converte "2026-04-03" → "2026-04" para poder comparar só o mês.
    # Exemplo: se há datas em março e abril, pega o mês que aparece mais vezes.
    data_ref = datas_validas.dt.to_period('M').mode().iloc[0].to_timestamp()

    meses_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }

    mes_nome = meses_pt.get(data_ref.month, str(data_ref.month))
    return f"{mes_nome}/{data_ref.year}"
