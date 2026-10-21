"""Leitura e derivações do painel. Única fonte: data/final/lpg_editais.xlsx."""
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

PLANILHA = Path(__file__).resolve().parents[2] / "data" / "final" / "lpg_editais.xlsx"

STATUS = ["conforme", "nao_conforme", "especifico", "indeterminado", "sem_leitura"]
ROTULO_STATUS = {
    "conforme": "Conforme",
    "nao_conforme": "Não conforme",
    "especifico": "Específico",
    "indeterminado": "Indeterminado",
    "sem_leitura": "Sem leitura",
}
TIPOS = {"ESTADO": "Estados e DF", "CAPITAL": "Capitais"}
GRUPOS = {"in5": "Negros e indígenas", "negras": "Pessoas negras", "indigenas": "Pessoas indígenas"}
MODALIDADES = {
    "fomento_execucao": "Fomento à execução",
    "premio": "Prêmio",
    "bolsa": "Bolsa",
    "subsidio": "Subsídio",
    "outro": "Outra",
}

# Entes federativos esperados (27 UFs e 26 capitais), só para mostrar quem não tem edital na base.
ESTADOS_ESPERADOS = [
    "Acre", "Alagoas", "Amapá", "Amazonas", "Bahia", "Ceará", "Distrito Federal", "Espírito Santo",
    "Goiás", "Maranhão", "Mato Grosso", "Mato Grosso do Sul", "Minas Gerais", "Pará", "Paraíba",
    "Paraná", "Pernambuco", "Piauí", "Rio de Janeiro", "Rio Grande do Norte", "Rio Grande do Sul",
    "Rondônia", "Roraima", "Santa Catarina", "São Paulo", "Sergipe", "Tocantins",
]
CAPITAIS_ESPERADAS = [
    "Aracaju", "Belém", "Belo Horizonte", "Boa Vista", "Campo Grande", "Cuiabá", "Curitiba",
    "Florianópolis", "Fortaleza", "Goiânia", "João Pessoa", "Macapá", "Maceió", "Manaus", "Natal",
    "Palmas", "Porto Alegre", "Porto Velho", "Recife", "Rio Branco", "Rio de Janeiro", "Salvador",
    "São Luis", "São Paulo", "Teresina", "Vitória",
]
ESPERADOS = {"ESTADO": ESTADOS_ESPERADOS, "CAPITAL": CAPITAIS_ESPERADAS}

# Resumo dos dispositivos da IN MinC nº 5/2023, art. 5º (texto do README do projeto).
DISPOSITIVOS = {
    "art. 5º": "No mínimo 20% das vagas para pessoas negras e 10% para pessoas indígenas.",
    "§2º": "Frações iguais ou maiores que 0,5 arredondam para cima; menores que 0,5, para baixo.",
    "§3º": "Edital dividido em categorias deve ter cotas em todas elas.",
    "§4º": "Categoria com uma única vaga pode ir à ampla concorrência, se o edital como um todo reservar 20% e 10%.",
}


def dispositivo(motivo: str) -> str | None:
    """Parágrafo da IN 5 que fundamenta um motivo gerado por transform/conformidade.py."""
    if not isinstance(motivo, str) or motivo.startswith("edital específico") or motivo.startswith("documento"):
        return None
    if "§4º" in motivo:
        return "§4º"
    if "§3º" in motivo or motivo.startswith(("abaixo do mínimo em", "sem reserva informada em")):
        return "§3º"
    return "art. 5º"


def ementa(motivo: str) -> str:
    """Motivo sem a remissão entre parênteses, que vira etiqueta."""
    if not isinstance(motivo, str):
        return ""
    return re.sub(r"\s*\((§\dº|ressalva §\dº)\)", "", motivo).strip()


def _status_grupo(df: pd.DataFrame, grupo: str) -> pd.Series:
    col = "status_in5" if grupo == "in5" else f"status_{grupo}"
    return df[col].fillna("sem_leitura")


def _motivo_grupo(df: pd.DataFrame, grupo: str) -> pd.Series:
    col = "motivo_in5" if grupo == "in5" else f"motivo_{grupo}"
    return df[col]


@lru_cache(maxsize=1)
def carrega() -> dict[str, pd.DataFrame]:
    abas = pd.read_excel(PLANILHA, sheet_name=None)
    ed = abas["editais"]
    ed["ente"] = ed["ente"].str.strip()
    ed["mes"] = ed["arquivo_pdf"].str[:7]
    return {"editais": ed, "categorias": abas["categorias"], "outras_cotas": abas["outras_cotas"],
            "evidencias": abas["evidencias"]}


def editais(grupo: str = "in5", modalidade: str = "todas", busca: str = "") -> pd.DataFrame:
    df = carrega()["editais"].copy()
    df["status"] = _status_grupo(df, grupo)
    df["motivo"] = _motivo_grupo(df, grupo)
    df.loc[df["status"] == "sem_leitura", "motivo"] = "extração truncada; edital não classificado"
    if modalidade == "outras":
        df = df[df["modalidade"].isin(["bolsa", "subsidio", "outro"]) | df["modalidade"].isna()]
    elif modalidade != "todas":
        df = df[df["modalidade"] == modalidade]
    if busca:
        b = busca.strip().lower()
        df = df[df["ente"].str.lower().str.contains(b, regex=False)
                | df["arquivo_pdf"].str.lower().str.contains(b, regex=False)
                | df["objeto"].fillna("").str.lower().str.contains(b, regex=False)]
    return df


def _motivo_dominante(sub: pd.DataFrame) -> tuple[str | None, str, int]:
    """Parágrafo e motivo mais frequentes entre os editais não conformes (ou indeterminados) do ente."""
    alvo = sub[sub["status"] == "nao_conforme"]
    if alvo.empty:
        alvo = sub[sub["status"] == "indeterminado"]
    if alvo.empty:
        return None, "", 0
    partes = alvo["motivo"].dropna().str.split(r" \| ").explode()
    resumo = partes.map(lambda m: (dispositivo(m), _tipo_motivo(m)))
    (par, texto), n = resumo.value_counts().index[0], int(resumo.value_counts().iloc[0])
    return par, texto, n


def _tipo_motivo(m: str) -> str:
    if m.startswith("abaixo do mínimo em"):
        return "categorias abaixo do mínimo"
    if m.startswith("sem reserva informada em"):
        return "categorias sem reserva informada"
    if m.startswith("total reservado"):
        return "total reservado abaixo do mínimo"
    if m.startswith("percentual"):
        return "percentual abaixo do mínimo"
    if "vagas reservadas de" in m:
        return "vagas reservadas abaixo do mínimo"
    if "total de vagas desconhecido" in m:
        return "total de vagas desconhecido"
    if m.startswith("nenhuma cota identificada"):
        return "sem cota identificada"
    return ementa(m)


def situacao(c: dict) -> tuple[str, str]:
    """Situação do ente a partir das contagens: (classe css, rótulo)."""
    if c["total"] == 0:
        return "vazio", "Sem editais"
    if c["nao_conforme"]:
        return "nao", f"{c['nao_conforme']} de {c['total']} não conformes"
    if c["indeterminado"] or c["sem_leitura"]:
        n = c["indeterminado"] + c["sem_leitura"]
        return "ind", f"Sem não conforme · {n} pendente{'s' if n > 1 else ''}"
    return "ok", "Cumpre"


def por_ente(df: pd.DataFrame, tipo: str, ordem: str = "alfabetica") -> list[dict]:
    sub = df[df["tipo_ente"] == tipo]
    linhas = []
    nomes = sorted(set(ESPERADOS[tipo]) | set(sub["ente"]), key=_chave)
    for nome in nomes:
        e = sub[sub["ente"] == nome]
        c = {s: int((e["status"] == s).sum()) for s in STATUS}
        c["total"] = len(e)
        par, texto, n = _motivo_dominante(e) if len(e) else (None, "", 0)
        cls, rot = situacao(c)
        linhas.append({"ente": nome, "tipo": tipo, "contagem": c, "dispositivo": par, "motivo": texto,
                       "n_motivo": n, "classe": cls, "situacao": rot,
                       "na_base": nome in set(carrega()["editais"].query("tipo_ente == @tipo")["ente"])})
    if ordem == "situacao":
        grupo = {"nao": 0, "ind": 1, "ok": 2, "vazio": 3}
        linhas.sort(key=lambda l: (grupo[l["classe"]], _chave(l["ente"])))
    elif ordem == "editais":
        linhas.sort(key=lambda l: (-l["contagem"]["total"], _chave(l["ente"])))
    return linhas


def _chave(nome: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()


def resumo_tipo(df: pd.DataFrame, tipo: str, grupo: str) -> dict:
    sub = df[df["tipo_ente"] == tipo]
    entes = por_ente(df, tipo)
    com_editais = [l for l in entes if l["contagem"]["total"]]
    out = {s: int((sub["status"] == s).sum()) for s in STATUS}
    out["editais"] = len(sub)
    out["entes_base"] = len(com_editais)
    out["entes_esperados"] = len(ESPERADOS[tipo])
    out["entes_sem_nc"] = sum(1 for l in com_editais if not l["contagem"]["nao_conforme"])
    out["ausentes"] = [l["ente"] for l in entes if not l["na_base"]]
    out["reserva"] = reserva(sub)
    return out


def reserva(sub: pd.DataFrame) -> dict:
    """Percentual agregado de vagas reservadas, só sobre editais com vagas totais e reservadas informadas."""
    out = {}
    for g in ("negras", "indigenas"):
        base = sub.dropna(subset=["vagas_totais", f"vagas_cotas_{g}"])
        base = base[base["vagas_totais"] > 0]
        tot = base["vagas_totais"].sum()
        out[g] = {"perc": (base[f"vagas_cotas_{g}"].sum() / tot) if tot else None,
                  "vagas": int(base[f"vagas_cotas_{g}"].sum()), "base": int(tot), "editais": len(base)}
        vb = sub.dropna(subset=["valor_total", f"valor_cotas_{g}"])
        vt = vb["valor_total"].sum()
        out[g]["valor_perc"] = (vb[f"valor_cotas_{g}"].sum() / vt) if vt else None
        out[g]["valor"] = float(vb[f"valor_cotas_{g}"].sum())
    return out


# Rampa fixa de magnitude do valor total (R$), do atlas: tamanho do ponto lê a ordem de grandeza.
RAMPA_VALOR = [(500_000, 1, "até R$ 500 mil"), (2_000_000, 2, "até R$ 2 mi"),
               (10_000_000, 3, "até R$ 10 mi"), (float("inf"), 4, "acima de R$ 10 mi")]


def magnitude(valor: float) -> tuple[int, str]:
    if pd.isna(valor):
        return 0, "valor não informado"
    for teto, m, rot in RAMPA_VALOR:
        if valor <= teto:
            return m, rot
    return 4, RAMPA_VALOR[-1][2]


def edital(id_: str) -> dict | None:
    b = carrega()
    e = b["editais"][b["editais"]["id"] == id_]
    if e.empty:
        return None
    return {
        "linha": e.iloc[0],
        "categorias": b["categorias"][b["categorias"]["id"] == id_],
        "outras_cotas": b["outras_cotas"][b["outras_cotas"]["id"] == id_],
        "evidencias": b["evidencias"][b["evidencias"]["id"] == id_].sort_values("pagina"),
    }


GRUPOS_OUTRAS = {
    "pcd": "Pessoas com deficiência", "mulheres": "Mulheres", "lgbtqia": "LGBTQIA+",
    "quilombolas": "Quilombolas", "territorio": "Território", "pessoas_idosas": "Pessoas idosas",
    "povos_tradicionais": "Povos tradicionais", "outro": "Outros grupos",
}


def outras_cotas_por_tipo() -> pd.DataFrame:
    b = carrega()
    oc = b["outras_cotas"].drop_duplicates(["id", "grupo_padrao"])
    tot = b["editais"].groupby("tipo_ente").size()
    t = oc.groupby(["grupo_padrao", "tipo_ente"]).size().unstack(fill_value=0)
    t = t.reindex(columns=["ESTADO", "CAPITAL"], fill_value=0)
    for tipo in ("ESTADO", "CAPITAL"):
        t[f"perc_{tipo}"] = t[tipo] / tot[tipo]
    t["total"] = t["ESTADO"] + t["CAPITAL"]
    return t.sort_values("total", ascending=False)


def brl(v: float, curto: bool = False) -> str:
    if v is None or pd.isna(v):
        return "—"
    if curto:
        if v >= 1e9:
            return f"R$ {v / 1e9:.1f} bi".replace(".", ",")
        if v >= 1e6:
            return f"R$ {v / 1e6:.1f} mi".replace(".", ",")
        if v >= 1e3:
            return f"R$ {v / 1e3:.0f} mil"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def pct(v: float | None, casas: int = 1) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v * 100:.{casas}f}%".replace(".", ",")


def inteiro(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{int(v):,}".replace(",", ".")


CAMPOS = {
    "objeto": "Objeto", "valor_total": "Valor total", "vagas_totais": "Vagas totais",
    "percentual_negras": "Percentual para pessoas negras", "percentual_indigenas": "Percentual para pessoas indígenas",
    "vagas_negras_total": "Vagas para pessoas negras", "vagas_indigenas_total": "Vagas para pessoas indígenas",
    "outras_cotas": "Outras cotas", "pontuacao_bonus": "Pontuação bônus", "cotas_por_categoria": "Cotas por categoria",
    "categorias": "Categorias", "edital_especifico_grupo": "Edital específico", "pcd": "Pessoas com deficiência",
}


def rotulo_campo(campo: str) -> str:
    return CAMPOS.get(campo, campo.replace("_", " ").replace(".", " ").capitalize())
