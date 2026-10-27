"""Relatório de cotas da LPG: respostas diretas sobre a IN 5, com recorte Todos / Estados e DF / Capitais.

Rodar a partir de src/:
    python relatorio_cotas.py      # gera relatorios/relatorio_cotas_lpg.html

Todo número é calculado aqui a partir de data/final/lpg_editais.xlsx; nada é digitado à mão.
"""
import base64
import unicodedata
from datetime import date
from html import escape
from pathlib import Path

import pandas as pd

from relatorio_exploratorio import GRUPOS_OUTRAS, ROT, STATUS, barras, brl, n, p, tipo_motivo
from transform.conformidade import _especifico_do_grupo

ROOT = Path(__file__).resolve().parents[1]
PLANILHA = ROOT / "data" / "final" / "lpg_editais.xlsx"
F1 = ROOT / "data" / "final" / "f1_lpg.xlsx"
EDITAIS_DIR = ROOT / "data" / "EDITAIS"
SAIDA = ROOT / "relatorios" / "relatorio_cotas_lpg.html"

# Editais fora do escopo da análise (definidos na revisão manual): seleções de OSC e um edital de evento.
FORA_DO_ESCOPO = [
    "2023-09_EST-ALAGOAS_LPG.pdf",
    "2023-02_EST-ESPIRITOSANTO_LPG.pdf", "2023-03_EST-ESPIRITOSANTO_LPG (2).pdf",
    "2023-03_EST-ESPIRITOSANTO_LPG.pdf", "2023-04_EST-ESPIRITOSANTO_LPG.pdf",
    "2023-05_EST-ESPIRITOSANTO_LPG.pdf", "2023-06_EST-ESPIRITOSANTO_LPG.pdf",
    "2025-01_EST-GOIAS_LPG.pdf",
]
ESCOPOS = {"todos": ("Todos", None), "estados": ("Estados e DF", "ESTADO"), "capitais": ("Capitais", "CAPITAL")}
GRUPOS = {"negras": "pessoas negras", "indigenas": "pessoas indígenas"}
MIN = {"negras": 0.20, "indigenas": 0.10}
SITUACAO_ENTE = {"cumpre": "Cumpre", "pendencia": "Cumpre com pendência", "nao_cumpre": "Não cumpre",
                 "sem_leitura": "Sem leitura", "sem_base": "Sem editais na base"}
GRAFIA = {"São Luis": "São Luís"}  # nome da pasta -> grafia correta na página
NENHUM_ED_SEM = "não cumprem para nenhum dos dois grupos"
NENHUM_ED = NENHUM_ED_SEM + " (entre eles, {pend} com pendência a revisar em algum grupo)"
AFIRMATIVAS = ["pcd", "lgbtqia", "quilombolas", "mulheres", "pessoas_idosas", "povos_tradicionais"]


# ---------------------------------------------------------------- dados

def carrega() -> dict:
    abas = pd.read_excel(PLANILHA, sheet_name=None)
    d = abas["editais"]
    d = d[~d["arquivo_pdf"].isin(FORA_DO_ESCOPO)].copy()
    d["ente"] = d["ente"].replace(GRAFIA)
    d["st"] = d["status_in5"].where(d["status_extracao"] == "ok").fillna("sem_leitura")
    d["vagas_base"] = d["vagas_totais"].fillna(d["numero_vagas_categoria_total"])

    # valor reservado por grupo: vagas de cota x valor médio da vaga; se faltar vaga, percentual x valor total;
    # edital específico do grupo: valor total inteiro (metodologia do README)
    for g in GRUPOS:
        est = d[f"valor_cotas_{g}"].copy()
        est = est.fillna(d[f"perc_cotas_{g}"] * d["valor_total"])
        espec = d.apply(lambda r: r["st"] == "especifico" and _especifico_do_grupo(
            {"edital_especifico_grupo": r["edital_especifico_grupo"]}, g), axis=1)
        est[espec] = d.loc[espec, "valor_total"]
        est[(d["st"] == "especifico") & ~espec] = 0.0
        d[f"valor_est_{g}"] = est
        d[f"espec_{g}"] = espec

    oc = abas["outras_cotas"]
    oc = oc[oc["id"].isin(d.loc[d["st"] != "sem_leitura", "id"])].merge(
        d[["id", "valor_total", "valor_por_vaga"]], on="id", how="left")
    oc["valor_est"] = (oc["vagas"] * oc["valor_por_vaga"]).fillna(oc["percentual"] * oc["valor_total"])
    oc = oc.sort_values("valor_est", ascending=False).drop_duplicates(["id", "grupo_padrao"])  # um por grupo/edital

    esperados = []
    for pasta, tipo in (("Estados", "ESTADO"), ("Capitais", "CAPITAL")):
        esperados += [{"tipo_ente": tipo, "ente": GRAFIA.get(e.name, e.name)} for e in sorted((EDITAIS_DIR / pasta).iterdir()) if e.is_dir()]
    f1 = None
    if F1.exists():
        t = pd.read_excel(F1, sheet_name="f1", index_col=0)
        f1 = t.loc["TOTAL"] if "TOTAL" in t.index else None
    return {"d": d, "oc": oc, "esperados": pd.DataFrame(esperados), "f1": f1}


def situacao_ente(st: pd.Series) -> str:
    if (st == "nao_conforme").any():
        return "nao_cumpre"
    if (st == "indeterminado").any():
        return "pendencia"
    if (st == "sem_leitura").all():
        return "sem_leitura"
    return "cumpre"


def situacao_grupo(st: pd.Series) -> str:
    """Situação do ente para um grupo: não cumpre se algum edital é não conforme para o grupo."""
    if (st == "nao_conforme").any():
        return "nao_cumpre"
    if (st == "indeterminado").any():
        return "pendencia"
    if st.isna().all():
        return "sem_leitura"
    return "cumpre"


def cotas_por_edital(d: pd.DataFrame) -> dict:
    """Cada edital pelas duas cotas: cumpre as duas, só uma, nenhuma, a revisar, específico ou sem leitura."""
    ok = {g: d[f"status_{g}"].isin(["conforme", "nao_aplicavel"]) for g in GRUPOS}
    nc = {g: d[f"status_{g}"] == "nao_conforme" for g in GRUPOS}
    aval = ~d["st"].isin(["especifico", "sem_leitura"])
    ind = aval & (d["status_negras"] == "indeterminado") | aval & (d["status_indigenas"] == "indeterminado")
    c = {"ambos": aval & ok["negras"] & ok["indigenas"],
         "so_n": aval & ok["negras"] & nc["indigenas"], "so_i": aval & nc["negras"] & ok["indigenas"],
         "nenhum": aval & nc["negras"] & nc["indigenas"]}
    c = {k: int(v.sum()) for k, v in c.items()}
    c["parcial"] = c["so_n"] + c["so_i"]
    c["revisar"] = int(ind.sum())
    c["revisar_nc"] = int((ind & (nc["negras"] | nc["indigenas"])).sum())
    c["especifico"] = int((d["st"] == "especifico").sum())
    c["sem_leitura"] = int((d["st"] == "sem_leitura").sum())
    c["aval"], c["total"] = int(aval.sum()), len(d)
    return c


def por_ente(d: pd.DataFrame, esperados: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for (tipo, ente), g in d.groupby(["tipo_ente", "ente"]):
        r = {"tipo_ente": tipo, "ente": ente, "editais": len(g), "situacao": situacao_ente(g["st"])}
        r |= {f"sit_{gr}": situacao_grupo(g[f"status_{gr}"]) for gr in GRUPOS}
        r |= {s: int((g["st"] == s).sum()) for s in STATUS}
        for gr in GRUPOS:
            b = g.dropna(subset=["vagas_base", f"vagas_cotas_{gr}"])
            r[f"agr_{gr}"] = b[f"vagas_cotas_{gr}"].sum() / b["vagas_base"].sum() if b["vagas_base"].sum() else None
        r["agr_cumpre"] = (None if r["agr_negras"] is None or r["agr_indigenas"] is None
                           else r["agr_negras"] >= MIN["negras"] and r["agr_indigenas"] >= MIN["indigenas"])
        r["valor_total"] = g["valor_total"].sum()
        r["valor_cotas"] = g["valor_est_negras"].sum() + g["valor_est_indigenas"].sum()
        linhas.append(r)
    e = pd.DataFrame(linhas)
    faltam = esperados.merge(e[["tipo_ente", "ente"]], how="left", indicator=True)
    faltam = faltam[faltam["_merge"] == "left_only"].drop(columns="_merge").assign(situacao="sem_base", editais=0)
    out = pd.concat([e, faltam], ignore_index=True)
    for c in ["editais", *STATUS]:
        out[c] = out[c].fillna(0).astype(int)
    out["_ord"] = out["ente"].map(lambda e: unicodedata.normalize("NFD", e).encode("ascii", "ignore").decode().lower())
    return out.sort_values(["tipo_ente", "_ord"], ascending=[False, True]).drop(columns="_ord")


def analisa(base: dict, tipo: str | None) -> dict:
    d = base["d"] if tipo is None else base["d"][base["d"]["tipo_ente"] == tipo]
    esp = base["esperados"] if tipo is None else base["esperados"][base["esperados"]["tipo_ente"] == tipo]
    oc = base["oc"][base["oc"]["id"].isin(d["id"])]
    ent = por_ente(d, esp)
    na_base = ent[ent["situacao"] != "sem_base"]
    A = {"d": d, "ent": ent, "n_editais": len(d), "n_entes": len(na_base), "n_esperados": len(esp)}
    A["sit"] = na_base["situacao"].value_counts().to_dict()
    A["nao_cumpre"] = na_base[na_base["situacao"] == "nao_cumpre"]
    agr = na_base.dropna(subset=["agr_cumpre"])
    A["agr_n"], A["agr_cumpre"] = len(agr), int(agr["agr_cumpre"].astype(bool).sum())
    A["agr_so"] = {g: int((agr[f"agr_{g}"] >= MIN[g]).sum()) for g in GRUPOS}
    neg, ind = na_base["sit_negras"] == "cumpre", na_base["sit_indigenas"] == "cumpre"
    A["venn_ed"] = {"so_n": int((neg & ~ind).sum()), "ambos": int((neg & ind).sum()), "so_i": int((~neg & ind).sum()),
                    "nenhum": int((~neg & ~ind).sum()), "total": len(na_base), "n": int(neg.sum()), "i": int(ind.sum()),
                    "pend": int(((na_base["sit_negras"] == "pendencia") | (na_base["sit_indigenas"] == "pendencia")).sum())}
    an, ai = agr["agr_negras"] >= MIN["negras"], agr["agr_indigenas"] >= MIN["indigenas"]
    A["venn_agr"] = {"so_n": int((an & ~ai).sum()), "ambos": int((an & ai).sum()), "so_i": int((~an & ai).sum()),
                     "nenhum": int((~an & ~ai).sum()), "total": len(agr), "n": int(an.sum()), "i": int(ai.sum())}
    A["ambos"] = int(((na_base["situacao"] == "cumpre") & na_base["agr_cumpre"].fillna(False).astype(bool)).sum())
    A["st_editais"] = d["st"].value_counts().to_dict()
    A["ed_cotas"] = cotas_por_edital(d)

    lido = d[d["st"] != "sem_leitura"]
    A["valor_total"] = lido["valor_total"].sum()
    A["valor"] = {g: lido[f"valor_est_{g}"].sum() for g in GRUPOS}
    A["valor_espec"] = {g: lido.loc[lido[f"espec_{g}"], "valor_total"].sum() for g in GRUPOS}
    com_est = lido.dropna(subset=["valor_est_negras", "valor_total"])
    A["valor_cobertura"] = com_est["valor_total"].sum() / A["valor_total"] if A["valor_total"] else 0
    A["valor_base_est"] = com_est["valor_total"].sum()
    A["valor_espec_outros"] = lido.loc[(lido["st"] == "especifico") & ~lido["espec_negras"] & ~lido["espec_indigenas"],
                                       "valor_total"].sum()

    vb = lido.dropna(subset=["vagas_base", "vagas_cotas_negras", "vagas_cotas_indigenas"])
    A["vagas_base"], A["vagas_n"] = vb["vagas_base"].sum(), len(vb)
    A["vagas"] = {g: vb[f"vagas_cotas_{g}"].sum() for g in GRUPOS}
    A["vagas_sem_info"] = int(lido["vagas_base"].isna().sum())

    t = oc.groupby("grupo_padrao").agg(editais=("id", "nunique"), valor=("valor_est", "sum"),
                                       mediana=("percentual", "median"), com_valor=("valor_est", "count"))
    t["entes"] = oc.groupby("grupo_padrao")["ente"].nunique()
    t[["editais", "entes"]] = t[["editais", "entes"]].astype(int)
    A["oc"] = t.sort_values("editais", ascending=False)
    A["oc_editais"] = oc["id"].nunique()
    A["oc_valor_afirm"] = t.loc[t.index.isin(AFIRMATIVAS), "valor"].sum()
    A["n_lidos"] = len(lido)

    pn = lido["perc_cotas_negras"].dropna()
    A["piso"] = (int((pn.round(3) == 0.2).sum()), len(pn), int((pn > 0.2001).sum()))
    nc = lido[lido["st"] == "nao_conforme"].copy()
    nc["tipos"] = nc["motivo_in5"].map(tipo_motivo)
    A["motivos"] = {k: int(nc["tipos"].map(lambda s: k in s).sum()) for k in ("sem_cota", "sem_categoria", "categoria_abaixo", "calculo")}
    A["nc_n"] = len(nc)
    A["espec"] = lido[lido["st"] == "especifico"]
    A["bonus"] = lido["pontuacao_bonus"].notna().mean() if len(lido) else 0
    return A


# ---------------------------------------------------------------- composição

def barras_v(linhas, val="168px", val_m="132px", **kw) -> str:
    """barras() do relatório exploratório com coluna de valor de largura fixa por gráfico."""
    return barras(linhas, **kw).replace('style="--rot:', f'style="--val:{val};--val-m:{val_m};--rot:', 1)


def ent_sit_barra(A) -> str:
    """Barra única dos entes por situação (cumpre / pendência / não cumpre)."""
    ordem = [("cumpre", "ok"), ("pendencia", "ind"), ("nao_cumpre", "nc"), ("sem_leitura", "sl")]
    tot = sum(A["sit"].get(k, 0) for k, _ in ordem) or 1
    segs = "".join(f'<span class="seg seg-{c}" style="flex:{A["sit"][k]}" title="{SITUACAO_ENTE[k]}: {A["sit"][k]}">'
                   f'{A["sit"][k]}</span>' for k, c in ordem if A["sit"].get(k))
    desc = ", ".join(f'{A["sit"][k]} {SITUACAO_ENTE[k].lower()}' for k, _ in ordem if A["sit"].get(k))
    leg = "".join(f'<span class="leg leg-{c}">{SITUACAO_ENTE[k]}</span>' for k, c in ordem if A["sit"].get(k))
    return (f'<div class="faixa-seg" role="img" aria-label="Entes por situação: {desc}">{segs}</div>'
            f'<div class="legenda">{leg}</div>')


def editais_cotas(c: dict) -> str:
    """Barra de todos os editais pelas duas cotas, com a chave de contagens abaixo."""
    pc = lambda k: p(c[k] / c["aval"] if c["aval"] else 0, 0)
    itens = [("ambos", "ok", "Cumpre as duas cotas", f"{pc('ambos')} dos avaliados"),
             ("parcial", "parc", "Cumpre só uma", f"{c['so_n']} só para negros, {c['so_i']} só para indígenas"),
             ("nenhum", "nc", "Não cumpre nenhuma", f"{pc('nenhum')} dos avaliados"),
             ("revisar", "ind", "A revisar", (f"{c['revisar_nc']} já descumprem uma das cotas" if c["revisar_nc"] else "")),
             ("especifico", "esp", "Específico para um grupo", "fora da conta"),
             ("sem_leitura", "sl", "Sem leitura", "fora da conta")]
    itens = [i for i in itens if c[i[0]]]
    segs = "".join(f'<span class="seg seg-{cl}" style="flex:{c[k]}" title="{rot}: {c[k]}">{c[k]}</span>' for k, cl, rot, _ in itens)
    desc = ", ".join(f"{c[k]} {rot.lower()}" for k, _, rot, _ in itens)
    chave = "".join(f'<li class="leg leg-{cl}"><div><b>{c[k]}</b> {rot}<span>{det}</span></div></li>' for k, cl, rot, det in itens)
    return (f'<div class="faixa-seg faixa-ed" role="img" aria-label="{c["total"]} editais: {desc}">{segs}</div>'
            f'<ul class="chave-ed">{chave}</ul>')


def venn(v: dict, titulo: str, rotulo_nenhum: str) -> str:
    """Dois círculos (pessoas negras, pessoas indígenas); áreas fixas, contagens nas regiões."""
    desc = (f"{titulo}: {v['n']} entes cumprem para pessoas negras, {v['i']} para pessoas indígenas, "
            f"{v['ambos']} para os dois e {v['nenhum']} para nenhum, de {v['total']}")
    return f"""<figure class="venn">
<svg viewBox="0 0 380 236" role="img" aria-label="{desc}">
  <text x="112" y="18" class="v-tit" text-anchor="middle">Pessoas negras · {v['n']}</text>
  <text x="268" y="18" class="v-tit" text-anchor="middle">Pessoas indígenas · {v['i']}</text>
  <circle cx="148" cy="122" r="88" class="v-c"/><circle cx="232" cy="122" r="88" class="v-c"/>
  <text x="104" y="130" class="v-n" text-anchor="middle">{v['so_n']}</text>
  <text x="190" y="130" class="v-n v-ambos" text-anchor="middle">{v['ambos']}</text>
  <text x="276" y="130" class="v-n" text-anchor="middle">{v['so_i']}</text>
  <text x="104" y="150" class="v-r" text-anchor="middle">só negros</text>
  <text x="190" y="150" class="v-r" text-anchor="middle">os dois</text>
  <text x="276" y="150" class="v-r" text-anchor="middle">só indígenas</text>
</svg>
<figcaption><b>{titulo}.</b> {v['nenhum']} de {v['total']} entes {rotulo_nenhum}.</figcaption>
</figure>"""


def medidor(rot, valor, minimo, escala=0.4, nota="") -> str:
    w, m = min(valor / escala, 1) * 100, minimo / escala * 100
    return (f'<div class="med-l"><span class="med-rot">{rot}</span>'
            f'<span class="med" role="img" aria-label="{rot}: {p(valor)}, mínimo da IN 5 {p(minimo, 0)}">'
            f'<span class="med-fill" style="width:{w:.2f}%"></span>'
            f'<span class="med-min" style="left:{m:.2f}%"><span>mín. {p(minimo, 0)}</span></span></span>'
            f'<span class="med-v"><b>{p(valor)}</b> {nota}</span></div>')


def resposta(num, pergunta, resposta_html, corpo, limite) -> str:
    return f"""
<section class="resp" id="{{esc}}-r{num}" aria-labelledby="{{esc}}-r{num}-t">
  <div class="num" aria-hidden="true">{num}</div>
  <div class="corpo">
    <h2 id="{{esc}}-r{num}-t"><span class="so-leitor">Pergunta {num}. </span>{pergunta}</h2>
    <p class="ementa">{resposta_html}</p>
    {corpo}
    <p class="limite"><b>Limite.</b> {limite}</p>
  </div>
</section>"""


def selo(sit: str) -> str:
    return f'<span class="selo selo-{sit}">{SITUACAO_ENTE[sit]}</span>'


def tabela_entes(A) -> str:
    linhas, tipo_atual = [], None
    for r in A["ent"].itertuples():
        if r.tipo_ente != tipo_atual:
            tipo_atual = r.tipo_ente
            rot = "Estados e DF" if tipo_atual == "ESTADO" else "Capitais"
            linhas.append(f'<tr class="grupo"><th colspan="7" scope="colgroup">{rot}</th></tr>')
        if r.situacao == "sem_base":
            linhas.append(f'<tr class="sem-base"><th scope="row">{escape(r.ente)}</th><td data-rot="Editais">0</td>'
                          f'<td data-rot="Por edital" class="sit" colspan="5"><span>{selo("sem_base")}</span></td></tr>')
            continue
        detalhe = []
        if r.nao_conforme:
            detalhe.append(f"{r.nao_conforme} não conforme{'s' if r.nao_conforme > 1 else ''}")
        if r.indeterminado:
            detalhe.append(f"{r.indeterminado} indeterminado{'s' if r.indeterminado > 1 else ''}")
        if r.especifico:
            detalhe.append(f"{r.especifico} específico{'s' if r.especifico > 1 else ''}")
        det = f'<span class="det">{", ".join(detalhe)}</span>' if detalhe else ""
        pct = lambda v, m: ('<span class="vazio">sem dado</span>' if pd.isna(v)
                            else f'<span class="{"" if v >= m else "abaixo"}">{p(v, 2 if abs(v - m) < .001 else 1)}</span>')
        agr = ('<span class="vazio">sem dado</span>' if pd.isna(r.agr_cumpre)
               else ('<span class="agr agr-ok">atinge</span>' if r.agr_cumpre else '<span class="agr agr-nc">não atinge</span>'))
        linhas.append(
            f'<tr><th scope="row">{escape(r.ente)}</th><td data-rot="Editais">{r.editais}</td>'
            f'<td data-rot="Por edital" class="sit"><span>{selo(r.situacao)}{det}</span></td>'
            f'<td data-rot="Negros (agregado)">{pct(r.agr_negras, MIN["negras"])}</td>'
            f'<td data-rot="Indígenas (agregado)">{pct(r.agr_indigenas, MIN["indigenas"])}</td>'
            f'<td data-rot="20% e 10%">{agr}</td>'
            f'<td data-rot="Valor p/ cotas">{brl(r.valor_cotas) if r.valor_cotas else "–"}</td></tr>')
    return f"""<div class="rola"><table class="entes">
<caption class="so-leitor">Situação de cada ente nos dois critérios</caption>
<thead><tr><th scope="col">Ente</th><th scope="col">Editais</th><th scope="col">Por edital</th>
<th scope="col">Negros<br><span>vagas, agregado</span></th><th scope="col">Indígenas<br><span>vagas, agregado</span></th>
<th scope="col">20% e 10%<br><span>agregado</span></th><th scope="col">Valor p/ cotas<br><span>estimado</span></th></tr></thead>
<tbody>{"".join(linhas)}</tbody></table></div>"""


def monta_escopo(esc: str, A: dict) -> str:
    sit = A["sit"]
    cumpre, pend, nc = sit.get("cumpre", 0), sit.get("pendencia", 0), sit.get("nao_cumpre", 0)
    ne, vt = A["n_entes"], A["valor_total"]
    vn, vi = A["valor"]["negras"], A["valor"]["indigenas"]
    gn, gi, gb = A["vagas"]["negras"], A["vagas"]["indigenas"], A["vagas_base"]
    oc = A["oc"]
    afirm = oc[oc.index.isin(AFIRMATIVAS)]
    st_ed = A["st_editais"]
    ed_aval = sum(st_ed.get(s, 0) for s in ("conforme", "nao_conforme", "indeterminado", "especifico"))
    nc_ed = st_ed.get("nao_conforme", 0)
    resp = []

    # 1. entes
    lista_nc = ", ".join(f"{escape(r.ente)} ({r.nao_conforme} de {r.editais})" for r in A["nao_cumpre"].itertuples())
    resp.append(resposta(
        1, "Quantos entes cumprem a IN 5?",
        f"<b class='n'>{A['venn_ed']['n']}</b> entes cumprem para pessoas negras, <b class='n'>{A['venn_ed']['i']}</b> "
        f"para pessoas indígenas e <b class='n'>{A['venn_ed']['ambos']} de {ne}</b> para os dois, isto é, não têm "
        f"nenhum edital não conforme"
        + (f", e outros {pend} só têm pendências a revisar" if pend else "")
        + f". Pelo agregado das vagas, <b class='n'>{A['agr_cumpre']} de {A['agr_n']}</b> reservam ao todo 20% para "
          f"pessoas negras e 10% para indígenas.",
        f"""<h3 class="sub">Edital por edital</h3>
{editais_cotas(A['ed_cotas'])}
<p class="nota">Dos {A['ed_cotas']['aval']} editais avaliados, {A['ed_cotas']['ambos']} cumprem as duas cotas da IN 5, {A['ed_cotas']['parcial']} cumprem só uma e {A['ed_cotas']['nenhum']} não cumprem nenhuma. Cumprir uma cota é reservar o mínimo para o grupo em todas as categorias, com o arredondamento do §2º e a exceção do §4º.</p>
<h3 class="sub sub-sep">Ente por ente, por grupo</h3>
<div class="vennes">{venn(A['venn_ed'], 'Por edital', NENHUM_ED.format(pend=A['venn_ed']['pend']) if A['venn_ed']['pend'] else NENHUM_ED_SEM)}
{venn(A['venn_agr'], 'Pelo agregado', 'não atingem o mínimo agregado para nenhum dos grupos')}</div>
<p class="nota">Por edital, o ente cumpre para um grupo quando nenhum dos seus editais é não conforme para esse grupo. Pelo agregado, quando a soma das vagas reservadas ao grupo chega a 20% (negros) ou 10% (indígenas) das vagas do ente. Os círculos não são proporcionais.</p>
<div class="dois">
  <div><h3 class="sub">Por edital</h3>{ent_sit_barra(A)}
    <p class="nota">O ente cumpre quando nenhum dos seus editais é não conforme. No total, {nc_ed} dos {ed_aval} editais avaliados ({p(nc_ed / ed_aval if ed_aval else 0)}) são não conformes.</p></div>
  <div><h3 class="sub">Pelo agregado (metodologia do README)</h3>
    <div class="faixa-seg" role="img" aria-label="{A['agr_cumpre']} entes atingem e {A['agr_n'] - A['agr_cumpre']} não atingem o agregado">
      <span class="seg seg-ok" style="flex:{A['agr_cumpre']}">{A['agr_cumpre']}</span><span class="seg seg-nc" style="flex:{A['agr_n'] - A['agr_cumpre']}">{A['agr_n'] - A['agr_cumpre']}</span></div>
    <div class="legenda"><span class="leg leg-ok">Atinge 20% e 10%</span><span class="leg leg-nc">Não atinge</span></div>
    <p class="nota">Soma das vagas reservadas do ente ÷ soma das vagas. {A['agr_so']['negras']} entes atingem 20% para pessoas negras, e {A['agr_so']['indigenas']} atingem 10% para pessoas indígenas. {A['ambos']} entes cumprem pelos dois critérios.</p></div>
</div>
<details class="lista"><summary>Entes com ao menos um edital não conforme ({nc})</summary><p>{lista_nc or "Nenhum."}</p></details>""",
        f"O critério por edital é rigoroso: um único edital não conforme tira o ente. O agregado pode ficar abaixo do "
        f"mínimo só pelo arredondamento do §2º em categorias pequenas, sem descumprimento. Por isso os dois aparecem "
        f"lado a lado, e a tabela por ente traz os dois."))

    # 2. recursos
    esp_txt = (f" Inclui {brl(A['valor_espec']['negras'] + A['valor_espec']['indigenas'])} de editais específicos "
               f"para esses grupos." if A['valor_espec']['negras'] + A['valor_espec']['indigenas'] else "")
    resp.append(resposta(
        2, "Quanto de recurso foi para as cotas?",
        f"<b class='n'>{brl(vn + vi)}</b>, cerca de {p((vn + vi) / vt if vt else 0)} dos {brl(vt)} dos editais: "
        f"{brl(vn)} para pessoas negras e {brl(vi)} para pessoas indígenas.",
        barras_v([("Pessoas negras", vn, "f-tinta", p(vn / vt if vt else 0)),
                ("Pessoas indígenas", vi, "f-tinta", p(vi / vt if vt else 0)),
                ("Demais vagas (ampla concorrência e outras cotas)", max(vt - vn - vi, 0), "f-fio",
                 p(max(vt - vn - vi, 0) / vt if vt else 0))], fmt=brl, rot_w=300)
        + (f'<p class="nota">{esp_txt.strip()}</p>' if esp_txt else ""),
        f"É uma estimativa: vagas reservadas × valor médio da vaga de cada edital (ou percentual × valor total, quando "
        f"o edital não informa vagas). Cobre {p(A['valor_cobertura'], 0)} do valor dos editais; o restante não tem "
        f"cota nem percentual identificados. Edital específico conta com o valor inteiro para o grupo."))

    # 3. vagas
    resp.append(resposta(
        3, "Quantas vagas foram para as cotas?",
        f"<b class='n'>{n(gn + gi)}</b> das {n(gb)} vagas ({p((gn + gi) / gb if gb else 0)}): {n(gn)} para pessoas "
        f"negras e {n(gi)} para pessoas indígenas.",
        '<div class="meds">' + medidor("Pessoas negras", gn / gb if gb else 0, MIN["negras"], nota=f"{n(gn)} vagas")
        + medidor("Pessoas indígenas", gi / gb if gb else 0, MIN["indigenas"], nota=f"{n(gi)} vagas") + "</div>"
        + '<p class="nota">O agregado passa do mínimo porque o arredondamento do §2º, aplicado categoria a '
          'categoria, empurra as reservas para cima nas categorias pequenas.</p>',
        f"Soma de {A['vagas_n']} editais com total de vagas e vagas reservadas informados ou calculáveis; "
        f"{A['vagas_sem_info']} editais não informam o número de vagas e ficam fora desta conta."))

    # 4. valor outras cotas
    lin4 = [(GRUPOS_OUTRAS.get(g, g), r.valor, "f-tinta", f"{int(r.editais)} editais") for g, r in afirm.sort_values("valor", ascending=False).iterrows()]
    terr = oc.loc[oc.index.isin(["territorio", "outro"]), "valor"].sum()
    resp.append(resposta(
        4, "Quanto de recurso vai para outras cotas?",
        f"<b class='n'>{brl(A['oc_valor_afirm'])}</b> em cotas para outros grupos sociais, "
        f"{p(A['oc_valor_afirm'] / vt if vt else 0)} do valor dos editais"
        + (f"; mulheres respondem por {brl(afirm.loc['mulheres', 'valor'])}" if "mulheres" in afirm.index else "") + ".",
        (barras_v(lin4, fmt=brl, rot_w=200) if lin4 else "<p class='nota'>Nenhuma outra cota neste recorte.</p>")
        + (f'<p class="nota">Fora dessa soma: {brl(terr)} em reservas territoriais (interior, regiões) e outros '
           f'critérios, que não são ações afirmativas para grupos sociais.</p>' if terr else ""),
        "Estimativa pelo percentual da cota × valor total do edital (ou vagas × valor médio da vaga). Os percentuais "
        "de grupos diferentes podem se sobrepor, porque uma pessoa pode pertencer a mais de um grupo."))

    # 5. principais outras cotas
    rows = "".join(
        f'<tr><th scope="row">{GRUPOS_OUTRAS.get(g, g)}</th><td data-rot="Editais">{int(r.editais)}</td>'
        f'<td data-rot="Entes">{int(r.entes)}</td><td data-rot="% mediano">{p(r.mediana, 0) if pd.notna(r.mediana) else "–"}</td>'
        f'<td data-rot="Valor estimado">{brl(r.valor) if r.valor else "–"}</td></tr>'
        for g, r in oc.iterrows())
    top = afirm.index[:2].tolist()
    resp.append(resposta(
        5, "Quais são as principais outras cotas?",
        (f"<b class='n'>{GRUPOS_OUTRAS.get(top[0], top[0])}</b>"
         + (f" e <b class='n'>{GRUPOS_OUTRAS.get(top[1], top[1]).lower()}</b>" if len(top) > 1 else "")
         + f". {A['oc_editais']} dos {A['n_lidos']} editais ({p(A['oc_editais'] / A['n_lidos'] if A['n_lidos'] else 0)}) "
           f"preveem alguma cota além de pessoas negras e indígenas." if top else "Nenhuma outra cota neste recorte."),
        f"""<div class="rola"><table class="tab"><caption class="so-leitor">Outras cotas por grupo</caption>
<thead><tr><th scope="col">Grupo</th><th scope="col">Editais</th><th scope="col">Entes</th><th scope="col">% mediano</th><th scope="col">Valor estimado</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="nota">Pontuação extra para grupos, que não é reserva de vagas, aparece em {p(A['bonus'], 0)} dos editais.</p>""",
        "Território e “outros” reúnem critérios regionais e grupos de baixa frequência (mães solo, vulnerabilidade "
        "socioeconômica etc.); estão na tabela, mas fora da soma da resposta 4."))

    # extras
    piso, base_p, acima = A["piso"]
    esp = A["espec"]
    esp_l = "".join(f"<li><b>{escape(r.ente)}</b> {escape(str(r.edital_especifico_grupo))}"
                    f"<span>{brl(r.valor_total) if pd.notna(r.valor_total) else '–'}</span></li>" for r in esp.itertuples())
    mt = A["motivos"]
    extras = f"""
<section class="extras" id="{esc}-extras" aria-labelledby="{esc}-extras-t">
  <h2 class="bloco-t" id="{esc}-extras-t">Também vale saber</h2>
  <div class="ex-grade">
    <div><h3 class="sub">O mínimo virou o padrão</h3>
      <p><b class="n">{p(piso / base_p if base_p else 0, 0)}</b> dos {base_p} editais com percentual informado reservam exatamente 20% para pessoas negras; só {acima} vão além.</p></div>
    <div><h3 class="sub">Por que os editais não cumprem</h3>
      {barras_v([("Nenhuma cota identificada", mt["sem_cota"], "f-tinta", ""), ("Cota não aplicada por categoria (§3º)", mt["sem_categoria"], "f-tinta", ""),
               ("Categoria abaixo do mínimo", mt["categoria_abaixo"], "f-tinta", ""), ("Conta de vagas ou total", mt["calculo"], "f-tinta", "")], val="40px", val_m="40px", rot_w=230) if A["nc_n"] else "<p>Nenhum edital não conforme.</p>"}
      <p class="nota">Motivos nos {A["nc_n"]} editais não conformes; um edital pode ter mais de um.</p></div>
    <div class="ex-largo"><h3 class="sub">Editais específicos ({len(esp)})</h3>
      <p>Editais inteiros dirigidos a um grupo, que não entram na conta de conformidade.</p>
      {f'<ul class="esp-l">{esp_l}</ul>' if len(esp) else ""}</div>
  </div>
</section>"""

    tabela = f"""
<section class="por-ente" id="{esc}-entes" aria-labelledby="{esc}-entes-t">
  <h2 class="bloco-t" id="{esc}-entes-t">Ente por ente</h2>
  <p class="nota">Em ordem alfabética. Percentuais abaixo do mínimo aparecem em tom de alerta, sem que isso signifique, por si só, descumprimento.</p>
  {tabela_entes(A)}
</section>"""

    regua = [
        (1, "Entes que cumprem a IN 5", f"{cumpre} de {ne} <small>por edital</small> · {A['agr_cumpre']} de {A['agr_n']} <small>agregado</small>"),
        (2, "Recurso para as cotas", f"{brl(vn + vi)} <small>{p((vn + vi) / vt if vt else 0)} do valor</small>"),
        (3, "Vagas para as cotas", f"{n(gn + gi)} <small>{p((gn + gi) / gb if gb else 0)} das vagas</small>"),
        (4, "Recurso para outras cotas", f"{brl(A['oc_valor_afirm'])}"),
        (5, "Principais outras cotas", ", ".join(GRUPOS_OUTRAS.get(g, g) for g in top) or "–"),
    ]
    regua_html = "".join(f'<li><a href="#{esc}-r{i}"><span class="rn">{i}</span><span class="rp">{t}</span>'
                         f'<span class="rl" aria-hidden="true"></span><span class="rv">{v}</span></a></li>' for i, t, v in regua)
    corpo = "".join(r.replace("{esc}", esc) for r in resp)
    rot = ESCOPOS[esc][0]
    return f"""
<div class="escopo" data-escopo="{esc}" {"" if esc == "todos" else "hidden"}>
  <section class="abertura" aria-label="Respostas em resumo, {rot}">
    <p class="base">{rot}: {A['n_editais']} editais de {ne} entes ({A['n_esperados'] - ne} sem editais na base).</p>
    <ol class="regua">{regua_html}</ol>
  </section>
  <main class="coluna">{corpo}{extras}{tabela}</main>
</div>"""


def monta(B: dict) -> str:
    blocos = "".join(monta_escopo(esc, analisa(B, tipo)) for esc, (_, tipo) in ESCOPOS.items())
    d = B["d"]
    f1 = B["f1"]
    qual = (f"Numa amostra de 77 editais revisados manualmente, a extração acertou {p(f1['acuracia'])} dos campos "
            f"(F1 de {p(f1['f1'])})." if f1 is not None else "")
    sem_base = (B["esperados"].merge(d[["tipo_ente", "ente"]].drop_duplicates(), how="left", indicator=True)
                .query("_merge == 'left_only'")["ente"].tolist())
    sl = d[d["st"] == "sem_leitura"]["arquivo_pdf"].tolist()
    limites = [
        f"<b>Fora do escopo.</b> {len(FORA_DO_ESCOPO)} editais foram excluídos por não selecionarem projetos culturais "
        f"(seleções de OSC no Espírito Santo, um edital de Alagoas e um de evento em Goiás): "
        + ", ".join(f"<code>{escape(a)}</code>" for a in FORA_DO_ESCOPO) + ".",
        f"<b>Sem leitura.</b> {len(sl)} editais tiveram a extração interrompida e ficam fora das contas: "
        + ", ".join(f"<code>{escape(a)}</code>" for a in sl) + "." if sl else "",
        f"<b>Cobertura.</b> Sem editais na base: {', '.join(sem_base)}." if sem_base else "",
        "<b>Valores.</b> Os valores das cotas são estimados a partir do valor médio da vaga de cada edital; "
        "são valores previstos nos editais, não executados.",
        f"<b>Qualidade.</b> {qual} Os campos de vagas reservadas são os de menor acerto (cerca de 90%)." if qual else "",
    ]
    return PAGINA.format(
        fontes=fontes_embutidas(), hoje=date.today().strftime("%d/%m/%Y"), n=len(d), blocos=blocos,
        limites="".join(f"<li>{x}</li>" for x in limites if x),
        metodo=(f"Base: <code>data/final/lpg_editais.xlsx</code>. Extração com LLM e regras do art. 5º da IN MinC nº 5/2023 "
                f"aplicadas em código. Gerado em {date.today().strftime('%d/%m/%Y')} por <code>src/relatorio_cotas.py</code>; "
                f"todos os números são recalculados a cada execução."))


PAGINA = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cotas na LPG · Respostas</title>
<meta name="description" content="Respostas sobre o cumprimento das cotas da IN MinC nº 5/2023 nos editais da Lei Paulo Gustavo de estados, DF e capitais.">
<style>
{fontes}
:root {{
  --papel:#ffffff; --lavado:#f3f5f4; --lavado-2:#e9eeeb; --tinta:#16191d; --tinta-2:#444a52; --tinta-3:#5d636b;
  --fio:#dcdfe3; --fio-2:#edeff1; --fio-forte:#c9ced3; --verde:#1f5f45; --verde-2:#174a36; --verde-3:#e4efe9;
  --verde-txt:#dfece5; --ok:#1f5f45; --nc:#9e3a2b; --nc-lav:#f6ebe8; --esp:#3e6e8e; --esp-lav:#e8f0f5;
  --ind:#8c5a0e; --ind-cor:#c48a2a; --ind-lav:#f8f0e1; --parc:#dc9c8f; --sl:#8a9097;
  --sans:"Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --serif:"Source Serif 4",Georgia,"Times New Roman",serif;
  --larg:1120px; --med:28px; color-scheme:light;
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; -webkit-text-size-adjust:100%; }}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior:auto; }} }}
body {{ margin:0; background:var(--papel); color:var(--tinta); font:16px/1.6 var(--sans); font-variant-numeric:tabular-nums lining-nums; }}
::selection {{ background:#cfe3d8; }}
a {{ color:var(--verde); text-underline-offset:3px; text-decoration-thickness:1px; }}
:focus-visible {{ outline:2px solid var(--verde); outline-offset:2px; border-radius:2px; }}
h1,h2,h3,p,ul,ol,figure {{ margin:0; }}
code {{ font-size:.86em; background:var(--lavado); padding:1px 5px; border-radius:3px; word-break:break-word; }}
[hidden] {{ display:none !important; }}
.so-leitor {{ position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap; }}
.pular {{ position:absolute; left:-999px; top:8px; background:var(--tinta); color:#fff; padding:8px 12px; z-index:9; }}
.pular:focus {{ left:8px; }}
b.n {{ font-family:var(--sans); font-weight:600; font-size:1.18em; letter-spacing:-.01em; color:var(--tinta); }}

/* faixa */
.faixa {{ background:var(--verde); color:var(--verde-txt); }}
.faixa-in {{ max-width:var(--larg); margin:0 auto; padding:32px var(--med) 22px; }}
.faixa h1 {{ color:#fff; font-size:clamp(27px, 3.3vw, 40px); line-height:1.12; letter-spacing:-.015em; font-weight:700; max-width:28ch; text-wrap:balance; }}
.faixa .lead {{ font-family:var(--serif); font-size:18px; color:#e9f2ed; max-width:60ch; margin-top:10px; }}
.serie {{ font-size:13px; color:#c6dccf; display:flex; flex-wrap:wrap; gap:4px 18px; margin-top:14px; }}
.recorte-barra {{ position:sticky; top:0; z-index:20; background:var(--verde); border-bottom:1px solid var(--verde-2); }}
.recorte {{ max-width:var(--larg); margin:0 auto; display:flex; flex-wrap:wrap; align-items:center; gap:10px 14px; padding:12px var(--med); border-top:1px solid rgba(255,255,255,.16); }}
.recorte .rr {{ font-size:12px; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:#c6dccf; }}
.seg-grupo {{ display:inline-flex; border:1px solid rgba(255,255,255,.45); border-radius:3px; overflow:hidden; }}
.seg-grupo button {{ font:500 14px/1 var(--sans); color:#fff; background:transparent; border:0; padding:9px 14px; cursor:pointer; transition:background .15s; }}
.seg-grupo button + button {{ border-left:1px solid rgba(255,255,255,.45); }}
.seg-grupo button:hover {{ background:rgba(255,255,255,.12); }}
.seg-grupo button[aria-pressed="true"] {{ background:#fff; color:var(--verde-2); font-weight:600; }}
.seg-grupo button:focus-visible {{ outline:2px solid #fff; outline-offset:-4px; }}

/* abertura: régua de respostas */
.abertura {{ max-width:var(--larg); margin:0 auto; padding:26px var(--med) 30px; border-bottom:2px solid var(--tinta); }}
.base {{ font-size:14px; color:var(--tinta-2); margin-bottom:12px; }}
.regua {{ list-style:none; padding:0; }}
.regua a {{ display:grid; grid-template-columns:30px auto minmax(24px,1fr) auto; align-items:baseline; gap:12px; padding:11px 0; border-bottom:1px solid var(--fio-2); color:var(--tinta); text-decoration:none; }}
.regua a:hover .rp {{ text-decoration:underline; text-decoration-color:var(--verde); }}
.rn {{ font-weight:700; color:var(--verde); font-size:15px; }}
.rp {{ font-size:16px; }}
.rl {{ border-bottom:1px dotted var(--fio-forte); transform:translateY(-4px); }}
.rv {{ font-size:19px; font-weight:600; letter-spacing:-.01em; text-align:right; }}
.rv small {{ font-size:13px; font-weight:400; color:var(--tinta-3); }}

/* respostas */
.coluna {{ max-width:var(--larg); margin:0 auto; padding:0 var(--med); }}
.resp {{ display:grid; grid-template-columns:64px minmax(0,1fr); gap:0 8px; padding:40px 0 34px; border-bottom:1px solid var(--fio); scroll-margin-top:76px; }}
.extras, .por-ente {{ scroll-margin-top:76px; }}
.resp .num {{ font-size:40px; font-weight:700; color:var(--verde); line-height:1; letter-spacing:-.02em; }}
.resp h2 {{ font-size:22px; line-height:1.25; letter-spacing:-.01em; margin-bottom:10px; text-wrap:balance; }}
.ementa {{ font-family:var(--serif); font-size:19px; line-height:1.55; max-width:62ch; margin-bottom:22px; }}
.sub {{ font-size:13px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-bottom:12px; }}
.nota {{ font-size:14px; color:var(--tinta-2); max-width:68ch; margin-top:12px; }}
.limite {{ font-size:14px; line-height:1.5; color:var(--tinta-2); max-width:72ch; margin-top:22px; padding-top:10px; border-top:1px dashed var(--fio-forte); }}
.limite b {{ color:var(--tinta); }}
.dois {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:32px; }}
.faixa-seg {{ display:flex; height:30px; gap:2px; }}
.seg {{ display:flex; align-items:center; padding-left:8px; font:600 13px/1 var(--sans); color:#fff; min-width:26px; }}
.seg-ok {{ background:var(--ok); }} .seg-nc {{ background:var(--nc); }} .seg-ind {{ background:var(--ind-cor); color:var(--tinta); }}
.seg-parc {{ background:var(--parc); color:var(--tinta); }} .seg-esp {{ background:var(--esp); }}
.leg-parc::before {{ background:var(--parc); }} .leg-esp::before {{ background:var(--esp); }}
.faixa-ed {{ height:40px; }} .faixa-ed .seg {{ font-size:14px; }}
.chave-ed {{ list-style:none; padding:0; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px 24px; margin-top:12px; font-size:14px; color:var(--tinta-2); }}
.chave-ed li {{ display:grid; grid-template-columns:16px minmax(0,1fr); line-height:1.35; }}
.chave-ed li::before {{ margin:5px 0 0; }}
.chave-ed b {{ font-size:18px; color:var(--tinta); margin-right:2px; }}
.chave-ed span {{ display:block; font-size:13px; color:var(--tinta-3); }}
.sub-sep {{ margin-top:36px; }}
.seg-sl {{ background:repeating-linear-gradient(135deg, var(--sl) 0 2px, transparent 2px 4px); color:var(--tinta); }}
.legenda {{ display:flex; flex-wrap:wrap; gap:4px 16px; font-size:13px; color:var(--tinta-2); margin-top:8px; }}
.leg::before {{ content:""; display:inline-block; width:10px; height:10px; margin-right:6px; vertical-align:-1px; }}
.leg-ok::before {{ background:var(--ok); }} .leg-nc::before {{ background:var(--nc); }} .leg-ind::before {{ background:var(--ind-cor); }}
.leg-sl::before {{ background:repeating-linear-gradient(135deg, var(--sl) 0 2px, transparent 2px 4px); outline:1px solid var(--sl); outline-offset:-1px; }}
details.lista {{ margin-top:20px; border-top:1px solid var(--fio-2); padding-top:10px; max-width:76ch; }}
details.lista summary {{ cursor:pointer; font-size:14px; font-weight:600; color:var(--verde); }}
details.lista p {{ font-size:14px; color:var(--tinta-2); margin-top:8px; line-height:1.6; }}

/* barras (reaproveitadas do relatório exploratório) */
.hb {{ display:grid; gap:9px; max-width:760px; }}
.hb-l {{ display:grid; grid-template-columns:var(--rot,140px) minmax(0,1fr) var(--val,168px); gap:12px; align-items:center; font-size:14px; }}
.hb-rot {{ line-height:1.3; }}
.hb-trilho {{ display:flex; height:16px; background:var(--fio-2); }}
.hb-trilho > span {{ display:block; height:100%; }}
.hb-v {{ font-size:13px; color:var(--tinta-3); white-space:nowrap; text-align:right; }}
.hb-v b {{ font-size:14px; color:var(--tinta); font-weight:600; margin-right:4px; }}
.b-tinta {{ background:var(--tinta-2); }} .b-fio {{ background:var(--fio-forte); }}

/* venn */
.vennes {{ display:grid; grid-template-columns:repeat(2,minmax(0,380px)); gap:12px 48px; margin-bottom:4px; }}
.venn {{ margin:0; }}
.venn svg {{ width:100%; height:auto; display:block; }}
.v-c {{ fill:var(--ok); fill-opacity:.13; stroke:var(--ok); stroke-width:1.5; }}
.v-tit {{ font:600 14px var(--sans); fill:var(--tinta); }}
.v-n {{ font:600 26px var(--sans); fill:var(--tinta); }}
.v-ambos {{ fill:var(--verde-2); }}
.v-r {{ font:400 12.5px var(--sans); fill:var(--tinta-2); }}
.venn figcaption {{ font-size:14px; color:var(--tinta-2); margin-top:4px; max-width:46ch; }}
.venn figcaption b {{ color:var(--tinta); }}
.dois {{ margin-top:28px; }}

/* medidores */
.meds {{ display:grid; gap:16px; max-width:760px; }}
.med-l {{ display:grid; grid-template-columns:160px minmax(0,1fr) 168px; gap:14px; align-items:center; font-size:14px; }}
.med {{ position:relative; height:14px; background:var(--fio-2); }}
.med-fill {{ position:absolute; inset:0 auto 0 0; background:var(--tinta-2); }}
.med-min {{ position:absolute; top:-6px; bottom:-6px; width:2px; background:var(--verde); }}
.med-min span {{ position:absolute; top:-18px; left:-2px; font-size:11.5px; font-weight:600; color:var(--verde); white-space:nowrap; }}
.med-v {{ font-size:13px; color:var(--tinta-3); text-align:right; white-space:nowrap; }}
.med-v b {{ font-size:15px; color:var(--tinta); }}

/* tabelas */
.rola {{ overflow-x:auto; }}
.tab, .entes {{ border-collapse:collapse; font-size:14px; width:100%; }}
.tab {{ max-width:760px; }}
.tab th, .tab td, .entes th, .entes td {{ padding:9px 14px 9px 0; border-bottom:1px solid var(--fio-2); text-align:right; vertical-align:top; }}
.tab thead th, .entes thead th {{ font-size:11.5px; font-weight:600; text-transform:uppercase; letter-spacing:.07em; color:var(--tinta-3); border-bottom:1px solid var(--tinta); vertical-align:bottom; }}
.entes thead th span {{ text-transform:none; letter-spacing:0; font-weight:400; }}
.tab tbody th, .entes tbody th {{ text-align:left; font-weight:600; }}
.entes td.sit {{ text-align:left; }}
.tab thead th:first-child, .entes thead th:nth-child(1), .entes thead th:nth-child(3) {{ text-align:left; }}
.entes tr.grupo th {{ font-size:13px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; padding-top:22px; border-bottom:2px solid var(--tinta); }}
.entes tbody tr:not(.grupo):hover {{ background:var(--lavado); }}
.entes tr.sem-base th {{ color:var(--tinta-3); font-weight:500; }}
.selo {{ display:inline-block; font-size:12px; font-weight:600; padding:2px 8px; border-radius:3px; border:1px solid; white-space:nowrap; }}
.selo-cumpre {{ color:var(--ok); background:var(--verde-3); border-color:#b2cbbe; }}
.selo-nao_cumpre {{ color:var(--nc); background:var(--nc-lav); border-color:#e2c3bb; }}
.selo-pendencia {{ color:var(--ind); background:var(--ind-lav); border-color:#e6d0a6; }}
.selo-sem_leitura, .selo-sem_base {{ color:var(--tinta-2); background:var(--lavado); border-color:var(--fio-forte); }}
.selo-sem_base {{ border-style:dashed; background:transparent; }}
.det {{ display:block; font-size:12.5px; color:var(--tinta-3); margin-top:3px; }}
.abaixo {{ color:var(--nc); }}
.vazio {{ color:var(--tinta-3); font-size:13px; }}
.agr {{ font-size:13px; font-weight:600; }} .agr-ok {{ color:var(--ok); }} .agr-nc {{ color:var(--nc); }}

/* extras e tabela */
.extras, .por-ente {{ padding:40px 0 34px; border-bottom:1px solid var(--fio); }}
.bloco-t {{ font-size:13px; font-weight:700; letter-spacing:.09em; text-transform:uppercase; padding-bottom:8px; border-bottom:2px solid var(--tinta); margin-bottom:18px; }}
.ex-grade {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.3fr); gap:28px 40px; }}
.ex-grade p {{ max-width:60ch; }}
.ex-largo {{ grid-column:1 / -1; }}
.esp-l {{ list-style:none; padding:0; margin-top:12px; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:0 32px; font-size:14px; }}
.esp-l li {{ display:grid; grid-template-columns:auto minmax(0,1fr) auto; gap:8px; padding:7px 0; border-bottom:1px solid var(--fio-2); color:var(--tinta-2); }}
.esp-l b {{ color:var(--tinta); font-weight:600; }}
.esp-l span {{ color:var(--tinta); white-space:nowrap; }}

.limites {{ max-width:var(--larg); margin:0 auto; padding:40px var(--med) 8px; }}
.limites ul {{ padding:0; list-style:none; display:grid; gap:12px; max-width:80ch; }}
.limites li {{ padding-left:16px; position:relative; color:var(--tinta-2); font-size:15px; }}
.limites li::before {{ content:""; position:absolute; left:0; top:.7em; width:6px; height:6px; background:var(--tinta-3); }}
.limites b {{ color:var(--tinta); }}
.metodo {{ max-width:var(--larg); margin:0 auto; padding:18px var(--med) 56px; font-size:14px; color:var(--tinta-3); }}

.escopo {{ animation:entra .22s cubic-bezier(.16,1,.3,1); }}
@keyframes entra {{ from {{ opacity:.35; }} to {{ opacity:1; }} }}
@media (prefers-reduced-motion: reduce) {{ .escopo {{ animation:none; }} }}

@media (max-width: 900px) {{
  .dois, .ex-grade, .vennes {{ grid-template-columns:minmax(0,1fr); }}
  .chave-ed {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
  .esp-l {{ grid-template-columns:minmax(0,1fr); }}
}}
@media (max-width: 680px) {{
  :root {{ --med:16px; }}
  .faixa .lead {{ font-size:16.5px; }}
  .regua a {{ grid-template-columns:24px minmax(0,1fr); gap:2px 10px; }}
  .rl {{ display:none; }}
  .rv {{ grid-column:2; text-align:left; font-size:17px; }}
  .resp {{ grid-template-columns:minmax(0,1fr); padding:32px 0 28px; }}
  .resp .num {{ font-size:30px; margin-bottom:8px; }}
  .resp h2 {{ font-size:20px; }}
  .ementa {{ font-size:17.5px; }}
  .hb-l {{ grid-template-columns:minmax(0,1fr) var(--val-m,132px); gap:4px 10px; }}
  .med-l {{ grid-template-columns:minmax(0,1fr) 132px; gap:4px 10px; }}
  .med-l {{ row-gap:26px; }}
  .meds {{ gap:22px; }}
  .hb-rot, .med-rot {{ grid-column:1 / -1; }}
  .seg-grupo {{ width:100%; }}
  .recorte {{ padding-top:10px; padding-bottom:10px; }}
  .recorte .rr {{ position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap; }}
  .seg-grupo button {{ flex:1; padding:10px 6px; }}
  .entes thead {{ display:none; }}
  .entes, .entes tbody, .entes tr, .entes th, .entes td {{ display:block; width:100%; }}
  .entes tr {{ padding:10px 0; border-bottom:1px solid var(--fio-2); }}
  .entes tr.grupo {{ border-bottom:0; padding:0; }}
  .entes th, .entes td {{ border:0; padding:2px 0; text-align:left; }}
  .entes td {{ display:grid; grid-template-columns:150px minmax(0,1fr); gap:8px; font-size:14px; }}
  .entes td::before {{ content:attr(data-rot); color:var(--tinta-3); font-size:12.5px; }}
}}
@media print {{
  .faixa {{ background:none; color:var(--tinta); border-bottom:2px solid var(--verde); }}
  .faixa h1, .faixa .lead, .serie {{ color:var(--tinta); }}
  .recorte-barra, .pular {{ display:none; }}
  .resp, .extras {{ break-inside:avoid; }}
  details.lista > p {{ display:block; }}
}}
</style>
</head>
<body>
<a class="pular" href="#conteudo">Pular para as respostas</a>
<header class="faixa">
  <div class="faixa-in">
    <h1>Cotas da IN 5 nos editais da Lei Paulo Gustavo</h1>
    <p class="lead">Quantos entes cumprem a reserva para pessoas negras e indígenas, quanto de recurso e de vagas ela representa, e quais outras cotas os editais preveem.</p>
    <p class="serie"><span>Base de {n} editais de estados, DF e capitais</span><span>Gerado em {hoje}</span></p>
  </div>
</header>
<div class="recorte-barra">
  <div class="recorte"><span class="rr" id="rr">Recorte</span>
    <div class="seg-grupo" role="group" aria-labelledby="rr">
      <button type="button" data-alvo="todos" aria-pressed="true">Todos</button>
      <button type="button" data-alvo="estados" aria-pressed="false">Estados e DF</button>
      <button type="button" data-alvo="capitais" aria-pressed="false">Capitais</button>
    </div>
  </div>
</div>
<div id="conteudo">{blocos}</div>
<section class="limites" aria-labelledby="lim-t"><h2 class="bloco-t" id="lim-t">Método e limites</h2><ul>{limites}</ul></section>
<footer><p class="metodo">{metodo}</p></footer>
<script>
(function () {{
  var botoes = document.querySelectorAll('.seg-grupo button');
  var blocos = document.querySelectorAll('.escopo');
  function mostra(alvo, rolar) {{
    if (!document.querySelector('.escopo[data-escopo="' + alvo + '"]')) alvo = 'todos';
    blocos.forEach(function (b) {{ b.hidden = b.getAttribute('data-escopo') !== alvo; }});
    botoes.forEach(function (b) {{ b.setAttribute('aria-pressed', String(b.getAttribute('data-alvo') === alvo)); }});
    if (history.replaceState) history.replaceState(null, '', alvo === 'todos' ? location.pathname : '#' + alvo);
  }}
  botoes.forEach(function (b) {{ b.addEventListener('click', function () {{ mostra(b.getAttribute('data-alvo')); }}); }});
  var h = (location.hash || '').replace('#', '');
  if (h) mostra(h.split('-')[0]);
}})();
</script>
</body>
</html>
"""


def fontes_embutidas() -> str:
    """@font-face com woff2 em base64: a página funciona offline e no SharePoint, sem CDN."""
    pasta = ROOT / "relatorios" / "fontes"
    faces = [("Public Sans", "public-sans", w) for w in (400, 500, 600, 700)]
    faces += [("Source Serif 4", "source-serif-4", w) for w in (400, 600)]
    out = []
    for fam, arq, w in faces:
        dados = base64.b64encode((pasta / f"{arq}-{w}.woff2").read_bytes()).decode("ascii")
        out.append(f'@font-face {{ font-family:"{fam}"; font-weight:{w}; font-style:normal; font-display:swap; '
                   f'src:url(data:font/woff2;base64,{dados}) format("woff2"); }}')
    return "\n".join(out)


def gera() -> Path:
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(monta(carrega()).replace("IN 5", "IN 5"), encoding="utf-8")
    return SAIDA


if __name__ == "__main__":
    print(f"Relatório gerado em {gera()}")
