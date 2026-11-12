import pandas as pd
import numpy as np
import math
import re
import unicodedata

from config import settings

def padronizar_percentual(serie: pd.Series) -> pd.Series:
    def converter(valor):
        if pd.isna(valor):
            return np.nan

        valor_str = str(valor).strip()

        # Caso com %
        if "%" in valor_str:
            try:
                return float(valor_str.replace("%", "").replace(",", ".")) / 100
            except ValueError:
                return np.nan

        # Caso numérico
        try:
            num = float(valor_str.replace(",", "."))
        except ValueError:
            return np.nan

        # Se for maior que 1, interpretamos como percentual inteiro
        if num > 1:
            return num / 100

        # Caso contrário, já é fração
        return num

    return serie.apply(converter).astype(float)


def moeda_br_para_float(serie: pd.Series) -> pd.Series:
    def converter(valor):
        if pd.isna(valor):
            return np.nan

        # Se já for número, retorna direto
        if isinstance(valor, (int, float)):
            return float(valor)

        valor_str = str(valor).strip()

        if valor_str == "":
            return np.nan

        # Remove símbolos (R$, espaços etc.)
        valor_str = re.sub(r"[^\d,\.]", "", valor_str)

        # Caso típico BR: tem vírgula decimal
        if "," in valor_str:
            valor_str = valor_str.replace(".", "")
            valor_str = valor_str.replace(",", ".")
            return float(valor_str)

        # Caso sem vírgula:
        # assume que já está no padrão correto
        return float(valor_str)

    return serie.apply(converter)


def coluna_sim_para_bool(
    df: pd.DataFrame,
    col: str,
    valor_true: str = 'sim'
) -> pd.DataFrame:
    """
    Converte uma coluna textual (ex: 'sim' / 'não') em booleano.

    Regras:
    - valor_true (default='sim') → True
    - qualquer outro valor → False
    - ignora caixa, espaços e lida com NaN

    Retorna o próprio DataFrame (mutável).
    """
    df[col] = (
        df[col]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq(valor_true)
    )

    return df

def normalizar_texto(txt: str) -> str:
    if pd.isna(txt):
        return None

    txt = unicodedata.normalize("NFD", txt)
    txt = txt.encode("ascii", "ignore").decode("utf-8")
    txt = txt.upper()
    txt = re.sub(r"\s+", " ", txt).strip()

    return txt




# ---------------------------------------------------------------------------
# Números da IN MinC nº 5/2023
# ---------------------------------------------------------------------------

def arredonda_in5(x: float) -> int:
    """Arredondamento do §2º do art. 5º da IN 5: fração >= 0,5 arredonda para cima; < 0,5 para baixo.

    Não usar round()/np.round(), que arredondam 2,5 para 2 (arredondamento bancário).
    """
    return math.floor(x + 0.5 + settings.COTA_TOL)


def num(valor) -> float | None:
    """Converte um valor isolado para float; texto não numérico, vazio ou NaN vira None."""
    v = pd.to_numeric(valor, errors="coerce")
    return None if pd.isna(v) else float(v)
