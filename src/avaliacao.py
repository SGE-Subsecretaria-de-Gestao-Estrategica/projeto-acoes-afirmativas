"""Gabarito manual e F1 da extração.

1) gera_planilha_revisao(): uma linha por edital x campo, com o valor do modelo, a evidência
   e as colunas em branco para a revisão manual (modelo_correto S/N e valor_real).
2) calcula_f1(): lê a planilha revisada e calcula precisão, revocação e F1 por campo.
"""
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from config import settings
from dicionario_cotas import menciona

AMOSTRA = settings.LPG_INTERIM / "amostra_gabarito.csv"
REVISAO = settings.FINAL_DATA_PATH / "gabarito_revisao_lpg.xlsx"
F1_SAIDA = settings.FINAL_DATA_PATH / "f1_lpg.xlsx"

# (coluna na planilha final, campo da evidência, o que conferir no edital)
CAMPOS = [
    ("objeto", "objeto", "O objeto está correto? (não precisa ser literal)"),
    ("vagas_totais", "vagas_totais", "Total de vagas/projetos/prêmios do edital"),
    ("valor_total", "valor_total", "Valor total do edital, em reais"),
    ("possui_categorias", "categorias", "O edital é dividido em categorias/módulos/linhas com vagas próprias?"),
    ("n_categorias", "categorias", "Quantas categorias com vagas próprias"),
    ("cotas_por_categoria", "cotas_por_categoria", "As cotas valem em cada categoria? (sim / nao / nao_informado / sem_categorias)"),
    ("perc_cotas_negras", "percentual_negras", "Percentual de cota para pessoas negras, em decimal (0.2)"),
    ("perc_cotas_indigenas", "percentual_indigenas", "Percentual de cota para pessoas indígenas, em decimal (0.1)"),
    ("edital_especifico_grupo", "edital_especifico_grupo", "O edital inteiro é para um grupo? Qual?"),
    ("tem_cota_pcd", "pcd", "Há reserva de vagas (cota) para PcD? (bônus na nota não conta)"),
    ("tem_cota_lgbtqia", "lgbtqia", "Há reserva de vagas (cota) para LGBTQIA+?"),
    ("tem_cota_quilombolas", "quilombolas", "Há reserva de vagas (cota) para quilombolas?"),
    ("status_in5", None, "Classificação final: conforme / nao_conforme / indeterminado / especifico / nao_aplicavel"),
]
CAMPOS_SIM_NAO = {"possui_categorias", "tem_cota_pcd", "tem_cota_lgbtqia", "tem_cota_quilombolas"}
NULOS = {"", "nan", "none", "null", "false", "0", "sem_categorias", "nao_aplicavel"}


def _vazio(v, campo: str = "") -> bool:
    if campo in CAMPOS_SIM_NAO:  # positivo = "sim"
        return str(v).strip().lower() != "sim"
    return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip().lower() in NULOS


def _exibe(valor, campo: str):
    if pd.isna(valor):
        return ""
    if campo in CAMPOS_SIM_NAO:
        return "sim" if bool(valor) else "não"
    return valor


def _evidencia(evid: pd.DataFrame, edital_id: str, campo_ev: str | None) -> tuple[str, str]:
    if campo_ev is None:
        return "", ""
    ev = evid[evid["id"] == edital_id]
    if campo_ev in ("pcd", "lgbtqia", "quilombolas"):  # evidências de outras cotas: filtra pelo grupo
        ev = ev[(ev["campo"] == campo_ev) | ((ev["campo"] == "outras_cotas") & ev["trecho"].map(lambda t: menciona(str(t), campo_ev)))]
    else:
        ev = ev[ev["campo"] == campo_ev]
    if ev.empty:
        return "", ""
    r = ev.iloc[0]
    return str(r["trecho"]), "" if pd.isna(r["pagina"]) else str(int(r["pagina"]))


def gera_planilha_revisao(sobrescrever: bool = False) -> Path:
    if REVISAO.exists() and not sobrescrever:
        raise FileExistsError(f"{REVISAO} já existe (pode conter revisão manual). Use sobrescrever=True.")
    x = pd.read_excel(settings.LPG_OUTPUT, sheet_name=None)
    editais, evid = x["editais"], x["evidencias"]
    amostra = pd.read_csv(AMOSTRA, sep=";", dtype=str)
    sel = editais[editais["id"].isin(amostra["id"])].sort_values(["tipo_ente", "ente", "arquivo_pdf"])
    paths = amostra.set_index("id")["pdf_path"]

    linhas = []
    for n, (_, e) in enumerate(sel.iterrows(), start=1):
        for col, campo_ev, pergunta in CAMPOS:
            trecho, pagina = _evidencia(evid, e["id"], campo_ev)
            valor = e.get(col)
            linhas.append({
                "n": n, "id": e["id"], "tipo_ente": e["tipo_ente"], "ente": e["ente"], "arquivo_pdf": e["arquivo_pdf"],
                "campo": col, "o_que_conferir": pergunta,
                "valor_modelo": _exibe(valor, col),
                "evidencia_trecho": trecho, "evidencia_pagina": pagina,
                "modelo_correto": "", "valor_real": "", "comentario": "",
            })
    df = pd.DataFrame(linhas)

    instrucoes = pd.DataFrame({"Como revisar": [
        "1. Para cada edital (coluna n), abra o PDF pelo link da coluna arquivo_pdf.",
        "2. Em cada linha, compare valor_modelo com o edital. A evidência e a página ajudam a localizar.",
        "3. modelo_correto: S se o valor do modelo está certo (inclusive vazio, quando o edital realmente não traz a informação); N se está errado.",
        "4. valor_real: preencha só quando modelo_correto = N, com o valor correto. Se a informação não existe no edital, escreva 'nenhum'. Nos campos sim/não, escreva 'sim' ou 'não'.",
        "5. Percentuais em decimal (20% -> 0.2). Valores em reais como número (1234567.89).",
        "6. Cota = reserva de vagas. Pontuação extra/bônus para um grupo NÃO é cota.",
        "7. status_in5 é calculado pelo código a partir dos campos acima; marque N se a conclusão final estiver errada.",
        f"Amostra: {sel['id'].nunique()} editais sorteados (estratificados por ente), {len(df)} linhas.",
    ]})

    REVISAO.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(REVISAO, engine="openpyxl") as xw:
        instrucoes.to_excel(xw, sheet_name="instrucoes", index=False)
        df.to_excel(xw, sheet_name="revisao", index=False)
    _formata(df, paths)
    print(f"📝 {REVISAO} ({sel['id'].nunique()} editais, {len(df)} linhas)")
    return REVISAO


def _formata(df: pd.DataFrame, paths: pd.Series) -> None:
    wb = load_workbook(REVISAO)
    ws = wb["revisao"]
    cols = {c: i + 1 for i, c in enumerate(df.columns)}
    larguras = {"n": 5, "id": 10, "tipo_ente": 10, "ente": 16, "arquivo_pdf": 30, "campo": 22, "o_que_conferir": 45,
                "valor_modelo": 35, "evidencia_trecho": 60, "evidencia_pagina": 9, "modelo_correto": 10,
                "valor_real": 25, "comentario": 35}
    for c, w in larguras.items():
        ws.column_dimensions[ws.cell(1, cols[c]).column_letter].width = w
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = "H2"

    cinza, amarelo = PatternFill("solid", fgColor="EEEEEE"), PatternFill("solid", fgColor="FFF2CC")
    for r in range(2, ws.max_row + 1):
        par = int(ws.cell(r, cols["n"]).value) % 2 == 0
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(r, c)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if par:
                cell.fill = cinza
        for c in ("modelo_correto", "valor_real", "comentario"):
            ws.cell(r, cols[c]).fill = amarelo
        link = ws.cell(r, cols["arquivo_pdf"])
        link.hyperlink = str(Path(paths[ws.cell(r, cols["id"]).value]).resolve())
        link.font = Font(color="0563C1", underline="single")

    dv = DataValidation(type="list", formula1='"S,N"', allow_blank=True)
    ws.add_data_validation(dv)
    letra = ws.cell(1, cols["modelo_correto"]).column_letter
    dv.add(f"{letra}2:{letra}{ws.max_row}")
    ws.auto_filter.ref = ws.dimensions
    wb["instrucoes"].column_dimensions["A"].width = 140
    wb.save(REVISAO)


def calcula_f1() -> pd.DataFrame:
    """TP: modelo trouxe valor e está certo | FP: trouxe valor errado |
    FN: deixou de trazer (ou trouxe errado) um valor que existe | TN: vazio e de fato não existe."""
    df = pd.read_excel(REVISAO, sheet_name="revisao", dtype=str).fillna("")
    df["modelo_correto"] = df["modelo_correto"].str.strip().str.upper()
    revisado = df[df["modelo_correto"].isin(["S", "N"])]
    pendentes = (df["modelo_correto"] == "").sum()

    def classifica(r):
        tem_modelo = not _vazio(r["valor_modelo"], r["campo"])
        if r["modelo_correto"] == "S":
            return ("TP",) if tem_modelo else ("TN",)
        real_existe = not _vazio(r["valor_real"], r["campo"]) and r["valor_real"].strip().lower() != "nenhum"
        if tem_modelo:
            return ("FP", "FN") if real_existe else ("FP",)
        return ("FN",)

    contagem = []
    for _, r in revisado.iterrows():
        for t in classifica(r):
            contagem.append({"campo": r["campo"], "tipo": t})
    c = pd.DataFrame(contagem).pivot_table(index="campo", columns="tipo", aggfunc="size", fill_value=0)
    for t in ("TP", "FP", "FN", "TN"):
        if t not in c:
            c[t] = 0
    total = c[["TP", "FP", "FN", "TN"]].sum().rename("TOTAL")
    c = pd.concat([c, total.to_frame().T])
    c["precisao"] = c["TP"] / (c["TP"] + c["FP"])
    c["revocacao"] = c["TP"] / (c["TP"] + c["FN"])
    c["f1"] = 2 * c["precisao"] * c["revocacao"] / (c["precisao"] + c["revocacao"])
    acerto = revisado.groupby("campo")["modelo_correto"].apply(lambda s: (s == "S").mean())
    c["acuracia"] = acerto.reindex(c.index)
    c.loc["TOTAL", "acuracia"] = (revisado["modelo_correto"] == "S").mean()
    c = c[["TP", "FP", "FN", "TN", "precisao", "revocacao", "f1", "acuracia"]].round(3)

    c.to_excel(F1_SAIDA)
    print(f"Linhas revisadas: {len(revisado)} de {len(df)} ({pendentes} pendentes)")
    print(c.to_string())
    print(f"\n📊 {F1_SAIDA}")
    return c
