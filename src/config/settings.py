from pathlib import Path

# CAMINHO DOS DIRETÓRIOS
ROOT = Path(__file__).resolve().parents[2] # PASTA RAÍZ DO PROJETO

DATA_PATH = ROOT / "data" # PASTA DE DADOS 
RAW_DATA_PATH = DATA_PATH / "raw" # RAW_DATA_PATH: onde ficam os dados crus, exatamente como chegaram da fonte, sem nenhum tratamento.
PROCESSED_DATA_PATH = DATA_PATH / "processed" # PROCESSED_DATA_PATH: onde são salvos os dados já tratados, limpos e prontos para análise/modelagem.
INTERIM_DATA_PATH = DATA_PATH / "interim" # INTERIM_DATA_PATH: área temporária para versões intermediárias durante o pipeline (não crus, mas ainda não finais).
EXTERNAL_DATA_PATH = DATA_PATH / "external" # EXTERNAL_DATA_PATH: reservatório para dados externos ao projeto (APIs, terceiros, microdados públicos, etc.).
FINAL_DATA_PATH = DATA_PATH / "final" # FINAL_DATA_PATH: entrega da obra-prima; resultados finais do pipeline prontos para consumo (dashboards, relatórios etc.).

# CAMINHOS GLOBAIS
MD_ROOT:str = Path(INTERIM_DATA_PATH/'MD')
CAPITAL_MD_ROOT:str = Path(MD_ROOT/'CAPITAL')
ESTADO_MD_ROOT:str = Path(MD_ROOT/'ESTADO')

PDF_ROOT: str = Path(RAW_DATA_PATH/'EDITAL_NOVO')
CAPITAL_PDF_ROOT: str = Path(PDF_ROOT / 'CAPITAL')
ESTADO_PDF_ROOT: str = Path(PDF_ROOT / 'ESTADO')


# LPG - LEI PAULO GUSTAVO
LPG_PDF_ROOT = DATA_PATH / 'EDITAIS'            # data/EDITAIS/{Capitais,Estados}/<ente>/*.pdf
LPG_NOVOS_ROOT = DATA_PATH / 'NOVOS'              # editais avulsos: NOVOS/<pasta>/*.pdf (ente pelo nome do arquivo)
LPG_PASTAS_IGNORADAS = {'outros editais', 'PlanilhasPC'}
LPG_INTERIM = INTERIM_DATA_PATH / 'LPG'
LPG_MD_ROOT = LPG_INTERIM / 'MD'                # editais convertidos para Markdown
LPG_PDF_COMPRIMIDO = LPG_INTERIM / 'PDF_ESCANEADO'  # escaneados recomprimidos para envio
LPG_MANIFESTO = LPG_INTERIM / 'manifesto.csv'   # 1 linha por edital (ente, arquivo, modo, tokens)
LPG_LLM_RAW = LPG_INTERIM / 'llm_raw'           # JSON bruto por edital (cache/retomada)
LPG_GASTOS = LPG_INTERIM / 'gastos.csv'         # gasto real por chamada
LPG_BATCHES = LPG_INTERIM / 'batches.csv'       # batches enviados
LPG_OUTPUT = FINAL_DATA_PATH / 'lpg_editais.xlsx'

# Endereço da pasta 'ações afirmativas' no SharePoint/OneDrive (sem barra no fim), para links absolutos
# na planilha de avaliação. Vazio = links relativos (../editais/...).
SHAREPOINT_PASTA_URL = 'https://culturagov-my.sharepoint.com/personal/gabriel_bizerril_cultura_gov_br/Documents/Projeto%20LPG/a%C3%A7%C3%B5es%20afirmativas'

MIN_CHARS_POR_PAGINA = 200  # abaixo disso o PDF é tratado como escaneado

# MODELO
MODEL_ID = 'claude-sonnet-5-5'
EFFORT = 'medium'
MAX_TOKENS = 8000
PROMPT_VERSION = 'lpg-v2'  # v1: piloto; v2: retificações completas = edital, PDFs com vários editais

# ORÇAMENTO (US$) - teto rígido somando todas as etapas
ORCAMENTO_USD = 40.0
PRECOS_USD_POR_MTOK = {  # preço padrão; o Batch API cobra 50%
    'claude-sonnet-5-5': {'input': 2.00, 'output': 10.00},
}
MULT_CACHE = {'escrita': 1.25, 'leitura': 0.10}  # sobre o preço de input
DESCONTO_BATCH = 0.5

# IN MinC nº 5/2023, art. 5º
COTA_MIN = {'negras': 0.20, 'indigenas': 0.10}  # caput: percentual mínimo de vagas por grupo
COTA_TOL = 1e-9  # tolerância para comparar floats (0.2 lido como 0.19999...)

# CONFORMIDADE IN 5 - CRITÉRIO AGREGADO (transform/conformidade_agregada.py; regras em notebooks/regras_conformidade_in5.md)
LPG_CONFORMIDADE_PARQUET = INTERIM_DATA_PATH / 'lpg_editais_conformidade.parquet'  # aba editais
LPG_EDITAIS_REVISADO_XLSX = FINAL_DATA_PATH / 'lpg_editais__2026-11-05_13-03.xlsx'  # planilha revisada
LPG_ABA_CATEGORIAS = 'categorias'  # uma linha por categoria: id, vagas, vagas_negras, vagas_indigenas...
# Regra E: valores de `edital_especifico_grupo` que tornam o edital específico de cada grupo
COTA_ESPECIFICO_GRUPO = {
    'negras': ['cultura afro-brasileira'],
    'indigenas': ['pessoas indígenas'],
}
# Início de `motivo_{g}` quando o pipeline calculou `vagas_cotas_{g}` a partir do percentual
# (não é evidência independente de reserva, então o número é ignorado)
COTA_MOTIVO_VAGAS_DERIVADAS = ('percentual', 'cotas não aplicadas')

# !!! AJUSTES MANUAIS PONTUAIS - NÃO SÃO REGRA !!!
# Correções caso a caso na aba `categorias`, decididas fora da extração (decisão de negócio).
# Cada item sobrescreve UMA célula, identificada por `id` + `nome` exato da categoria.
# São aplicadas antes da agregação (transform/conformidade_agregada.aplica_ajustes_manuais)
# e o edital fica marcado em `ajuste_manual_in5`. Não generalizar para outros editais.
COTA_AJUSTES_MANUAIS_CATEGORIAS = [
    {
        'id': '1723459b79dee085',
        'arquivo_pdf': '2023-92_CAP-CURITIBA_LPG.pdf',
        'nome': 'Inciso I - Modalidade 4 - Ações Afirmativas (curtas-metragens)',
        'coluna': 'vagas_negras',
        'valor': 2,
        'justificativa': 'Decisão de negócio: considerar 2 vagas para pessoas negras na '
                         'modalidade 4 do inciso I (total do edital passa de 17 para 19).',
    },
]

# !!! AJUSTES MANUAIS PONTUAIS - NÃO SÃO REGRA !!!
# Correções caso a caso na aba `editais` (decisão de negócio). Cada item sobrescreve UMA
# célula, identificada por `id` + `arquivo_pdf`, antes da avaliação
# (transform/conformidade_agregada.aplica_ajustes_manuais_editais). O edital fica marcado
# em `ajuste_manual_in5`. Não generalizar para outros editais.
COTA_AJUSTES_MANUAIS_EDITAIS = [
    {
        'id': '28df00d0663bbb8e',
        'arquivo_pdf': '2023-04_EST-AMAZONAS_LPG.pdf',
        'coluna': 'edital_especifico_grupo',
        'valor': 'cultura afro-brasileira',
        'justificativa': 'Decisão de negócio: edital específico para pessoas negras '
                         '(extração classificou como "Múltiplos grupos vulnerabilizados"). '
                         'Não precisa de cotas -> conforme pela regra E.',
    },
    {
        'id': 'eb34beb00c066ff5',
        'arquivo_pdf': '2023-20_EST-TOCANTINS_LPG.pdf',
        'coluna': 'edital_especifico_grupo',
        'valor': 'pessoas indígenas',
        'justificativa': 'Decisão de negócio: edital específico para pessoas indígenas '
                         '(extração classificou como "Povos e comunidades tradicionais"). '
                         'Conforme pela regra E.',
    },
    {
        'id': 'edadd8ac82bdcb1d',
        'arquivo_pdf': '2023-13_EST-BAHIA_LPG.pdf',
        'coluna': 'perc_cotas_negras',
        'valor': 0.2,
        'justificativa': 'Decisão de negócio: o edital prevê cota para pessoas negras, que a '
                         'extração não identificou. Vagas = arred(0,2 × 12) = 2.',
    },
    {
        'id': 'f6297ad186b35b62',
        'arquivo_pdf': '2023-16_EST-BAHIA_LPG.pdf',
        'coluna': 'perc_cotas_negras',
        'valor': 0.2,
        'justificativa': 'Decisão de negócio: o edital prevê cota para pessoas negras, que a '
                         'extração não identificou. Vagas = arred(0,2 × 20) = 4.',
    },
    {
        'id': None,  # edital inserido à mão, sem id: identificado só pelo arquivo
        'arquivo_pdf': '2024-06_EST-MARANHÃO_LPG.pdf',
        'coluna': 'vagas_totais',
        'valor': 81,
        'justificativa': 'Decisão de negócio: base de 81 vagas (e não 560). Mínimos: '
                         'arred(0,2 × 81) = 16 e arred(0,1 × 81) = 8.',
    },
    {
        # Vários campos de uma vez: use 'valores' (coluna -> valor) no lugar de 'coluna'/'valor'.
        'id': 'd5b3de457e36a28d',
        'arquivo_pdf': '2023-19_EST-ALAGOAS_LPG.pdf',
        'valores': {
            'perc_cotas_negras': 0.2,
            'vagas_cotas_negras': 8,       # arred(0,2 × 38) = 8
            'motivo_negras': 'retificação do edital: 20% das vagas',
            'perc_cotas_indigenas': 0.1,
            'vagas_cotas_indigenas': 4,    # arred(0,1 × 38) = 4
            'motivo_indigenas': 'retificação do edital: 10% das vagas',
            'status_in5': 'conforme',
            '2status_in5': 'conforme',
        },
        'justificativa': 'Decisão de negócio: retificação do edital passou a prever 20% para '
                         'pessoas negras e 10% para indígenas sobre 38 vagas (8 e 4 vagas).',
    },
]

# !!! AJUSTES MANUAIS PONTUAIS - NÃO SÃO REGRA !!!
# Editais cujo resultado final é DEFINIDO À MÃO (decisão de negócio), sem passar pelas regras.
# Aplicado no fim de transform/conformidade_agregada.aplica_conformidade; o motivo fica
# "AJUSTE MANUAL: <justificativa>" e o edital é marcado em `ajuste_manual_in5`.
COTA_AJUSTES_MANUAIS_STATUS = [
    {
        'id': '6bc279cea8cff4be',
        'arquivo_pdf': '2023-13_EST-PARANA_LPG.pdf',
        'status': 'conforme',
        'justificativa': 'decisão de negócio pontual (a extração não identificou vagas nem cotas).',
    },
]

# !!! AJUSTES MANUAIS PONTUAIS - NÃO SÃO REGRA !!!
# Editais em que a aba `categorias` é IGNORADA (decisão de negócio): valem a base e as vagas
# declaradas na aba `editais` (numero_vagas_categoria_total / vagas_totais e vagas_cotas_{g}).
# Aplicado em transform/conformidade_agregada.aplica_conformidade; o edital fica marcado em
# `ajuste_manual_in5`. Não generalizar para outros editais.
COTA_AJUSTES_MANUAIS_IGNORA_CATEGORIAS = [
    {
        'id': '8aac54822e3a2e38',
        'arquivo_pdf': '2023-08_EST-AMAZONAS_LPG.pdf',
        'justificativa': 'Decisão de negócio: valem as 60 vagas e as 12 vagas para pessoas negras '
                         'e 12 para indígenas declaradas no edital. A aba categorias soma 72 vagas '
                         '(mínimo 14), o que tornaria o edital nao_conforme.',
    },
]


# CONTROLE CONVERSAO
LOG_PATH = Path(INTERIM_DATA_PATH/'controle_conversao.csv')

# ARQUIVOS DO ÚLTIMO RESULTADO
CAPITAL_FILE_NAME: str = 'output_capitais_pt2.xlsx.xlsx'
ESTADO_FILE_NAME:str = 'estados_output.xlsx'
ESTADO_V2_FILE_NAME:str = 'estados_output_v2.xlsx'
ESTADO_SHEET_NAME: str = 'dados consolidados - não mexer'

# ESTADOS
RENAME_COLUNAS_ESTADO: dict = {
    'ESTADO': 'ente_federativo',
    'pdf':'nome_pdf_pk',
    'cotas_negras': 'perc_cotas_negras',
    'cotas_indigenas': 'perc_cotas_indigenas',
    'cotas_pcd': 'perc_cotas_pcd',
    'novo': 'is_novo'
}
COLUNAS_INTERESSE_ESTADO: list = ['ESTADO', 'pdf', 'cotas_negras', 'cotas_indigenas', 'cotas_pcd', 'vagas_totais','valor_total','novo']
MAP_ESTADOS_IBGE = {
    "ACRE": "12",
    "ALAGOAS": "27",
    "AMAPA": "16",
    "AMAZONAS": "13",
    "BAHIA": "29",
    "CEARA": "23",
    "DISTRITO FEDERAL": "53",
    "ESPIRITO SANTO": "32",
    "GOIAS": "52",
    "MARANHAO": "21",
    "MATO GROSSO": "51",
    "MATO GROSSO DO SUL": "50",
    "MINAS GERAIS": "31",
    "PARA": "15",
    "PARAIBA": "25",
    "PARANA": "41",
    "PERNAMBUCO": "26",
    "PIAUI": "22",
    "RIO DE JANEIRO": "33",
    "RIO GRANDE DO NORTE": "24",
    "RIO GRANDE DO SUL": "43",
    "RONDONIA": "11",
    "RORAIMA": "14",
    "SANTA CATARINA": "42",
    "SAO PAULO": "35",
    "SERGIPE": "28",
    "TOCANTINS": "17"
}


# CAPITAL
CAPITAL_COLUNAS_INTERESSE = ['uf', 'pdf', 'valor_total', 'cotas_negras', 'cotas_indigenas', 'cotas_pcd', 'vagas_totais', 'novo']
CAPITAL_RENAME_COLUNAS = {
    'uf' : 'ente_federativo',
    'pdf': 'nome_pdf_pk',
    'cotas_negras': 'perc_cotas_negras',
    'cotas_indigenas': 'perc_cotas_indigenas',
    'cotas_pcd': 'perc_cotas_pcd',
    'novo':'is_novo'
}
MAP_CAPITAIS_IBGE = {
    "ARACAJU": "2800308",
    "BELEM": "1501402",
    "BELO HORIZONTE": "3106200",
    "BOA VISTA": "1400100",
    "CAMPO GRANDE": "5002704",
    "CUIABA": "5103403",
    "CURITIBA": "4106902",
    "FLORIANOPOLIS": "4205407",
    "FORTALEZA": "2304400",
    "GOIANIA": "5208707",
    "JOAO PESSOA": "2507507",
    "MACAPA": "1600303",
    "MACEIO": "2704302",
    "MANAUS": "1302603",
    "NATAL": "2408102",
    "PALMAS": "1721000",
    "PORTO ALEGRE": "4314902",
    "PORTO VELHO": "1100205",
    "RECIFE": "2611606",
    "RIO BRANCO": "1200401",
    "SALVADOR": "2927408",
    "SAO LUIS": "2111300",
    "SAO PAULO (CAPITAL)": "3550308",
    "TERESINA": "2211001",
    "VITORIA": "3205309",
    "RIO DE JANEIRO (CAPITAL)": "3304557"
}


# DATA VIZ - PESSOAS NEGRAS
BINS_PESSOAS_NEGRAS    = [0.0, 0.2000000001, 0.25, 0.30, 1.0000001]
LABELS_PESSOAS_NEGRAS = [
    r"Menor ou igual a 20%",
    r"Maior ou igual a 21% e menor que 25%",
    r"Maior ou igual a 25% e menor que 30%",
    r"Maior ou igual a 30%"
]
COLORS_PESSOAS_NEGRAS  = [
    "#F2CECE", 
    "#D96D6D", 
    "#B22E2E", 
    "#511515"
]

# DATA VIZ - PESSOAS INDÍGENAS
# DATA VIZ - PESSOAS INDÍGENAS
BINS_PESSOAS_INDIGENAS = [
    0.0,
    0.0500000001,
    0.10,
    0.20,
    1.0000001
]

LABELS_PESSOAS_INDIGENAS = [
    r"Menor ou igual a 5%",
    r"Maior ou igual a 6% e menor que 10%",
    r"Maior ou igual a 10% e menor que 20%",
    r"Maior ou igual a 20%"
]

COLORS_PESSOAS_INDIGENAS = [
    "#DFF2E1",  # verde claro
    "#9ED9A5",  # verde médio claro
    "#4FAF64",  # verde médio escuro
    "#1F5C2E"   # verde escuro
]


# DATA VIZ - PESSOAS COM DEFICIÊNCIA (PCD)
# DATA VIZ - PESSOAS COM DEFICIÊNCIA (PCD)
BINS_PESSOAS_PCD = [
    0.0,
    0.0200000001,
    0.0400000001,
    0.0700000001,
    1.0000001
]

LABELS_PESSOAS_PCD = [
    r"Menor ou igual a 2%",
    r"Maior ou igual a 3% e menor que 4%",
    r"Maior ou igual a 5% e menor que 7%",
    r"Maior ou igual a 7%"
]

COLORS_PESSOAS_PCD = [
    "#D6E6F5",  # azul claro
    "#8BBCE6",  # azul médio claro
    "#3B82C4",  # azul médio escuro
    "#0F2F4F"   # azul escuro
]



# CENSO DEMOGRÁFICO
RENAME_COLUMNS_CENSO = {
   'Unidade da Federação e Município': 'nome_ente',
   'Total': 'pop_total',
   'Branca': 'pop_branca',
   'Preta': 'pop_preta',
   'Amarela': 'pop_amarela',
   'Parda': 'pop_parda',
   'Indígena': 'pop_indigena'
}

COLS_POP = [
    "pop_branca",
    "pop_preta",
    "pop_amarela",
    "pop_parda",
    "pop_indigena",
    "pop_pcd",
    "pop_pessoas_negras",
]

COLS_NUM = COLS_POP + ["pop_total"]