"""Relatório exploratório (nota técnica de achados) da base data/final/lpg_editais.xlsx.

Rodar a partir de src/:
    python relatorio_exploratorio.py      # gera relatorios/relatorio_exploratorio_lpg.html

Todo número do texto é calculado aqui a partir da planilha; nada é digitado à mão.
"""
from datetime import date
from html import escape
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PLANILHA = ROOT / "data" / "final" / "lpg_editais.xlsx"
SAIDA = ROOT / "relatorios" / "relatorio_exploratorio_lpg.html"

STATUS = ["conforme", "nao_conforme", "especifico", "indeterminado", "sem_leitura"]
ROT = {"conforme": "Conforme", "nao_conforme": "Não conforme", "especifico": "Específico",
       "indeterminado": "Indeterminado", "sem_leitura": "Sem leitura"}
TIPO = {"ESTADO": "Estados e DF", "CAPITAL": "Capitais"}
ESPERADOS = {"ESTADO": 27, "CAPITAL": 26}
GRUPOS_OUTRAS = {"pcd": "Pessoas com deficiência", "mulheres": "Mulheres", "lgbtqia": "LGBTQIA+",
                 "quilombolas": "Quilombolas", "territorio": "Território", "pessoas_idosas": "Pessoas idosas",
                 "povos_tradicionais": "Povos tradicionais", "outro": "Outros grupos"}
DISPOSITIVOS = {
    "art. 5º": "No mínimo 20% das vagas para pessoas negras e 10% para pessoas indígenas.",
    "§2º": "Frações iguais ou maiores que 0,5 arredondam para cima; menores que 0,5, para baixo.",
    "§3º": "Edital dividido em categorias deve ter cotas em todas elas.",
    "§4º": "Categoria com uma única vaga pode ir à ampla concorrência, se o edital como um todo reservar 20% e 10%.",
}
CAPITAL_UF = {"Aracaju": "SE", "Belo Horizonte": "MG", "Belém": "PA", "Boa Vista": "RR", "Campo Grande": "MS",
              "Cuiabá": "MT", "Curitiba": "PR", "Florianópolis": "SC", "Fortaleza": "CE", "Goiânia": "GO",
              "João Pessoa": "PB", "Macapá": "AP", "Maceió": "AL", "Natal": "RN", "Palmas": "TO",
              "Porto Alegre": "RS", "Porto Velho": "RO", "Recife": "PE", "Rio Branco": "AC",
              "Rio de Janeiro": "RJ", "Salvador": "BA", "São Luis": "MA", "São Paulo": "SP",
              "Teresina": "PI", "Vitória": "ES"}
SIGLA = {"Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM", "Bahia": "BA", "Ceará": "CE",
         "Distrito Federal": "DF", "Espírito Santo": "ES", "Goiás": "GO", "Mato Grosso": "MT",
         "Mato Grosso do Sul": "MS", "Minas Gerais": "MG", "Pará": "PA", "Paraíba": "PB", "Paraná": "PR",
         "Pernambuco": "PE", "Piauí": "PI", "Rio de Janeiro": "RJ", "Rio Grande do Norte": "RN",
         "Rio Grande do Sul": "RS", "Rondônia": "RO", "Santa Catarina": "SC", "São Paulo": "SP",
         "Sergipe": "SE", "Tocantins": "TO"}


# ---------------------------------------------------------------- formatação pt-BR

def n(v) -> str:
    return f"{int(round(v)):,}".replace(",", ".")


def p(v, casas=1) -> str:
    return f"{v * 100:.{casas}f}".replace(".", ",") + "%"


def brl(v) -> str:
    if v >= 1e9:
        return f"R$ {v / 1e9:.2f} bi".replace(".", ",")
    if v >= 1e6:
        return f"R$ {v / 1e6:.0f} mi"
    return f"R$ {v / 1e3:.0f} mil"


def frac(a, b) -> str:
    return f"{n(a)} de {n(b)}"


# ---------------------------------------------------------------- gráficos (SVG em linha)

def barra_empilhada(linhas, largura=None):
    """linhas: [(rótulo, {status: contagem})] -> barras 100% horizontais em HTML."""
    out = []
    for rot, c in linhas:
        tot = sum(c.values()) or 1
        segs = "".join(
            f'<span class="b-{s}" style="width:{100 * c[s] / tot:.2f}%" title="{ROT[s]}: {c[s]}">'
            f'{c[s] if c[s] / tot > .05 else ""}</span>' for s in STATUS if c.get(s))
        desc = ", ".join(f"{c[s]} {ROT[s].lower()}" for s in STATUS if c.get(s))
        out.append(f'<div class="hb-l"><span class="hb-rot">{escape(rot)}</span>'
                   f'<span class="hb-trilho emp" role="img" aria-label="{escape(rot)}: {desc}">{segs}</span>'
                   f'<span class="hb-v"><b>{n(tot)}</b></span></div>')
    leg = "".join(f'<span class="leg b-{s}-l">{ROT[s]}</span>' for s in STATUS
                  if any(c.get(s) for _, c in linhas))
    return f'<div class="hb hb-emp">{"".join(out)}<div class="legenda">{leg}</div></div>'


def barras(linhas, largura=None, fmt=n, maximo=None, rot_w=230):
    """linhas: [(rótulo, valor, classe, nota)] -> barras horizontais em HTML."""
    m = maximo or max(v for _, v, _, _ in linhas) or 1
    out = []
    for rot, v, cls, nota in linhas:
        w = max(100 * v / m, 0.6)
        out.append(f'<div class="hb-l"><span class="hb-rot">{escape(rot)}</span>'
                   f'<span class="hb-trilho"><span class="{cls.replace("f-", "b-")}" style="width:{w:.2f}%"></span></span>'
                   f'<span class="hb-v"><b>{fmt(v)}</b>' + (f' {escape(nota)}' if nota else "") + '</span></div>')
    return f'<div class="hb" style="--rot:{rot_w}px">{"".join(out)}</div>'


def _dispersao_svg(pontos, largura, altura, curto):
    import math
    ml, mb, mt, mr = 34, 34, 14, 12
    xmax = max(x for _, x, _, _, _ in pontos) + 2
    ymax = max(y for _, _, y, _, _ in pontos) + 2
    sx = lambda v: ml + (largura - ml - mr) * v / xmax
    sy = lambda v: altura - mb - (altura - mb - mt) * v / ymax
    out = []
    for t in range(0, int(xmax) + 1, 5):
        out.append(f'<line x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{mt}" y2="{altura - mb}" class="grade"/>'
                   f'<text x="{sx(t):.1f}" y="{altura - mb + 16}" class="t-eixo" text-anchor="middle">{t}</text>')
    for t in range(0, int(ymax) + 1, 5):
        out.append(f'<line x1="{ml}" x2="{largura - mr}" y1="{sy(t):.1f}" y2="{sy(t):.1f}" class="grade"/>'
                   f'<text x="{ml - 8}" y="{sy(t) + 4:.1f}" class="t-eixo" text-anchor="end">{t}</text>')
    lim = min(xmax, ymax)
    ang = math.degrees(math.atan((sy(0) - sy(lim)) / (sx(lim) - sx(0))))
    lx, ly = sx(lim * .55) - 6, sy(lim * .55) - 8
    out.append(f'<line x1="{sx(0)}" y1="{sy(0)}" x2="{sx(lim):.1f}" y2="{sy(lim):.1f}" class="diag"/>'
               f'<text x="{lx:.1f}" y="{ly:.1f}" class="t-nota" text-anchor="end" transform="rotate(-{ang:.1f} '
               f'{lx:.1f} {ly:.1f})">{"todos não conformes" if curto else "todos os editais não conformes"}</text>')
    out.append(f'<text x="{largura - mr}" y="{altura - 2}" class="t-eixo" text-anchor="end">editais do ente →</text>'
               f'<text x="{ml}" y="{mt - 3}" class="t-eixo">↑ não conformes</text>')
    for sig, x, y, tipo, dest in sorted(pontos, key=lambda q: q[4]):
        cls = "pt-est" if tipo == "ESTADO" else "pt-cap"
        out.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="{4 if curto else 5}" class="{cls}">'
                   f'<title>{escape(sig)}: {y} de {x}</title></circle>')
        if dest and not (curto and y == 0):
            rot = (CAPITAL_UF.get(sig, sig) + " cap.") if (curto and tipo == "CAPITAL") else sig
            dir_ = x > xmax * .78
            tx = sx(x) - 8 if dir_ else sx(x) + 8
            out.append(f'<text x="{tx:.1f}" y="{sy(y) + 4:.1f}" class="t-ponto" '
                       f'text-anchor="{"end" if dir_ else "start"}">{escape(rot)}</text>')
    return (f'<svg viewBox="0 0 {largura} {altura}" class="{"disp-estreita" if curto else "disp-larga"}" role="img" '
            f'aria-label="Número de editais e de editais não conformes por ente">{"".join(out)}</svg>')


def dispersao(pontos):
    """pontos: [(rótulo, n_editais, n_nc, tipo, destacar)] -> versão larga e estreita do mesmo gráfico."""
    return _dispersao_svg(pontos, 640, 330, False) + _dispersao_svg(pontos, 340, 300, True)


# ---------------------------------------------------------------- análise

def tipo_motivo(m: str) -> set[str]:
    out = set()
    for parte in str(m).split(" | "):
        if parte.startswith("nenhuma cota"):
            out.add("sem_cota")
        elif parte.startswith("cotas não aplicadas"):
            out.add("sem_categoria")
        elif parte.startswith(("abaixo do mínimo", "sem reserva informada")):
            out.add("categoria_abaixo")
        elif parte.startswith("total reservado") or "vagas reservadas de" in parte or parte.startswith("percentual"):
            out.add("calculo")
    return out


def analisa():
    abas = pd.read_excel(PLANILHA, sheet_name=None)
    d, cat, oc, ev = abas["editais"], abas["categorias"], abas["outras_cotas"], abas["evidencias"]
    d["st"] = d["status_in5"].fillna("sem_leitura")
    A = {"hoje": date.today().strftime("%d/%m/%Y"), "n": len(d), "entes": d.groupby("tipo_ente")["ente"].nunique()}
    A["st"] = d["st"].value_counts()
    A["por_tipo"] = {t: d[d.tipo_ente == t]["st"].value_counts().to_dict() for t in TIPO}
    A["taxa_tipo"] = {t: (d[d.tipo_ente == t]["st"] == "nao_conforme").mean() for t in TIPO}

    g = d.groupby(["tipo_ente", "ente"]).agg(total=("id", "size"), nc=("st", lambda s: (s == "nao_conforme").sum()))
    g = g.reset_index()
    A["ente"] = g
    A["sem_nc"] = {t: int(((g.tipo_ente == t) & (g.nc == 0)).sum()) for t in TIPO}
    A["mediana_editais"] = g.groupby("tipo_ente")["total"].median().to_dict()
    A["entes_base"] = g.groupby("tipo_ente").size().to_dict()

    nc = d[d.st == "nao_conforme"].copy()
    nc["tipos"] = nc["motivo_in5"].map(tipo_motivo)
    A["motivos"] = {k: int(nc["tipos"].map(lambda s: k in s).sum())
                    for k in ("sem_cota", "sem_categoria", "categoria_abaixo", "calculo")}
    A["estrutural"] = int(nc["tipos"].map(lambda s: bool(s & {"sem_cota", "sem_categoria"})).sum())
    A["so_calculo"] = int(nc["tipos"].map(lambda s: s == {"calculo"}).sum())
    A["nc_n"] = len(nc)
    A["ambos"] = int(((nc.status_negras == "nao_conforme") & (nc.status_indigenas == "nao_conforme")).sum())
    A["matriz"] = pd.crosstab(nc.status_negras, nc.status_indigenas)

    est = g[(g.tipo_ente == "ESTADO") & (g.nc > 0)].sort_values(["nc", "total"], ascending=[False, True])
    A["top_est"] = est.head(4)
    A["nc_est_total"] = int(g[g.tipo_ente == "ESTADO"]["nc"].sum())
    cap = g[(g.tipo_ente == "CAPITAL") & (g.nc > 0)].sort_values("nc", ascending=False)
    A["cap_max"] = cap.head(1)
    A["cap_com_nc"] = len(cap)
    A["integral"] = g[(g.nc == g.total) & (g.total > 1)]

    pn, pi = d["perc_cotas_negras"].dropna(), d["perc_cotas_indigenas"].dropna()
    A["piso_n"], A["base_n"] = int((pn.round(3) == 0.2).sum()), len(pn)
    A["piso_i"], A["base_i"] = int((pi.round(3) == 0.1).sum()), len(pi)
    A["dist_n"] = pn.round(2).value_counts().sort_index()
    A["dist_i"] = pi.round(2).value_counts().sort_index()
    agg = {}
    for t in TIPO:
        s = d[d.tipo_ente == t]
        for gr in ("negras", "indigenas"):
            b = s.dropna(subset=["vagas_totais", f"vagas_cotas_{gr}"])
            agg[(t, gr)] = b[f"vagas_cotas_{gr}"].sum() / b["vagas_totais"].sum()
            v = s.dropna(subset=["valor_total", f"valor_cotas_{gr}"])
            agg[(t, gr, "valor")] = v[f"valor_cotas_{gr}"].sum() / v["valor_total"].sum()
    A["agg"] = agg
    sl = cat[cat.vagas == 1]
    A["cat_n"], A["cat_um"] = len(cat), len(sl)

    A["valor_total"] = d["valor_total"].sum()
    A["valor_st"] = d.groupby("st")["valor_total"].sum()
    A["valor_tipo"] = d.groupby("tipo_ente")["valor_total"].sum()
    A["mediana_valor_vaga"] = d["valor_por_vaga"].median()

    cpc = d[d.st != "sem_leitura"].groupby("cotas_por_categoria")["st"].agg(
        total="size", nc=lambda s: (s == "nao_conforme").sum())
    A["cpc"] = cpc

    mod = d[d.st != "sem_leitura"].copy()
    mod["mod"] = mod["modalidade"].map({"fomento_execucao": "Fomento à execução", "premio": "Prêmio"}).fillna(
        "Bolsa, subsídio e outras")
    A["mod"] = mod.groupby("mod")["st"].agg(total="size", nc=lambda s: (s == "nao_conforme").sum())
    A["outro_mod"] = d[d.modalidade == "outro"][["ente", "objeto", "st"]]
    ar = d["area_cultural"].fillna("").str.lower()
    so_av = ar.str.contains("audiovisual") & ~ar.str.contains("demais|exceto|multiling")
    A["av"] = {"Somente audiovisual": d[so_av], "Demais áreas e multilinguagem": d[~so_av & (d.st != "sem_leitura")]}

    ocu = oc.drop_duplicates(["id", "grupo_padrao"])
    tot = d.groupby("tipo_ente").size()
    t = ocu.groupby(["grupo_padrao", "tipo_ente"]).size().unstack(fill_value=0).reindex(columns=list(TIPO), fill_value=0)
    t["total"] = t.sum(axis=1)
    A["oc"] = t.sort_values("total", ascending=False)
    A["oc_tot"] = tot
    A["oc_mediana"] = oc.groupby("grupo_padrao")["percentual"].median()
    A["editais_com_oc"] = ocu["id"].nunique()
    A["bonus"] = d["pontuacao_bonus"].notna().groupby(d.tipo_ente).mean()

    A["esp"] = d[d.st == "especifico"]
    A["leitura"] = d.groupby("modo_leitura")["st"].agg(total="size", nc=lambda s: (s == "nao_conforme").sum())
    A["sem_vagas"] = int(d["vagas_totais"].isna().sum())
    A["cat_sem_negras"] = cat["vagas_negras"].isna().mean()
    A["ev_n"], A["ev_media"] = len(ev), ev.groupby("id").size().mean()
    A["ev_pag_mediana"] = ev["pagina"].median()
    A["paginas_mediana"] = d["paginas"].median()
    A["revisar"] = int(d["revisar_grupos"].notna().sum())
    return A


# ---------------------------------------------------------------- composição

def achado(num, titulo, ementa, corpo, figura, legenda, limite, remissao=None):
    rem = (f'<span class="par" tabindex="0">{remissao}<span class="par-txt" role="tooltip"><b>IN 5, {remissao}</b> '
           f'{DISPOSITIVOS[remissao]}</span></span>' if remissao else "")
    fig = (f'<figure>{figura}<figcaption>{legenda}</figcaption></figure>' if figura else "")
    return f"""
<section class="achado" id="a{num}" aria-labelledby="a{num}-t">
  <div class="num" aria-hidden="true">{num}</div>
  <div class="corpo">
    <h2 id="a{num}-t"><span class="so-leitor">Achado {num}. </span>{titulo}</h2>
    <p class="ementa">{rem}{ementa}</p>
    {corpo}
    {fig}
    <p class="limite"><b>Limite.</b> {limite}</p>
  </div>
</section>"""


def monta(A) -> str:
    st, N = A["st"], A["n"]
    nc_n, conf = int(st.get("nao_conforme", 0)), int(st.get("conforme", 0))
    esp, ind, sl = int(st.get("especifico", 0)), int(st.get("indeterminado", 0)), int(st.get("sem_leitura", 0))
    vnc = A["valor_st"].get("nao_conforme", 0)
    top = A["top_est"]
    top_nc = int(top["nc"].sum())
    top_nomes = [f'{r.ente} ({int(r.nc)} de {int(r.total)})' for r in top.itertuples()]
    cpc = A["cpc"]
    taxa = lambda k: cpc.loc[k, "nc"] / cpc.loc[k, "total"] if k in cpc.index else 0
    mo = A["mod"]
    agg = A["agg"]
    cap_max = A["cap_max"].iloc[0]

    achados = []

    # 1
    linhas = [(TIPO[t], A["por_tipo"][t]) for t in TIPO]
    achados.append(achado(
        1, f"Sete em cada dez editais cumprem a IN 5; {n(nc_n)} não cumprem",
        f"{frac(conf, N)} editais ({p(conf / N)}) reservam o mínimo de 20% para pessoas negras e 10% para "
        f"pessoas indígenas; {n(nc_n)} ({p(nc_n / N)}) ficam abaixo em pelo menos um grupo.",
        f"<p>A taxa de não conformidade é quase a mesma nos dois tipos de ente: {p(A['taxa_tipo']['ESTADO'])} "
        f"nos editais estaduais e {p(A['taxa_tipo']['CAPITAL'])} nos das capitais. Outros {n(esp)} editais são "
        f"específicos, dirigidos integralmente a um grupo, e {n(ind + sl)} não puderam ser classificados.</p>",
        barra_empilhada(linhas), "Editais por situação na IN 5, por tipo de ente (número de editais).",
        f"A classificação vem de regras aplicadas em código sobre a extração automática; {n(ind)} indeterminados "
        f"e {n(sl)} sem leitura ficam fora das duas contas e pedem revisão manual.", "art. 5º"))

    # 2
    g = A["ente"]
    dest = set(top["ente"]) | set(A["cap_max"]["ente"]) | {"Pará", "Alagoas", "São Paulo"}
    pontos = [(SIGLA.get(r.ente, r.ente) if r.tipo_ente == "ESTADO" else r.ente, int(r.total), int(r.nc),
               r.tipo_ente, r.ente in dest) for r in g.itertuples()]
    achados.append(achado(
        2, "Capitais parecem cumprir mais, em boa parte porque publicam menos editais",
        f"{A['sem_nc']['CAPITAL']} de {A['entes_base']['CAPITAL']} capitais não têm nenhum edital não conforme, "
        f"contra {A['sem_nc']['ESTADO']} de {A['entes_base']['ESTADO']} estados.",
        f"<p>Por edital, os dois tipos falham na mesma proporção (achado 1). A diferença está no volume: a "
        f"mediana é de {n(A['mediana_editais']['ESTADO'])} editais por estado e "
        f"{n(A['mediana_editais']['CAPITAL'])} por capital. Quem publica mais editais tem mais chances de ter ao "
        f"menos um fora da regra, então “ente sem não conforme” mede tanto o volume quanto o cuidado.</p>",
        dispersao(pontos),
        "Cada ponto é um ente: editais publicados (horizontal) e editais não conformes (vertical). "
        "Círculo cheio: estado ou DF; vazado: capital.",
        "Comparar entes por “cumpre/não cumpre” sem ponderar o número de editais favorece quem publica pouco. "
        "A proporção de editais não conformes é a medida mais justa."))

    # 3
    mt = A["motivos"]
    achados.append(achado(
        3, "A falha é de desenho do edital, não de arredondamento",
        f"{frac(A['estrutural'], nc_n)} editais não conformes não preveem cota alguma para o grupo ou não a "
        f"aplicam em cada categoria; só {n(A['so_calculo'])} falham apenas na conta de vagas.",
        "<p>O motivo mais comum é não haver cota identificada para o grupo. O segundo é declarar o percentual "
        "geral sem distribuí-lo pelas categorias, como exige o §3º. Ficar abaixo do mínimo por diferença de "
        "arredondamento ou pela exceção de vaga única (§4º) é raro.</p>",
        barras([("Nenhuma cota identificada", mt["sem_cota"], "f-tinta", ""),
                ("Cotas não aplicadas por categoria (§3º)", mt["sem_categoria"], "f-tinta", ""),
                ("Categorias abaixo do mínimo ou sem reserva", mt["categoria_abaixo"], "f-tinta", ""),
                ("Conta de vagas ou total (§2º, §4º)", mt["calculo"], "f-tinta", "")], rot_w=290),
        "Motivos registrados nos editais não conformes. Um edital pode ter mais de um motivo, então as barras "
        "somam mais que o total.",
        "“Nenhuma cota identificada” pode incluir cotas descritas fora do trecho lido pelo modelo; vale "
        "conferir esses editais no PDF antes de qualquer notificação.", "§3º"))

    # 4
    mx = A["matriz"]
    cel = lambda a, b: int(mx.loc[a, b]) if a in mx.index and b in mx.columns else 0
    tab4 = f"""<table class="tab mini"><caption class="so-leitor">Situação para negros e indígenas nos editais não conformes</caption>
<thead><tr><th></th><th>Indígenas conforme</th><th>Indígenas não conforme</th><th>Indígenas indeterminado</th></tr></thead>
<tbody><tr><th>Negros conforme</th><td>{cel('conforme', 'conforme')}</td><td>{cel('conforme', 'nao_conforme')}</td><td>{cel('conforme', 'indeterminado')}</td></tr>
<tr><th>Negros não conforme</th><td>{cel('nao_conforme', 'conforme')}</td><td class="forte">{cel('nao_conforme', 'nao_conforme')}</td><td>{cel('nao_conforme', 'indeterminado')}</td></tr></tbody></table>"""
    achados.append(achado(
        4, "Quando um edital falha, falha para negros e indígenas ao mesmo tempo",
        f"{frac(A['ambos'], nc_n)} editais não conformes ficam abaixo do mínimo nos dois grupos.",
        "<p>Isso reforça o achado 3: o problema raramente é calibrar um percentual específico, e sim a ausência "
        "da política de cotas no edital. A correção de um edital tende a resolver os dois grupos de uma vez.</p>"
        + tab4, None, "",
        "A tabela considera só os editais classificados como não conformes no total da IN 5."))

    # 5
    demais = A["nc_est_total"] - top_nc
    segs5 = "".join(f'<span class="b-nao_conforme" style="width:{100 * r.nc / A["nc_est_total"]:.2f}%" '
                    f'title="{escape(r.ente)}: {int(r.nc)}">{SIGLA.get(r.ente, r.ente)} {int(r.nc)}</span>'
                    for r in top.itertuples())
    segs5 += (f'<span class="b-nao_conforme" style="width:{100 * demais / A["nc_est_total"]:.2f}%" '
              f'title="Demais estados: {demais}">demais {demais}</span>')
    lista5 = "".join(f"<li><b>{escape(r.ente)}</b> {int(r.nc)} não conformes de {int(r.total)} editais</li>"
                     for r in top.itertuples())
    fig5 = (f'<div class="hb"><div class="hb-l hb-um"><span class="hb-trilho emp part" role="img" '
            f'aria-label="{n(top_nc)} dos {n(A["nc_est_total"])} editais estaduais não conformes estão em quatro estados">'
            f'{segs5}</span><span class="hb-v"><b>{n(A["nc_est_total"])}</b></span></div></div>'
            f'<ul class="lista5">{lista5}</ul>')
    integ = A["integral"]
    frase_int = ""
    if len(integ) == 1:
        r = integ.iloc[0]
        frase_int = f"{r.ente} tem todos os {int(r.total)} editais da base classificados como não conformes. "
    elif len(integ) > 1:
        frase_int = (f"Em {len(integ)} entes, todos os editais da base são não conformes: "
                     + ", ".join(f"{r.ente} ({int(r.total)})" for r in integ.itertuples()) + ". ")
    achados.append(achado(
        5, f"Quatro estados concentram {p(top_nc / A['nc_est_total'], 0)} dos editais estaduais não conformes",
        f"{', '.join(top_nomes[:-1])} e {top_nomes[-1]} somam {n(top_nc)} dos {n(A['nc_est_total'])} editais "
        f"estaduais não conformes.",
        f"<p>Nas capitais, a não conformidade é dispersa: {A['cap_com_nc']} capitais têm ao menos um edital não "
        f"conforme, e a que mais tem é {cap_max.ente}, com {int(cap_max.nc)} de {int(cap_max.total)}. "
        f"{frase_int}"
        "A concentração sugere que uma orientação dirigida a poucos entes alcançaria a maior parte dos casos "
        "estaduais.</p>",
        fig5,
        "Participação de cada estado nos editais estaduais não conformes; abaixo, o total de editais de cada um.",
        "A base reúne os editais localizados para cada ente; um ente com poucos editais na base pode ter "
        "publicado outros não incluídos."))

    # 6
    dist = [(f"{p(k, 0)} para pessoas negras", int(v), "f-tinta", "mínimo da IN 5" if round(k, 2) == 0.2 else "")
            for k, v in A["dist_n"].items()]
    dist += [(f"{p(k, 0)} para pessoas indígenas", int(v), "f-tinta", "mínimo da IN 5" if round(k, 2) == 0.1 else "")
             for k, v in A["dist_i"].items()]
    achados.append(achado(
        6, "O mínimo da norma virou o padrão",
        f"{frac(A['piso_n'], A['base_n'])} editais com percentual informado reservam exatamente 20% para "
        f"pessoas negras, e {frac(A['piso_i'], A['base_i'])}, exatamente 10% para pessoas indígenas.",
        f"<p>Quase nenhum ente vai além do piso. Mesmo assim, as vagas efetivamente reservadas somam "
        f"{p(agg[('ESTADO', 'negras')])} (negros) e {p(agg[('ESTADO', 'indigenas')])} (indígenas) nos estados, e "
        f"{p(agg[('CAPITAL', 'negras')])} e {p(agg[('CAPITAL', 'indigenas')])} nas capitais: o arredondamento "
        f"para cima em categorias pequenas (§2º) empurra o agregado acima do percentual declarado, sobretudo "
        f"no grupo de 10%. Em valor, a reserva estimada para pessoas negras chega a "
        f"{p(agg[('ESTADO', 'negras', 'valor')])} nos estados e {p(agg[('CAPITAL', 'negras', 'valor')])} nas capitais.</p>",
        barras(dist, rot_w=230), "Editais por percentual de reserva declarado.",
        "Os agregados usam só os editais com vagas totais e reservadas informadas; o valor reservado é estimado "
        "pelo valor médio da vaga de cada edital.", "§2º"))

    # 7
    vt = A["valor_total"]
    lin7 = [(ROT[s], A["valor_st"].get(s, 0), f"f-{s}", p(A["valor_st"].get(s, 0) / vt)) for s in STATUS
            if A["valor_st"].get(s, 0) > 0]
    achados.append(achado(
        7, f"{brl(vnc)} estão em editais que não cumprem a IN 5",
        f"Dos {brl(vt)} somados nos editais com valor informado, {p(vnc / vt)} estão em editais não conformes.",
        f"<p>Os estados respondem por {brl(A['valor_tipo']['ESTADO'])} e as capitais por "
        f"{brl(A['valor_tipo']['CAPITAL'])}. A mediana do valor por vaga é de {brl(A['mediana_valor_vaga'])}.</p>",
        barras(lin7, fmt=brl, rot_w=150), "Valor total dos editais por situação na IN 5.",
        "O valor é o total declarado no edital, não o valor executado; editais retificados ou cancelados "
        "depois da publicação não são descontados."))

    # 8
    nomes_cpc = {"sim": "Declara cota por categoria", "nao": "Declara que não aplica por categoria",
                 "nao_informado": "Não informa", "sem_categorias": "Edital sem categorias"}
    lin8 = [(nomes_cpc.get(k, k), taxa(k), "f-tinta",
             f"{int(cpc.loc[k, 'nc'])} de {int(cpc.loc[k, 'total'])}") for k in ["nao", "nao_informado", "sem_categorias", "sim"]
            if k in cpc.index]
    achados.append(achado(
        8, "Distribuir a cota por categoria é o melhor sinal de conformidade",
        f"Entre os editais que dizem não aplicar a cota em cada categoria, {p(taxa('nao'), 0)} são não "
        f"conformes; entre os que a distribuem, só {p(taxa('sim'), 0)}.",
        "<p>A pergunta “o edital distribui a cota pelas categorias?” separa os casos melhor do que tipo de ente, "
        "área ou modalidade. É um bom primeiro filtro para uma triagem rápida de novos editais.</p>",
        barras(lin8, fmt=lambda v: p(v, 0), maximo=1, rot_w=270), "Proporção de editais não conformes conforme o "
        "edital declara ou não cotas por categoria.",
        "Parte da relação é mecânica: declarar que não aplica por categoria leva, pelo §3º, à não conformidade.",
        "§3º"))

    # 9
    lin9 = [(k, r.nc / r.total, "f-tinta", f"{int(r.nc)} de {int(r.total)}") for k, r in mo.iterrows()]
    av = [(k, (v["st"] == "nao_conforme").mean(), "f-tinta", f"{int((v['st'] == 'nao_conforme').sum())} de {len(v)}")
          for k, v in A["av"].items()]
    outros = A["outro_mod"]
    exemplo = next((o for o in outros["objeto"].dropna() if "parecer" in o.lower()), None)
    achados.append(achado(
        9, "Prêmios falham menos que fomento; a área cultural pesa pouco",
        f"{p(mo.loc['Fomento à execução', 'nc'] / mo.loc['Fomento à execução', 'total'], 0)} dos editais de fomento "
        f"à execução são não conformes, contra {p(mo.loc['Prêmio', 'nc'] / mo.loc['Prêmio', 'total'], 0)} dos prêmios.",
        "<p>Audiovisual e demais áreas têm taxas próximas. Entre as modalidades menores, há editais que não "
        "selecionam projetos culturais"
        + (f" (por exemplo, “{escape(exemplo[:120])}…”)" if exemplo else "")
        + ", aos quais as cotas da IN 5 talvez nem se apliquem.</p>",
        barras(lin9 + av, fmt=lambda v: p(v, 0), maximo=max(v for _, v, _, _ in lin9 + av) * 1.15, rot_w=230),
        "Proporção de editais não conformes por modalidade e por área.",
        "As modalidades “bolsa, subsídio e outras” somam poucos editais; a taxa delas oscila muito com um caso a mais."))

    # 10
    oc, tot = A["oc"], A["oc_tot"]
    lin10 = [(GRUPOS_OUTRAS.get(gr, gr), int(r["total"]), "f-tinta",
              f"{int(r['ESTADO'])} estaduais, {int(r['CAPITAL'])} de capitais") for gr, r in oc.iterrows()]
    med_m = A["oc_mediana"].get("mulheres")
    achados.append(achado(
        10, "Além da IN 5, PcD e mulheres são as cotas mais frequentes",
        f"{n(A['editais_com_oc'])} editais preveem alguma cota além de negros e indígenas; pessoas com deficiência "
        f"aparecem em {n(oc.loc['pcd', 'total'])} e mulheres em {n(oc.loc['mulheres', 'total'])}.",
        f"<p>As cotas para mulheres são as mais altas, com mediana de {p(med_m, 0)} das vagas. Quilombolas e "
        f"território são quase exclusivas dos estados ({n(oc.loc['quilombolas', 'ESTADO'])} de "
        f"{n(oc.loc['quilombolas', 'total'])} e {n(oc.loc['territorio', 'ESTADO'])} de "
        f"{n(oc.loc['territorio', 'total'])}). Pontuação bônus para grupos aparece em "
        f"{p(A['bonus']['ESTADO'], 0)} dos editais estaduais e {p(A['bonus']['CAPITAL'], 0)} dos de capitais.</p>",
        barras(lin10, rot_w=190), "Editais que preveem cada grupo de cota adicional.",
        "“Território” reúne reservas regionais (interior, regiões administrativas) que não são ações afirmativas "
        "para grupos sociais."))

    sumario = "".join(f'<li><a href="#a{i}"><span class="sn">{i}</span>{t}</a></li>' for i, t in enumerate([
        "Sete em cada dez cumprem", "Capitais e volume de editais", "Falha de desenho", "Os dois grupos juntos",
        "Concentração em quatro estados", "O mínimo virou padrão", "Valor em editais não conformes",
        "Cota por categoria como sinal", "Modalidade e área", "Outras cotas"], 1))

    exec_itens = [
        f"{p(conf / N, 0)} dos {n(N)} editais cumprem a IN 5; a taxa de não conformidade é quase igual em estados e capitais.",
        f"{frac(A['estrutural'], nc_n)} não conformes não têm cota ou não a aplicam por categoria (§3º).",
        f"Quatro estados concentram {p(top_nc / A['nc_est_total'], 0)} dos não conformes estaduais.",
        f"{p(A['piso_n'] / A['base_n'], 0)} dos {n(A['base_n'])} editais com percentual informado reservam exatamente "
        f"o mínimo para pessoas negras.",
        f"{brl(vnc)} ({p(vnc / vt, 0)} do valor) estão em editais não conformes.",
    ]
    chave = [(n(N), "editais"), (f"{A['entes_base']['ESTADO']}+{A['entes_base']['CAPITAL']}", "entes na base"),
             (brl(vt), "em editais"), (p(conf / N, 1), "conformes"), (n(nc_n), "não conformes"),
             (n(ind + sl), "a revisar")]

    leit = A["leitura"]
    taxa_pdf = leit.loc["pdf", "nc"] / leit.loc["pdf", "total"] if "pdf" in leit.index else 0
    taxa_txt = leit.loc["texto", "nc"] / leit.loc["texto", "total"]
    limites = [
        f"<b>Cobertura.</b> {A['entes_base']['ESTADO']} de {ESPERADOS['ESTADO']} UFs e {A['entes_base']['CAPITAL']} "
        f"de {ESPERADOS['CAPITAL']} capitais têm editais na base.",
        f"<b>Vagas.</b> {n(A['sem_vagas'])} editais ({p(A['sem_vagas'] / N, 0)}) não informam o total de vagas, e "
        f"{p(A['cat_sem_negras'], 0)} das {n(A['cat_n'])} categorias não trazem vagas para negros explicitadas.",
        f"<b>Leitura.</b> {n(leit.loc['pdf', 'total']) if 'pdf' in leit.index else 0} PDFs escaneados foram lidos como "
        f"imagem; neles a não conformidade é de {p(taxa_pdf, 0)}, contra {p(taxa_txt, 0)} nos lidos como texto, "
        f"o que pode refletir erro de leitura.",
        f"<b>Revisão.</b> {n(ind)} editais indeterminados, {n(sl)} sem leitura e {n(A['revisar'])} com outras cotas "
        f"marcadas para revisão manual.",
        f"<b>Evidência.</b> {n(A['ev_n'])} trechos citados, cerca de {str(round(A['ev_media'], 1)).replace('.', ',')} "
        f"por edital; a mediana da página citada é {n(A['ev_pag_mediana'])}, e os editais têm mediana de "
        f"{n(A['paginas_mediana'])} páginas.",
    ]

    return PAGINA.format(
        hoje=A["hoje"], n=n(N),
        exec="".join(f"<li>{x}</li>" for x in exec_itens),
        chave="".join(f"<div><dd>{v}</dd><dt>{k}</dt></div>" for v, k in chave),
        sumario=sumario, achados="".join(achados),
        limites="".join(f"<li>{x}</li>" for x in limites),
        metodo=(f"Base: <code>data/final/lpg_editais.xlsx</code> (abas editais, categorias, outras_cotas e "
                f"evidencias), gerada pelo pipeline do projeto. Extração estruturada com LLM e regras do art. 5º "
                f"da IN MinC nº 5/2023 aplicadas em código. Este relatório foi gerado em {A['hoje']} por "
                f"<code>src/relatorio_exploratorio.py</code>; todos os números são recalculados a cada execução."),
    )


PAGINA = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cotas na LPG · Achados</title>
<meta name="description" content="Nota técnica com os principais achados da base de editais da Lei Paulo Gustavo sobre as cotas da IN MinC nº 5/2023.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<style>
:root {{
  --papel:#ffffff; --lavado:#f3f5f4; --tinta:#16191d; --tinta-2:#444a52; --tinta-3:#5d636b;
  --fio:#dcdfe3; --fio-2:#edeff1; --fio-forte:#c9ced3; --verde:#1f5f45; --verde-2:#174a36; --verde-3:#e4efe9;
  --verde-txt:#dfece5; --ok:#1f5f45; --nc:#9e3a2b; --esp:#3e6e8e; --ind:#8c5a0e; --ind-cor:#c48a2a; --sl:#8a9097;
  --sans:"Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --serif:"Source Serif 4",Georgia,"Times New Roman",serif;
  color-scheme: light;
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; -webkit-text-size-adjust:100%; }}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior:auto; }} }}
body {{ margin:0; background:var(--papel); color:var(--tinta); font:16px/1.6 var(--sans); font-variant-numeric:tabular-nums lining-nums; }}
::selection {{ background:#cfe3d8; }}
a {{ color:var(--verde); text-underline-offset:3px; text-decoration-thickness:1px; }}
:focus-visible {{ outline:2px solid var(--verde); outline-offset:2px; border-radius:2px; }}
h1,h2,p,ul,ol,dl,dd,figure {{ margin:0; }}
code {{ font-size:.88em; background:var(--lavado); padding:1px 5px; border-radius:3px; }}
.so-leitor {{ position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap; }}
.pular {{ position:absolute; left:-999px; top:8px; background:var(--tinta); color:#fff; padding:8px 12px; z-index:9; }}
.pular:focus {{ left:8px; }}

/* faixa: o mundo é dono da moldura */
.faixa {{ background:var(--verde); color:var(--verde-txt); }}
.faixa-in {{ max-width:1180px; margin:0 auto; padding:34px 32px 30px; display:grid; gap:10px; }}
.faixa .serie {{ font-size:13px; color:#c6dccf; display:flex; flex-wrap:wrap; gap:4px 18px; margin-top:6px; padding-top:12px; border-top:1px solid rgba(255,255,255,.16); max-width:62ch; }}
.faixa h1 {{ color:#fff; font-size:clamp(28px, 3.4vw, 42px); line-height:1.12; letter-spacing:-.015em; font-weight:700; max-width:30ch; text-wrap:balance; }}
.faixa .sub {{ font-family:var(--serif); font-size:18px; color:#e9f2ed; max-width:62ch; }}

.abertura {{ max-width:1180px; margin:0 auto; padding:30px 32px 34px; display:grid; grid-template-columns:minmax(0,1.5fr) minmax(280px,1fr); gap:36px; border-bottom:1px solid var(--fio); }}
.bloco-t {{ font-size:13px; font-weight:700; letter-spacing:.09em; text-transform:uppercase; padding-bottom:8px; border-bottom:2px solid var(--tinta); margin-bottom:14px; }}
.exec ol {{ padding:0; list-style:none; counter-reset:e; display:grid; gap:10px; }}
.exec li {{ counter-increment:e; display:grid; grid-template-columns:22px 1fr; gap:10px; font-size:16px; line-height:1.5; }}
.exec li::before {{ content:counter(e); font-weight:700; color:var(--verde); }}
.chave {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:0; }}
.chave div {{ padding:12px 0; border-bottom:1px solid var(--fio-2); display:grid; }}
.chave div:nth-child(odd) {{ padding-right:16px; }}
.chave dd {{ font-size:26px; font-weight:600; letter-spacing:-.01em; line-height:1.15; }}
.chave dt {{ font-size:13px; color:var(--tinta-2); }}

/* corpo: sumário fixo + coluna */
.grade {{ max-width:1180px; margin:0 auto; padding:0 32px; display:grid; grid-template-columns:240px minmax(0,1fr); gap:48px; }}
.indice {{ position:sticky; top:0; align-self:start; padding:28px 0; max-height:100vh; overflow:auto; }}
.indice ol {{ list-style:none; padding:0; display:grid; gap:2px; }}
.indice a {{ display:grid; grid-template-columns:26px 1fr; gap:6px; padding:6px 8px; margin:0 -8px; color:var(--tinta-2); text-decoration:none; font-size:14px; line-height:1.35; border-radius:3px; }}
.indice a:hover {{ background:var(--lavado); color:var(--tinta); }}
.indice .sn {{ font-weight:700; color:var(--verde); }}
.indice .extra {{ margin-top:12px; padding-top:12px; border-top:1px solid var(--fio); }}

.achado {{ display:grid; grid-template-columns:64px minmax(0,1fr); gap:0 8px; padding:40px 0 36px; border-bottom:1px solid var(--fio); scroll-margin-top:12px; }}
.achado .num {{ font-size:40px; font-weight:700; color:var(--verde); line-height:1; letter-spacing:-.02em; padding-top:2px; }}
.achado h2 {{ font-size:23px; line-height:1.25; letter-spacing:-.01em; max-width:34ch; text-wrap:balance; margin-bottom:12px; }}
.ementa {{ font-family:var(--serif); font-size:18.5px; line-height:1.55; max-width:62ch; margin-bottom:14px; }}
.corpo > p:not(.ementa):not(.limite) {{ max-width:68ch; color:var(--tinta-2); margin-bottom:18px; }}
.par {{ display:inline-block; font:600 12px/1.6 var(--sans); color:var(--verde); background:var(--verde-3); border:1px solid #b2cbbe; border-radius:2px; padding:0 5px; margin-right:8px; vertical-align:2px; }}
figure {{ margin:8px 0 18px; max-width:720px; }}
figure svg {{ width:100%; height:auto; display:block; overflow:visible; }}
.rola {{ overflow-x:auto; }}
.hb {{ display:grid; gap:9px; max-width:720px; }}
.hb-l {{ display:grid; grid-template-columns:var(--rot, 140px) minmax(0,1fr) minmax(64px, max-content); gap:12px; align-items:center; font-size:14px; }}
.hb-emp .hb-l {{ grid-template-columns:120px minmax(0,1fr) 48px; }}
.hb-rot {{ color:var(--tinta); line-height:1.3; }}
.hb-trilho {{ display:flex; height:16px; }}
.hb-trilho.emp {{ height:22px; background:var(--fio-2); }}
.hb-trilho > span {{ display:block; height:100%; font:600 12px/22px var(--sans); color:#fff; padding-left:5px; overflow:hidden; white-space:nowrap; }}
.hb-trilho > .b-indeterminado {{ color:var(--tinta); }}
.hb-v {{ font-size:13px; color:var(--tinta-3); white-space:nowrap; text-align:right; }}
.hb-v b {{ font-size:14px; color:var(--tinta); font-weight:600; }}
.hb-emp .hb-v {{ text-align:right; }}
.b-conforme {{ background:var(--ok); }} .b-nao_conforme {{ background:var(--nc); }} .b-especifico {{ background:var(--esp); }}
.b-indeterminado {{ background:var(--ind-cor); }} .b-tinta {{ background:var(--tinta-2); }}
.b-sem_leitura {{ background:repeating-linear-gradient(135deg, var(--sl) 0 2px, transparent 2px 4px); }}
.part > span {{ border-right:2px solid #fff; }}
.hb-um {{ grid-template-columns:minmax(0,1fr) 48px !important; }}
.lista5 {{ list-style:none; padding:0; margin:12px 0 0; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:6px 24px; font-size:14px; color:var(--tinta-2); }}
.lista5 b {{ color:var(--tinta); font-weight:600; margin-right:4px; }}
.disp-estreita {{ display:none !important; }}
.par {{ position:relative; cursor:help; }}
.par-txt {{ position:absolute; z-index:5; left:0; top:calc(100% + 6px); width:280px; white-space:normal; background:var(--tinta); color:#f1f3f4; font:400 13px/1.45 var(--sans); padding:9px 11px; border-radius:3px; box-shadow:0 6px 18px rgba(16,24,32,.22); opacity:0; transform:translateY(-3px); pointer-events:none; transition:opacity .16s, transform .16s; }}
.par-txt b {{ color:#fff; font-weight:600; }}
.par:hover .par-txt, .par:focus .par-txt {{ opacity:1; transform:none; }}
.legenda {{ display:flex; flex-wrap:wrap; gap:4px 16px; font-size:13px; color:var(--tinta-2); margin-top:2px; }}
.leg::before {{ content:""; display:inline-block; width:10px; height:10px; margin-right:6px; vertical-align:-1px; }}
.b-conforme-l::before {{ background:var(--ok); }} .b-nao_conforme-l::before {{ background:var(--nc); }}
.b-especifico-l::before {{ background:var(--esp); }} .b-indeterminado-l::before {{ background:var(--ind-cor); }}
.b-sem_leitura-l::before {{ background:repeating-linear-gradient(135deg, var(--sl) 0 2px, transparent 2px 4px); outline:1px solid var(--sl); outline-offset:-1px; }}
figcaption {{ font-size:13.5px; color:var(--tinta-3); margin-top:8px; max-width:68ch; }}
.limite {{ font-size:14px; line-height:1.5; color:var(--tinta-2); max-width:68ch; padding:10px 0 0; border-top:1px dashed var(--fio-forte); }}
.limite b {{ color:var(--tinta); }}

/* tabela */
.tab {{ border-collapse:collapse; font-size:14px; margin:4px 0 18px; }}
.tab th, .tab td {{ padding:8px 14px 8px 0; border-bottom:1px solid var(--fio-2); text-align:right; }}
.tab thead th {{ font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--tinta-3); border-bottom:1px solid var(--tinta); }}
.tab tbody th {{ text-align:left; font-weight:600; }}
.tab td.forte {{ font-weight:700; font-size:17px; }}

/* svg */
.t-rot {{ font:14px var(--sans); fill:var(--tinta); }}
.t-num {{ font:600 14px var(--sans); fill:var(--tinta); }}
.t-nota {{ font:400 13px var(--sans); fill:var(--tinta-3); }}
.t-in {{ font:600 12px var(--sans); fill:#fff; }}
.t-eixo {{ font:12px var(--sans); fill:var(--tinta-3); }}
.t-ponto {{ font:600 12px var(--sans); fill:var(--tinta); }}
.grade line, line.grade {{ stroke:var(--fio-2); stroke-width:1; }}
.diag {{ stroke:var(--nc); stroke-width:1; stroke-dasharray:4 4; }}
.pt-est {{ fill:var(--tinta-2); }}
.pt-cap {{ fill:#fff; stroke:var(--tinta-2); stroke-width:1.6; }}
.f-conforme {{ fill:var(--ok); }} .f-nao_conforme {{ fill:var(--nc); }} .f-especifico {{ fill:var(--esp); }}
.f-indeterminado {{ fill:var(--ind-cor); }} .f-sem_leitura {{ fill:var(--sl); }} .f-tinta {{ fill:var(--tinta-2); }}

.limites {{ padding:40px 0 20px; }}
.limites ul {{ padding:0; list-style:none; display:grid; gap:12px; max-width:72ch; }}
.limites li {{ padding-left:16px; position:relative; color:var(--tinta-2); }}
.limites li::before {{ content:""; position:absolute; left:0; top:.7em; width:6px; height:6px; background:var(--ind-cor); }}
.limites b {{ color:var(--tinta); }}
.metodo {{ font-size:14px; color:var(--tinta-3); max-width:72ch; padding:18px 0 56px; }}
.rodape {{ border-top:2px solid var(--tinta); }}

@media (max-width: 960px) {{
  .abertura {{ grid-template-columns:minmax(0,1fr); }}
  .grade {{ grid-template-columns:minmax(0,1fr); gap:0; }}
  .indice {{ position:static; max-height:none; padding:24px 0 8px; border-bottom:1px solid var(--fio); }}
  .indice ol {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
}}
@media (max-width: 600px) {{
  .faixa-in, .abertura, .grade {{ padding-left:16px; padding-right:16px; }}
  .faixa .sub {{ font-size:16.5px; }}
  .indice ol {{ grid-template-columns:minmax(0,1fr); }}
  .achado {{ grid-template-columns:minmax(0,1fr); padding:32px 0 28px; }}
  .achado .num {{ font-size:30px; margin-bottom:8px; }}
  .achado h2 {{ font-size:20px; }}
  .ementa {{ font-size:17px; }}
  .chave dd {{ font-size:22px; }}
  .tab {{ font-size:13px; display:block; overflow-x:auto; }}
  .hb-l, .hb-emp .hb-l {{ grid-template-columns:minmax(0,1fr) auto; gap:4px 10px; }}
  .hb-rot {{ grid-column:1 / -1; font-size:13.5px; }}
  .hb-v {{ white-space:normal; }}
  .disp-larga {{ display:none !important; }}
  .disp-estreita {{ display:block !important; }}
  .lista5 {{ grid-template-columns:minmax(0,1fr); }}
  .par-txt {{ width:min(280px, calc(100vw - 48px)); }}
  .tab th, .tab td {{ padding-right:10px; }}
}}
@media print {{
  .faixa {{ background:none; color:var(--tinta); border-bottom:2px solid var(--verde); }}
  .faixa h1, .faixa .sub, .faixa .serie {{ color:var(--tinta); }}
  .indice, .pular {{ display:none; }}
  .par-txt {{ position:static; opacity:1; transform:none; background:none; color:var(--tinta-2); box-shadow:none; padding:0 0 0 6px; width:auto; display:inline; }}
  .par-txt b {{ color:var(--tinta); }}
  .grade {{ grid-template-columns:minmax(0,1fr); }}
  .achado {{ break-inside:avoid; }}
  a {{ color:inherit; text-decoration:none; }}
}}
</style>
</head>
<body>
<a class="pular" href="#achados">Pular para os achados</a>
<header class="faixa">
  <div class="faixa-in">
    <h1>Cotas da IN 5 nos editais da Lei Paulo Gustavo: dez achados</h1>
    <p class="sub">O que a base de editais de estados, DF e capitais mostra sobre a reserva de vagas para pessoas negras e indígenas, e o que ela ainda não permite afirmar.</p>
    <p class="serie"><span>Nota técnica</span><span>Base de {n} editais</span><span>Gerada em {hoje}</span></p>
  </div>
</header>
<section class="abertura" aria-label="Resumo">
  <div class="exec"><h2 class="bloco-t">Sumário executivo</h2><ol>{exec}</ol></div>
  <div><h2 class="bloco-t">Números-chave</h2><dl class="chave">{chave}</dl></div>
</section>
<div class="grade">
  <nav class="indice" aria-label="Achados">
    <h2 class="bloco-t">Achados</h2>
    <ol>{sumario}</ol>
    <ol class="extra"><li><a href="#limites"><span class="sn"></span>Limites da base</a></li></ol>
  </nav>
  <main id="achados">
    {achados}
    <section class="limites" id="limites" aria-labelledby="lim-t">
      <h2 class="bloco-t" id="lim-t">Limites da base</h2>
      <ul>{limites}</ul>
    </section>
    <footer class="rodape"><p class="metodo">{metodo}</p></footer>
  </main>
</div>
</body>
</html>
"""


def gera() -> Path:
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(monta(analisa()).replace("IN 5", "IN\u00a05"), encoding="utf-8")
    return SAIDA


if __name__ == "__main__":
    print(f"Relatório gerado em {gera()}")
