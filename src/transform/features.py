import pandas as pd
import numpy as np
from unicodedata import normalize
from config import settings
from transform.conformidade import arredonda_in5

def resolve_cod_ibge(ente):
    if ente in settings.MAP_CAPITAIS_IBGE:
        return settings.MAP_CAPITAIS_IBGE[ente]
    elif ente in settings.MAP_ESTADOS_IBGE:
        return settings.MAP_ESTADOS_IBGE[ente]
    else:
        return None  # ou pd.NA



def calcula_cotas_vagas_e_valores(
    df: pd.DataFrame,
    col_valor_total: str = 'valor_total',
    col_vagas_totais: str = 'vagas_totais',
    type_round: str = 'in5'
) -> pd.DataFrame:

    cotas = {
        'negras': 'perc_cotas_negras',
        'indigenas': 'perc_cotas_indigenas',
        'pcd': 'perc_cotas_pcd'
    }

    # calcula vagas
    if type_round == 'in5':  # IN MinC nº 5/2023, art. 5º, §2º (meio para cima)
        for grupo, col_perc in cotas.items():
            df[f'vagas_cotas_{grupo}'] = (
                (df[col_perc] * df[col_vagas_totais])
                .apply(lambda x: arredonda_in5(x) if pd.notna(x) else pd.NA)
                .astype('Int64')
            )
    elif type_round == 'ceil':
        for grupo, col_perc in cotas.items():
            df[f'vagas_cotas_{grupo}'] = (
                np.ceil(df[col_perc] * df[col_vagas_totais])
                .astype('Int64')
            )
    else:
        for grupo, col_perc in cotas.items():
            df[f'vagas_cotas_{grupo}'] = (
                np.round(df[col_perc] * df[col_vagas_totais])
                .astype('Int64')
            )        

    # valor unitário
    df['valor_por_vaga'] = df[col_valor_total] / df[col_vagas_totais]

    # calcula valores
    for grupo in cotas.keys():
        df[f'valor_cotas_{grupo}'] = (
            df['valor_por_vaga'] * df[f'vagas_cotas_{grupo}']
        )

    return df

def calcula_valor_cotas_sem_vagas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    mask_sem_vagas = df['vagas_totais'].isna()

    df.loc[mask_sem_vagas, 'valor_cotas_negras'] = (
        df.loc[mask_sem_vagas, 'perc_cotas_negras'] * df.loc[mask_sem_vagas, 'valor_total']
    )

    df.loc[mask_sem_vagas, 'valor_cotas_indigenas'] = (
        df.loc[mask_sem_vagas, 'perc_cotas_indigenas'] * df.loc[mask_sem_vagas, 'valor_total']
    )

    df.loc[mask_sem_vagas, 'valor_cotas_pcd'] = (
        df.loc[mask_sem_vagas, 'perc_cotas_pcd'] * df.loc[mask_sem_vagas, 'valor_total']
    )

    return df



def cria_flags_cotas(df: pd.DataFrame) -> pd.DataFrame:
    # LPG (IN MinC nº 5/2023): só negras e indígenas são obrigatórias
    regras = {g: (f'perc_cotas_{g}', limite) for g, limite in settings.COTA_MIN.items()}

    for grupo, (col, limite) in regras.items():
        df[f'flag_cotas_{grupo}'] = df[col] >= limite

    return df


def cria_tipo_edital(
    df: pd.DataFrame,
    col_origem: str = 'nome_pdf_pk',
    col_destino: str = 'tipo_edital'
) -> pd.DataFrame:

    def normaliza_texto(s: str) -> str:
        s = str(s)
        s = normalize('NFD', s)
        s = s.encode('ascii', 'ignore').decode('utf-8')
        return s.lower()

    texto = df[col_origem].apply(normaliza_texto)

    sep = r'(^|[_\-\s\.])'
    end = r'([_\-\s\.]|$)'

    regras = [
        # CULTURA VIVA (prioridade máxima)
        (
            rf'{sep}(pncv|cultura{sep}?viva|ponto(s)?|pontao(s)?|pontoe?s?){end}',
            'CULTURA VIVA'
        ),

        # BOLSA
        (
            rf'{sep}bolsa(s)?{end}',
            'BOLSA'
        ),

        # SUBSÍDIO (com erro comum)
        (
            rf'{sep}(subsidio|subisidio)(s)?{end}',
            'SUBSÍDIO'
        ),

        # PRÊMIO / PREMIAÇÃO
        (
            rf'{sep}premi(o|os|acao|acoes)?{end}',
            'PRÊMIO'
        ),

        # FOMENTO (inclui QUALIFICAÇÃO)
        (
            rf'{sep}(fomento(s)?|qualificacao){end}',
            'FOMENTO'
        ),
    ]

    df[col_destino] = pd.NA

    for pattern, label in regras:
        mask = texto.str.contains(pattern, regex=True)
        df.loc[mask & df[col_destino].isna(), col_destino] = label

    return df


def print_resumo(df: pd.DataFrame, categoria_cota:str = 'cotas_negras'):
    # Cotas pessoas negras - Geral
    mask_cotas_negras   = df[f'flag_{categoria_cota}'].eq(1)
    qtd_cotas_negras    = mask_cotas_negras.sum()
    qtd_total           = len(df)
    percentual          = qtd_cotas_negras / qtd_total * 100 # 85.75%
    soma_valor          = df[f'valor_{categoria_cota}'].sum() # 302.939.910,84
    soma_vaga           = df[f'vagas_{categoria_cota}'].sum() 

    print("==========================================")
    print(f"Geral - {categoria_cota}")
    print("==========================================")
    print("% Cumprimento Cotas")
    print(percentual)
    print("\nValor total")
    print(soma_valor)
    print("\nNúmero de vagas")
    print(soma_vaga)
    print("==========================================")


    # Cotas pessoas negras - Estados
    df_estados          = df.loc[df['tipo_ente'] == 'ESTADO']
    mask_cotas_negras   = df_estados[f'flag_{categoria_cota}'].eq(1)
    qtd_cotas_negras    = mask_cotas_negras.sum()
    qtd_total           = len(df_estados)
    percentual          = qtd_cotas_negras / qtd_total * 100 # 85.75%
    soma_valor          = df_estados[f'valor_{categoria_cota}'].sum() # 302.939.910,84
    soma_vaga           = df_estados[f'vagas_{categoria_cota}'].sum() 

    print("==========================================")
    print("Estados")
    print("==========================================")
    print("% Cumprimento ")
    print(percentual)
    print("\nValor total ")
    print(soma_valor)
    print("\nNúmero de vagas")
    print(soma_vaga)
    print("==========================================")
    # Cotas pessoas negras - Capitais

    df_capitais          = df.loc[df['tipo_ente'] == 'CAPITAL']
    mask_cotas_negras    = df_capitais[f'flag_{categoria_cota}'].eq(1)
    qtd_cotas_negras    = mask_cotas_negras.sum()
    qtd_total           = len(df_capitais)
    percentual          = qtd_cotas_negras / qtd_total * 100 # 83.75%
    soma_valor          = df_capitais[f'valor_{categoria_cota}'].sum() # 56.346.222,21
    soma_vaga           = df_capitais[f'vagas_{categoria_cota}'].sum() 
    print("Capitais")
    print("==========================================")
    print("% Cumprimento")
    print(percentual)
    print("\nValor total ")
    print(soma_valor)
    print("\nNúmero de vagas")
    print(soma_vaga)
    print("==========================================")