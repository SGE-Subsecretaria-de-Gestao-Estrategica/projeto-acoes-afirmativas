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
LPG_PASTAS_IGNORADAS = {'outros editais', 'PlanilhasPC'}
LPG_INTERIM = INTERIM_DATA_PATH / 'LPG'
LPG_MD_ROOT = LPG_INTERIM / 'MD'                # editais convertidos para Markdown
LPG_PDF_COMPRIMIDO = LPG_INTERIM / 'PDF_ESCANEADO'  # escaneados recomprimidos para envio
LPG_MANIFESTO = LPG_INTERIM / 'manifesto.csv'   # 1 linha por edital (ente, arquivo, modo, tokens)
LPG_LLM_RAW = LPG_INTERIM / 'llm_raw'           # JSON bruto por edital (cache/retomada)
LPG_GASTOS = LPG_INTERIM / 'gastos.csv'         # gasto real por chamada
LPG_BATCHES = LPG_INTERIM / 'batches.csv'       # batches enviados
LPG_OUTPUT = FINAL_DATA_PATH / 'lpg_editais.xlsx'

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
COTA_MIN = {'negras': 0.20, 'indigenas': 0.10}

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