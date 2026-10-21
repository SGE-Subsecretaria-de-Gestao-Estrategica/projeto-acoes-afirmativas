"""Painel de conformidade das cotas da IN MinC nº 5/2023 nos editais da LPG.

Rodar a partir de src/:
    python -m dashboard.app        # http://127.0.0.1:8050
"""
from urllib.parse import parse_qs, quote, unquote

import pandas as pd
from dash import Dash, Input, Output, dcc, html

from dashboard import dados as d

FONTES = ("https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400"
          "&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap")

app = Dash(__name__, title="Cotas LPG · IN 5", external_stylesheets=[FONTES],
           suppress_callback_exceptions=True, update_title=None)


# ---------------------------------------------------------------- peças

def barra(c: dict, grande: bool = False) -> html.Div:
    partes = [html.Span(className=f"seg-{s}", style={"flexGrow": c[s]}) for s in d.STATUS if c.get(s)]
    rotulo = ", ".join(f"{c[s]} {d.ROTULO_STATUS[s].lower()}" for s in d.STATUS if c.get(s)) or "sem editais"
    return html.Div(partes, className="barra barra-g" if grande else "barra", role="img",
                    **{"aria-label": rotulo})


def remissao(par: str | None) -> html.Span | None:
    """Etiqueta do parágrafo da IN 5; o texto resumido aparece em foco ou hover."""
    if not par:
        return None
    return html.Span([par, html.Span([html.B(f"IN 5, {par}"), " ", d.DISPOSITIVOS[par]], className="par-txt",
                                     role="tooltip")],
                     className="par", tabIndex="0")


def selo(status: str) -> html.Span:
    return html.Span(d.ROTULO_STATUS.get(status, status), className=f"selo st-{status}")


def ponto_valor(v: float) -> html.Span | None:
    m, rot = d.magnitude(v)
    if not m:
        return None
    return html.Span(className=f"mag mag-{m}", title=rot, **{"aria-hidden": "true"})


RAMPA_TXT = "Tamanho do ponto em rampa fixa de valor: " + "; ".join(r for _, _, r in d.RAMPA_VALOR)


def plural(n: int, um: str, varios: str) -> str:
    return f"{n} {um if n == 1 else varios}"


def ementa_ente(l: dict) -> list:
    c = l["contagem"]
    if not c["total"]:
        return ["nenhum edital na base"]
    if l["dispositivo"]:
        txt = f"{plural(l['n_motivo'], 'edital', 'editais')}: {l['motivo']}"
        return [remissao(l["dispositivo"]), txt]
    partes = [plural(c["conforme"], "conforme", "conformes")]
    if c["especifico"]:
        partes.append(plural(c["especifico"], "específico", "específicos"))
    if c["indeterminado"]:
        partes.append(plural(c["indeterminado"], "indeterminado", "indeterminados"))
    if c["sem_leitura"]:
        partes.append(f"{c['sem_leitura']} sem leitura")
    return [", ".join(partes[:-1]) + (" e " if len(partes) > 1 else "") + partes[-1]]


def link_ente(tipo: str, ente: str) -> str:
    return f"/ente/{tipo}/{quote(ente)}"


def linha_ente(l: dict) -> dcc.Link | html.Div:
    c = l["contagem"]
    filhos = [
        html.Span(l["ente"], className="nm"),
        html.Span(c["total"] or "—", className="num"),
        html.Div(barra(c), className="meio"),
        html.Span(l["situacao"], className="sit"),
        html.Div(ementa_ente(l), className="ementa"),
    ]
    if not c["total"]:
        return html.Div(filhos, className="linha linha-vazio")
    return dcc.Link(filhos, href=link_ente(l["tipo"], l["ente"]), className=f"linha linha-{l['classe']}")


def medidor(rotulo: str, r: dict, minimo: float) -> html.Div:
    p = r["perc"]
    escala = 0.3  # o medidor vai de 0 a 30%
    return html.Div([
        html.Div([html.Span(rotulo), html.B(d.pct(p))], className="med-cab"),
        html.Div([html.Span(className="med-ch", style={"width": f"{min((p or 0) / escala, 1) * 100:.1f}%"}),
                  html.Span(className="med-min", style={"left": f"{minimo / escala * 100:.1f}%"},
                            title=f"mínimo da IN 5: {d.pct(minimo, 0)}")],
                 className="med", role="img",
                 **{"aria-label": f"{rotulo}: {d.pct(p)} das vagas; mínimo {d.pct(minimo, 0)}"}),
        html.Div(f"{d.inteiro(r['vagas'])} de {d.inteiro(r['base'])} vagas · valor {d.pct(r['valor_perc'])}",
                 className="med-nota"),
    ], className="medidor")


def resumo(tipo: str, df: pd.DataFrame, grupo: str) -> html.Div:
    r = d.resumo_tipo(df, tipo, grupo)
    itens = [("Entes sem não conforme", f"{r['entes_sem_nc']}/{r['entes_base']}")]
    itens += [(d.ROTULO_STATUS[s], d.inteiro(r[s])) for s in d.STATUS if s != "sem_leitura" or r[s]]
    reserva = r["reserva"]
    meds = []
    if grupo in ("in5", "negras"):
        meds.append(medidor("Vagas para pessoas negras", reserva["negras"], 0.20))
    if grupo in ("in5", "indigenas"):
        meds.append(medidor("Vagas para pessoas indígenas", reserva["indigenas"], 0.10))
    return html.Div([
        html.Dl([html.Div([html.Dt(k), html.Dd(v)], className=f"dl-{i}") for i, (k, v) in enumerate(itens)],
                className="totais"),
        barra({s: r[s] for s in d.STATUS}, grande=True),
        html.Div(meds, className="medidores"),
        html.P(f"Percentuais agregados sobre os {reserva['negras']['editais']} editais com vagas totais e "
               "reservadas informadas.", className="nota"),
    ], className="resumo")


def secao_tipo(tipo: str, df: pd.DataFrame, grupo: str, ordem: str, largo: bool = False) -> html.Section:
    r = d.resumo_tipo(df, tipo, grupo)
    linhas = d.por_ente(df, tipo, ordem)
    busca_ativa = len(df) < len(d.carrega()["editais"])
    if busca_ativa:
        linhas = [l for l in linhas if l["contagem"]["total"]]
    unidade = "UFs" if tipo == "ESTADO" else "capitais"
    meta = f"{r['entes_base']} de {r['entes_esperados']} {unidade} na base · {plural(r['editais'], 'edital', 'editais')}"
    corpo = [html.Div([html.Span("Ente"), html.Span("Editais", className="num"),
                       html.Span("Editais por situação"), html.Span("Situação", className="sit")],
                      className="colh", **{"aria-hidden": "true"})]
    corpo += [linha_ente(l) for l in linhas] if linhas else [vazio("Nenhum edital deste tipo de ente com esses filtros.")]
    if r["ausentes"] and not busca_ativa:
        corpo.append(html.P(f"Sem editais na base: {', '.join(r['ausentes'])}.", className="nota"))
    return html.Section([
        html.Div([html.H2(d.TIPOS[tipo]), html.Span(meta, className="meta")], className="sec-cab"),
        resumo(tipo, df, grupo),
        html.Div(corpo, className="tabela-entes", role="list"),
    ], className="secao secao-larga" if largo else "secao")


def vazio(msg: str) -> html.Div:
    return html.Div([html.P(msg, className="vazio-t"),
                     html.P("Altere o grupo, a modalidade ou limpe a busca.", className="vazio-s")], className="vazio")


def cabecalho(titulo: str, sub=None, extra=None) -> html.Header:
    return html.Header([html.Div([html.H1(titulo), html.P(sub, className="sub") if sub else None]),
                        extra], className="cab")


def legenda() -> html.Div:
    return html.Div([html.Span(d.ROTULO_STATUS[s], className=f"leg leg-{s}") for s in d.STATUS],
                    className="legenda", **{"aria-hidden": "true"})


def linha_total(df: pd.DataFrame) -> str:
    c = df["status"].value_counts()
    partes = [f"{d.inteiro(len(df))} editais"] + [f"{d.inteiro(c.get(s, 0))} {d.ROTULO_STATUS[s].lower()}"
                                                   for s in d.STATUS if c.get(s, 0)]
    return " · ".join(partes)


# ---------------------------------------------------------------- páginas

def pg_visao(df, grupo, ordem):
    return [cabecalho("Cumprimento da IN\u00a05 por tipo de ente", linha_total(df), legenda()),
            html.Div([secao_tipo("ESTADO", df, grupo, ordem), secao_tipo("CAPITAL", df, grupo, ordem)],
                     className="duas")]


def pg_tipo(tipo, df, grupo, ordem):
    sub = df[df["tipo_ente"] == tipo]
    return [cabecalho(d.TIPOS[tipo], linha_total(sub), legenda()),
            html.Div([secao_tipo(tipo, df, grupo, ordem, largo=True)], className="uma")]


def tabela_editais(df: pd.DataFrame, fila: str, mostra_ente: bool = True) -> html.Div:
    if df.empty:
        return vazio("Nenhum edital com esses filtros.")
    cab = (["Ente"] if mostra_ente else []) + ["Edital", "Modalidade", "Valor", "Vagas", "Situação"]
    linhas = []
    for _, e in df.iterrows():
        motivos = [m for m in str(e["motivo"]).split(" | ") if m and m != "nan"] if e["status"] != "conforme" else []
        cel_ed = html.Div([
            html.Span(e["arquivo_pdf"], className="arq"),
            html.Span(e["objeto"] if isinstance(e["objeto"], str) else "objeto não extraído", className="obj"),
            html.Div([html.Span([remissao(d.dispositivo(m)), d.ementa(m)], className="mot") for m in motivos],
                     className="mots") if motivos else None,
        ])
        cels = ([html.Div([html.Span(e["ente"], className="nm"),
                           html.Span("Estado" if e["tipo_ente"] == "ESTADO" else "Capital", className="tipo")])]
                if mostra_ente else [])
        cels += [cel_ed,
                 html.Span(d.MODALIDADES.get(e["modalidade"], "—")),
                 html.Span([ponto_valor(e["valor_total"]), d.brl(e["valor_total"], curto=True)], className="valor"),
                 html.Span(d.inteiro(e["vagas_totais"]), className="num"),
                 selo(e["status"])]
        linhas.append(dcc.Link(cels, href=f"/edital/{e['id']}?fila={fila}", className=f"ed st-row-{e['status']}"))
    cab_el = [html.Span(c, title=RAMPA_TXT, className="cab-valor") if c == "Valor" else html.Span(c) for c in cab]
    return html.Div([html.Div(cab_el, className="ed ed-cab"), html.P(RAMPA_TXT + ".", className="nota rampa")] + linhas,
                    className="tabela-ed" + ("" if mostra_ente else " sem-ente"))


def pg_editais(df, status):
    abas = [("todos", "Todos", len(df))] + [(s, d.ROTULO_STATUS[s], int((df["status"] == s).sum()))
                                            for s in d.STATUS]
    sel = df if status == "todos" else df[df["status"] == status]
    sel = sel.sort_values(["tipo_ente", "ente", "mes"], key=lambda s: s.map(d._chave) if s.name == "ente" else s,
                          ascending=[False, True, True])
    nav = html.Nav([dcc.Link([nome, html.Span(d.inteiro(n), className="cont")], href=f"/editais?status={k}",
                             className="aba aba-on" if k == status else "aba")
                    for k, nome, n in abas if n or k == status], className="abas", **{"aria-label": "Situação"})
    titulo = "Editais" if status == "todos" else f"Editais · {d.ROTULO_STATUS[status].lower()}"
    return [cabecalho(titulo, f"{plural(len(sel), 'edital', 'editais')} com os filtros atuais"), nav,
            html.Div(tabela_editais(sel, status), className="uma")]


def pg_ente(tipo, ente, df, grupo):
    sub = df[(df["tipo_ente"] == tipo) & (df["ente"] == ente)].sort_values("mes")
    l = next((x for x in d.por_ente(df, tipo) if x["ente"] == ente), None)
    if l is None:
        return pg_404()
    c = l["contagem"]
    r = d.reserva(sub)
    fatos = [("Editais", d.inteiro(c["total"])), ("Valor total", d.brl(sub["valor_total"].sum(), curto=True)),
             ("Vagas informadas", d.inteiro(sub["vagas_totais"].sum())),
             ("Vagas p/ negros", d.pct(r["negras"]["perc"])), ("Vagas p/ indígenas", d.pct(r["indigenas"]["perc"]))]
    return [
        html.Div(dcc.Link(["Visão geral"], href="/", className="volta"), className="trilha"),
        cabecalho(ente, f"{'Estado' if tipo == 'ESTADO' else 'Capital'} · {l['situacao']}",
                  html.Span(l["situacao"], className=f"sit-g sit-{l['classe']}")),
        html.Div([
            html.Dl([html.Div([html.Dt(k), html.Dd(v)]) for k, v in fatos], className="totais"),
            barra(c, grande=True),
            html.P(ementa_ente(l), className="ementa ementa-g"),
        ], className="resumo resumo-ente"),
        html.Div(tabela_editais(sub, "ente", mostra_ente=False), className="uma"),
    ]


def fila_ids(df: pd.DataFrame, fila: str, e: pd.Series) -> list[str]:
    if fila == "ente" or fila not in d.STATUS + ["todos"]:
        sub = df[(df["tipo_ente"] == e["tipo_ente"]) & (df["ente"] == e["ente"])].sort_values("mes")
    else:
        sub = df if fila == "todos" else df[df["status"] == fila]
        sub = sub.sort_values(["tipo_ente", "ente", "mes"], key=lambda s: s.map(d._chave) if s.name == "ente" else s,
                              ascending=[False, True, True])
    return list(sub["id"])


def fato(rot, val, campo, evs):
    tem = campo in set(evs["campo"])
    v = html.A(val, href=f"#ev-{campo}", className="prova", title="ver trecho do edital") if tem else val
    return html.Div([html.Dt(rot), html.Dd(v)])


def pg_edital(id_, fila, df, grupo):
    info = d.edital(id_)
    if info is None:
        return pg_404()
    e, evs = info["linha"], info["evidencias"]
    st = df.set_index("id")["status"].get(id_, "sem_leitura")
    ids = fila_ids(df, fila, e)
    i = ids.index(id_) if id_ in ids else -1
    ant = ids[i - 1] if i > 0 else None
    prox = ids[i + 1] if 0 <= i < len(ids) - 1 else None
    nome_fila = "deste ente" if fila == "ente" else ("de todos os editais" if fila == "todos"
                                                      else f"de {d.ROTULO_STATUS.get(fila, fila).lower()}s")
    navega = html.Div([
        dcc.Link([html.Span(className="ico ico-esq"), "Anterior"], href=f"/edital/{ant}?fila={fila}",
                 className="btn", id="tecla-k") if ant else html.Span("Anterior", className="btn btn-off"),
        html.Span(f"{i + 1} de {len(ids)} {nome_fila}" if i >= 0 else "fora da fila atual", className="pos"),
        dcc.Link(["Próximo", html.Span(className="ico ico-dir")], href=f"/edital/{prox}?fila={fila}",
                 className="btn", id="tecla-j") if prox else html.Span("Próximo", className="btn btn-off"),
        html.Span(["teclas ", html.Kbd("k"), " ", html.Kbd("j")], className="dica"),
    ], className="navega")

    grupos = []
    for g, nome, minimo in (("negras", "Pessoas negras", 0.2), ("indigenas", "Pessoas indígenas", 0.1)):
        stg = e[f"status_{g}"] if isinstance(e[f"status_{g}"], str) else "sem_leitura"
        mot = e[f"motivo_{g}"] if isinstance(e[f"motivo_{g}"], str) else "extração truncada; edital não classificado"
        grupos.append(html.Div([
            html.Div([html.H3(nome), selo(stg)], className="g-cab"),
            html.P([remissao(d.dispositivo(mot)), d.ementa(mot)], className="ementa"),
            html.Dl([html.Div([html.Dt("Percentual previsto"), html.Dd(d.pct(e[f"perc_cotas_{g}"], 0))]),
                     html.Div([html.Dt("Vagas reservadas"), html.Dd(d.inteiro(e[f"vagas_cotas_{g}"]))]),
                     html.Div([html.Dt("Mínimo calculado"), html.Dd(d.inteiro(e[f"vagas_min_{g}"]))]),
                     html.Div([html.Dt("Valor estimado"), html.Dd(d.brl(e[f"valor_cotas_{g}"], curto=True))])],
                    className="mini"),
        ], className=f"grupo st-row-{stg}"))

    cats = info["categorias"]
    tab_cat = None
    if not cats.empty:
        cols = [("nome", "Categoria"), ("vagas", "Vagas"), ("valor_por_vaga", "Valor por vaga"),
                ("vagas_negras", "Negros"), ("vagas_indigenas", "Indígenas"), ("vagas_pcd", "PcD"),
                ("vagas_quilombolas", "Quilombolas"), ("vagas_lgbtqia", "LGBTQIA+")]
        cols = [(k, r) for k, r in cols if k in ("nome", "vagas") or cats[k].notna().any()]
        corpo = []
        for _, c in cats.iterrows():
            cels = []
            for k, _r in cols:
                if k == "nome":
                    cels.append(html.Td(c[k], className="cat-nome"))
                elif k == "valor_por_vaga":
                    cels.append(html.Td(d.brl(c[k]), className="num", **{"data-rot": _r}))
                else:
                    falta = k in ("vagas_negras", "vagas_indigenas") and pd.isna(c[k])
                    cels.append(html.Td("sem reserva" if falta else d.inteiro(c[k]),
                                        className="num falta" if falta else "num", **{"data-rot": _r}))
            corpo.append(html.Tr(cels))
        tab_cat = html.Div([html.H2(f"Categorias · {len(cats)}"),
                            html.Div(html.Table([html.Thead(html.Tr([html.Th(r, className="" if k == "nome" else "num")
                                                                     for k, r in cols])),
                                                 html.Tbody(corpo)], className="tab"), className="rolagem")],
                           className="bloco")

    oc = info["outras_cotas"]
    bloco_oc = html.Div([html.H2("Outras cotas"),
                         html.Ul([html.Li([html.Span(o["grupo"]), html.Span(d.pct(o["percentual"], 0) if pd.notna(o["percentual"])
                                                                            else f"{d.inteiro(o['vagas'])} vagas", className="num")])
                                  for _, o in oc.iterrows()], className="lista-oc")]
                        , className="bloco") if not oc.empty else None

    bloco_ev = html.Div([html.H2(f"Evidências · {len(evs)} trechos"),
                         html.Ol([html.Li([html.Div([html.Span(d.rotulo_campo(ev["campo"]), className="campo"),
                                                     html.Span(f"p. {ev['pagina']}", className="pag")], className="ev-cab"),
                                           html.Blockquote(ev["trecho"])], id=f"ev-{ev['campo']}", className="ev")
                                  for _, ev in evs.drop_duplicates("campo").iterrows()], className="evs")],
                        className="bloco") if not evs.empty else html.Div(
        [html.H2("Evidências"), html.P("Nenhum trecho registrado para este edital.", className="nota")], className="bloco")

    fatos = html.Dl([fato("Valor total", d.brl(e["valor_total"]), "valor_total", evs),
                     fato("Vagas totais", d.inteiro(e["vagas_totais"]), "vagas_totais", evs),
                     html.Div([html.Dt("Modalidade"), html.Dd(d.MODALIDADES.get(e["modalidade"], "—"))]),
                     html.Div([html.Dt("Área"), html.Dd(e["area_cultural"] if isinstance(e["area_cultural"], str) else "—")]),
                     html.Div([html.Dt("Páginas"), html.Dd(d.inteiro(e["paginas"]))]),
                     html.Div([html.Dt("Leitura"), html.Dd("texto" if e["modo_leitura"] == "texto" else "imagem (PDF escaneado)")])],
                    className="totais fatos")

    obs = e["observacoes"] if isinstance(e["observacoes"], str) else None
    return [
        html.Div([dcc.Link(e["ente"], href=link_ente(e["tipo_ente"], e["ente"]), className="volta"), navega],
                 className="trilha"),
        cabecalho(e["arquivo_pdf"], f"{e['ente']} · {'Estado' if e['tipo_ente'] == 'ESTADO' else 'Capital'}",
                  html.Span(d.ROTULO_STATUS.get(st, st), className=f"sit-g sit-st-{st}")),
        html.Div([
            html.Div([
                html.Div([html.H2("Objeto"),
                          html.P(e["objeto"] if isinstance(e["objeto"], str) else "Objeto não extraído.",
                                 className="objeto"),
                          fatos, html.P(obs, className="obs") if obs else None], className="bloco"),
                html.Div(grupos, className="grupos"),
                tab_cat, bloco_oc,
            ], className="col-a"),
            html.Aside(bloco_ev, className="col-b"),
        ], className="ficha"),
    ]


def pg_outras(df):
    t = d.outras_cotas_por_tipo()
    tot = d.carrega()["editais"].groupby("tipo_ente").size()
    linhas = []
    for g, r in t.iterrows():
        cels = [html.Span(d.GRUPOS_OUTRAS.get(g, g), className="nm")]
        for tipo in ("ESTADO", "CAPITAL"):
            p = r[f"perc_{tipo}"]
            cels.append(html.Div([html.Div(html.Span(style={"width": f"{p * 100:.1f}%"}), className="hbar"),
                                  html.Span(f"{d.inteiro(r[tipo])} · {d.pct(p, 0)}", className="num")], className="hcel"))
        linhas.append(html.Div(cels, className="oc-linha"))
    esp = df[df["status"] == "especifico"].sort_values(["tipo_ente", "ente"], ascending=[False, True])
    return [
        cabecalho("Outras cotas e editais específicos",
                  "Cotas além das da IN 5, contadas por edital que as prevê (aba outras_cotas)"),
        html.Div([
            html.Section([
                html.Div([html.Span("Grupo"), html.Span(f"Estados e DF · de {tot['ESTADO']} editais"),
                          html.Span(f"Capitais · de {tot['CAPITAL']} editais")], className="oc-linha oc-cab"),
                *linhas], className="secao secao-larga"),
            html.Section([html.Div([html.H2("Editais específicos"),
                                    html.Span(plural(len(esp), "edital dirigido", "editais dirigidos") +
                                              " integralmente a um grupo", className="meta")], className="sec-cab"),
                          tabela_editais(esp, "especifico")], className="secao secao-larga"),
        ], className="uma"),
    ]


def pg_404():
    return [cabecalho("Página não encontrada"),
            html.Div([html.P("O endereço não corresponde a um ente ou edital da base.", className="vazio-t"),
                      dcc.Link("Voltar à visão geral", href="/", className="btn")], className="vazio")]


# ---------------------------------------------------------------- casca

def opcoes(dic):
    return [{"label": v, "value": k} for k, v in dic.items()]


filtros = html.Div([
    html.Div([html.Span("Grupo", className="f-rot", id="rot-grupo"),
              dcc.RadioItems(id="grupo", options=opcoes(d.GRUPOS), value="in5", className="seg", inline=True,
                             persistence=True, persistence_type="session")], className="f"),
    html.Div([html.Span("Modalidade", className="f-rot"),
              dcc.RadioItems(id="modalidade", value="todas", className="seg", inline=True, persistence=True,
                             persistence_type="session",
                             options=[{"label": "Todas", "value": "todas"},
                                      {"label": "Fomento", "value": "fomento_execucao"},
                                      {"label": "Prêmio", "value": "premio"},
                                      {"label": "Outras", "value": "outras"}])], className="f"),
    html.Div([html.Span("Ordem", className="f-rot"),
              dcc.RadioItems(id="ordem", value="alfabetica", className="seg", inline=True, persistence=True,
                             persistence_type="session",
                             options=[{"label": "Alfabética", "value": "alfabetica"},
                                      {"label": "Por situação", "value": "situacao"},
                                      {"label": "Nº de editais", "value": "editais"}])], className="f f-ordem"),
    html.Label([html.Span("Buscar ente, arquivo ou objeto", className="so-leitor"),
                dcc.Input(id="busca", type="search", placeholder="Buscar ente, arquivo ou objeto", debounce=0.3,
                          className="busca", autoComplete="off")], className="busca-rot"),
], className="filtros", id="filtros")

app.layout = html.Div([
    dcc.Location(id="url"),
    html.A("Pular para o conteúdo", href="#conteudo", className="pular"),
    html.Nav(id="trilho", className="trilho", **{"aria-label": "Navegação do painel"}),
    html.Main([filtros, html.Div(id="conteudo", className="conteudo", tabIndex="-1")], className="principal"),
], className="casca")


def item(href, rot, n, ativo):
    return dcc.Link([html.Span(rot), html.Span(" (página atual)", className="so-leitor") if ativo else None,
                     html.Span(n, className="cont") if n is not None else None], href=href,
                    className="nav-on" if ativo else None)


def trilho(path, query, df):
    c = df["status"].value_counts()
    st = query.get("status", [""])[0]
    tipos = df.groupby("tipo_ente")["ente"].nunique()
    return [
        html.Div([html.B("Cotas LPG"), html.Span("Conformidade com a IN MinC nº 5/2023")], className="marca"),
        html.Div("Painel", className="nav-sec"),
        item("/", "Visão geral", None, path == "/"),
        item("/estados", "Estados e DF", tipos.get("ESTADO", 0), path == "/estados"),
        item("/capitais", "Capitais", tipos.get("CAPITAL", 0), path == "/capitais"),
        item("/editais?status=todos", "Editais", d.inteiro(len(df)), path == "/editais" and st in ("", "todos")),
        html.Div("Revisão", className="nav-sec"),
        item("/editais?status=nao_conforme", "Não conformes", d.inteiro(c.get("nao_conforme", 0)),
             path == "/editais" and st == "nao_conforme"),
        item("/editais?status=indeterminado", "Indeterminados", d.inteiro(c.get("indeterminado", 0)),
             path == "/editais" and st == "indeterminado"),
        item("/editais?status=especifico", "Específicos", d.inteiro(c.get("especifico", 0)),
             path == "/editais" and st == "especifico"),
        item("/outras-cotas", "Outras cotas", None, path == "/outras-cotas"),
        html.Div([html.Span("Fonte: lpg_editais.xlsx"), html.Span("Regras do art. 5º, §§ 2º a 4º, aplicadas em código")],
                 className="rodape"),
    ]


@app.callback(Output("conteudo", "children"), Output("trilho", "children"), Output("filtros", "className"),
              Input("url", "pathname"), Input("url", "search"), Input("grupo", "value"),
              Input("modalidade", "value"), Input("ordem", "value"), Input("busca", "value"))
def rota(path, search, grupo, modalidade, ordem, busca):
    path = (path or "/").rstrip("/") or "/"
    query = parse_qs((search or "").lstrip("?"))
    try:
        df = d.editais(grupo or "in5", modalidade or "todas", busca or "")
    except FileNotFoundError:
        erro = [cabecalho("Planilha não encontrada"),
                html.Div([html.P(f"O painel lê {d.PLANILHA}.", className="vazio-t"),
                          html.P("Gere-a com: python main.py consolidar", className="vazio-s")], className="vazio")]
        return erro, [], "filtros oculto"
    partes = path.strip("/").split("/")
    mostra_filtros, mostra_ordem = True, False
    if path == "/":
        pagina, mostra_ordem = pg_visao(df, grupo, ordem), True
    elif path in ("/estados", "/capitais"):
        pagina, mostra_ordem = pg_tipo("ESTADO" if path == "/estados" else "CAPITAL", df, grupo, ordem), True
    elif path == "/editais":
        status = query.get("status", ["todos"])[0]
        pagina = pg_editais(df, status if status in d.STATUS else "todos")
    elif partes[0] == "ente" and len(partes) == 3 and partes[1] in d.TIPOS:
        pagina = pg_ente(partes[1], unquote(partes[2]), df, grupo)
    elif partes[0] == "edital" and len(partes) == 2:
        pagina, mostra_filtros = pg_edital(partes[1], query.get("fila", ["ente"])[0], df, grupo), False
    elif path == "/outras-cotas":
        pagina, mostra_filtros = pg_outras(df), False
    else:
        pagina = pg_404()
    classe = "filtros" + ("" if mostra_filtros else " oculto") + ("" if mostra_ordem else " sem-ordem")
    return pagina, trilho(path, query, df), classe


server = app.server

if __name__ == "__main__":
    app.run(debug=False)
