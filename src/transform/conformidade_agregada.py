"""Conformidade dos editais da LPG com a IN MinC nº 5/2023, pelo critério agregado.

Avalia as cotas para pessoas negras e indígenas a partir da tabela consolidada
(uma linha por edital), e não do JSON extraído. Diferenças em relação a
`transform/conformidade.py`:

- em editais com categorias, o mínimo é calculado sobre a SOMA das vagas de todas
  as categorias, e não categoria por categoria (o §3º não é verificado);
- o número de vagas reservadas prevalece sobre o percentual declarado.

Origem das vagas reservadas de cada grupo, em ordem de prioridade:
    1. explícitas nas categorias: soma de `vagas_{g}` da aba `categorias`
       (categoria sem número conta como 0);
    2. informadas na aba `editais`: `vagas_cotas_{g}`. Também prevalece sobre o passo 1
       quando a soma das categorias é PARCIAL (alguma categoria sem número);
    3. calculadas do percentual: arred(`perc_cotas_{g}` × base).

Regras completas, com fórmulas e fluxograma: notebooks/regras_conformidade_in5.md.
Cada regra aparece no código com o mesmo código do documento (E, G0 a G7) e é
gravada no início do motivo (ex.: "G2: 15 vagas reservadas < mínimo 20").

Colunas de entrada usadas:
    aba editais:     id, edital_especifico_grupo, possui_categorias, vagas_totais,
                     numero_vagas_categoria_total, perc_cotas_{g}, vagas_cotas_{g}, motivo_{g}
    aba categorias:  id, vagas, vagas_negras, vagas_indigenas
    (g em {negras, indigenas})

Colunas de saída (ver `aplica_conformidade`):
    conformidade_in5        conforme | nao_conforme | indeterminado
    motivo_conformidade     regra e motivo de cada grupo que não ficou conforme
    vagas_cotas_{g}_in5     vagas reservadas usadas na avaliação
    vagas_min_{g}_in5       mínimo de vagas exigido pela IN
    origem_vagas_{g}_in5    categorias | editais | percentual (de onde veio o número)
    ajuste_manual_in5       True se o edital recebeu ajuste manual pontual (ver abaixo)
    vagas_categorias_total, vagas_categorias_{g}   agregados da aba categorias
    categorias_sem_{g}      nº de categorias do edital sem `vagas_{g}` (> 0 = soma parcial)

!!! Ajustes manuais pontuais, por decisão de negócio caso a caso. Não são regra:
    - `settings.COTA_AJUSTES_MANUAIS_CATEGORIAS` sobrescreve células da aba `categorias` antes
      da agregação (hoje: Curitiba, 2023-92_CAP-CURITIBA_LPG.pdf); ver `aplica_ajustes_manuais`;
    - `settings.COTA_AJUSTES_MANUAIS_EDITAIS` sobrescreve células da aba `editais` antes da
      avaliação (hoje: Amazonas, 2023-04_EST-AMAZONAS_LPG.pdf, específico para pessoas negras);
      ver `aplica_ajustes_manuais_editais`;
    - `settings.COTA_AJUSTES_MANUAIS_IGNORA_CATEGORIAS` faz a aba `categorias` ser ignorada em
      editais específicos (hoje: Amazonas, 2023-08_EST-AMAZONAS_LPG.pdf), valendo a base e as
      vagas declaradas na aba `editais`; ver `aplica_conformidade`;
    - `settings.COTA_AJUSTES_MANUAIS_STATUS` define o resultado final de editais específicos
      (hoje: Paraná, 2023-13_EST-PARANA_LPG.pdf); ver `aplica_conformidade`.
"""
import pandas as pd

from config import settings
from transform.sanitize import arredonda_in5, num

STATUS_CONFORME = "conforme"
STATUS_NAO_CONFORME = "nao_conforme"
STATUS_INDETERMINADO = "indeterminado"


def aplica_ajustes_manuais(categorias: pd.DataFrame) -> tuple[pd.DataFrame, set]:
    """!!! EXCEÇÃO PONTUAL, NÃO É REGRA !!!

    Sobrescreve células da aba `categorias` conforme `settings.COTA_AJUSTES_MANUAIS_CATEGORIAS`.
    São decisões de negócio caso a caso (ex.: Curitiba, 2023-92_CAP-CURITIBA_LPG.pdf, modalidade 4
    do inciso I com 2 vagas para pessoas negras), e não um critério da análise.

    Retorna (categorias ajustadas, ids dos editais ajustados). Falha se um ajuste não encontrar
    exatamente uma categoria, para que uma mudança na planilha não faça o ajuste sumir em silêncio.
    """
    out = categorias.copy()
    ids = set()
    for aj in settings.COTA_AJUSTES_MANUAIS_CATEGORIAS:
        alvo = (out["id"] == aj["id"]) & (out["nome"] == aj["nome"])
        if alvo.sum() != 1:
            raise ValueError(f"Ajuste manual não encontrou exatamente 1 categoria ({alvo.sum()}): {aj}")
        out.loc[alvo, aj["coluna"]] = aj["valor"]
        ids.add(aj["id"])
    return out, ids


def _alvo_edital(df: pd.DataFrame, aj: dict) -> pd.Series:
    """Máscara do edital de um ajuste manual: `arquivo_pdf` e, se informado, `id`.

    Falha se não encontrar exatamente um edital, para que uma mudança na planilha não faça
    o ajuste sumir em silêncio.
    """
    alvo = df["arquivo_pdf"] == aj["arquivo_pdf"]
    if aj.get("id") is not None:
        alvo &= df["id"] == aj["id"]
    if alvo.sum() != 1:
        raise ValueError(f"Ajuste manual não encontrou exatamente 1 edital ({alvo.sum()}): {aj}")
    return alvo


def aplica_ajustes_manuais_editais(df: pd.DataFrame) -> tuple[pd.DataFrame, set]:
    """!!! EXCEÇÃO PONTUAL, NÃO É REGRA !!!

    Sobrescreve células da aba `editais` conforme `settings.COTA_AJUSTES_MANUAIS_EDITAIS`.
    São decisões de negócio caso a caso (ex.: Amazonas, 2023-04_EST-AMAZONAS_LPG.pdf, tratado
    como edital específico para pessoas negras), e não um critério da análise.

    Retorna (editais ajustados, máscara dos editais ajustados). Ver `_alvo_edital`.
    """
    out = df.copy()
    ajustados = pd.Series(False, index=out.index)
    for aj in settings.COTA_AJUSTES_MANUAIS_EDITAIS:
        alvo = _alvo_edital(out, aj)
        # um campo ('coluna'/'valor') ou vários ('valores': {coluna: valor})
        valores = aj.get("valores") or {aj["coluna"]: aj["valor"]}
        for coluna, valor in valores.items():
            out.loc[alvo, coluna] = valor
        ajustados |= alvo
    return out, ajustados


def agrega_categorias(categorias: pd.DataFrame) -> pd.DataFrame:
    """Soma, por edital (`id`), as vagas da aba `categorias`.

    Retorna um DataFrame indexado por `id` com:
        vagas_categorias_total       soma de `vagas` de todas as categorias (base)
        vagas_categorias_{g}         soma de `vagas_{g}`; categoria sem número conta como 0.
                                     Fica vazio (NaN) se nenhuma categoria do edital traz o número,
                                     para não confundir "não informado" com "0 vagas".
        categorias_sem_{g}           nº de categorias sem `vagas_{g}`; > 0 indica soma parcial
                                     (usado na origem das vagas, passo 2 de `avalia_grupo`).
    """
    agg = {"vagas_categorias_total": ("vagas", lambda s: s.sum(min_count=1))}
    for g in settings.COTA_MIN:
        agg[f"vagas_categorias_{g}"] = (f"vagas_{g}", lambda s: s.sum(min_count=1))
        agg[f"categorias_sem_{g}"] = (f"vagas_{g}", lambda s: int(s.isna().sum()))
    return categorias.groupby("id").agg(**agg)


def base_calculo(r: pd.Series) -> float | None:
    """Base B: total de vagas sobre o qual se calcula o mínimo de cotas.

    - se o edital tem linhas na aba `categorias`: soma das vagas dessas categorias;
    - com categorias (possui_categorias == 1): `numero_vagas_categoria_total`;
    - sem categorias (ou não informado): `vagas_totais`.
    Se a coluna preferida estiver vazia, usa a outra. Sem nenhuma, retorna None.
    """
    vagas_aba_cat = num(r.get("vagas_categorias_total"))
    if vagas_aba_cat:
        return vagas_aba_cat
    vagas_totais = num(r["vagas_totais"])
    vagas_cat = num(r["numero_vagas_categoria_total"])
    if r["possui_categorias"] == 1:
        return vagas_cat or vagas_totais
    return vagas_totais or vagas_cat


def edital_especifico(r: pd.Series) -> str | None:
    """Regra E: devolve o grupo ('negras' ou 'indigenas') se o edital é específico dele, senão None."""
    grupo_edital = str(r["edital_especifico_grupo"]).strip().lower()
    for grupo, valores in settings.COTA_ESPECIFICO_GRUPO.items():
        if grupo_edital in valores:
            return grupo
    return None


def avalia_grupo(r: pd.Series, grupo: str) -> dict:
    """Aplica as regras G0 a G7 a um grupo ('negras' ou 'indigenas') de um edital.

    As regras são testadas em ordem; a primeira que se aplica decide.
    Retorna um dict com:
        status     conforme | nao_conforme | indeterminado
        motivo     código da regra + explicação (ex.: "G2: 15 vagas reservadas < mínimo 20")
        vagas      vagas reservadas usadas na avaliação
        vagas_min  mínimo de vagas exigido pela IN sobre a base
        origem     de onde veio `vagas`: categorias | editais | percentual (None se não há vagas)
    """
    m = settings.COTA_MIN[grupo]                 # percentual mínimo (caput)
    p = num(r[f"perc_cotas_{grupo}"])            # percentual declarado
    B = base_calculo(r)                          # base: soma das categorias ou total de vagas
    v_min = arredonda_in5(m * B) if B else None  # mínimo de vagas (§2º)

    # Origem das vagas reservadas, em ordem de prioridade --------------------------------
    # Vagas informadas na aba editais (vagas_cotas_{g}), exceto quando o pipeline as calculou
    # do percentual categoria a categoria (motivo_{g} começa com "percentual"/"cotas não
    # aplicadas"): esse número pode ficar 1 vaga abaixo e é refeito no passo 3.
    vagas_derivadas = str(r[f"motivo_{grupo}"]).startswith(settings.COTA_MOTIVO_VAGAS_DERIVADAS)
    v_editais = None if vagas_derivadas else num(r[f"vagas_cotas_{grupo}"])

    # 1. Explícitas nas categorias: soma de vagas_{g} da aba `categorias`.
    #    Prevalece sobre a aba editais, salvo soma parcial (passo 2b); categoria sem número conta como 0.
    v = num(r.get(f"vagas_categorias_{grupo}"))
    origem, rotulo = "categorias", "explícitas nas categorias"

    # 2. Informadas na aba editais. Usadas quando:
    #    a) a aba categorias não traz número para o grupo; ou
    #    b) a soma das categorias é PARCIAL (alguma categoria sem vagas_{g}) e a aba editais
    #       traz o número. Ex.: Fortaleza (2023-20) soma 12 vagas em 12 de 22 categorias,
    #       mas declara 18 vagas para pessoas negras -> vale 18 (mínimo arred(0,2 × 91) = 18).
    soma_parcial = (num(r.get(f"categorias_sem_{grupo}")) or 0) > 0
    if v is None or (soma_parcial and v_editais is not None):
        v = v_editais
        origem, rotulo = "editais", "reservadas"

    # 3. Calculadas do percentual sobre o total (não há análise por categoria):
    #        vagas = arred(percentual × base)
    #    Ex.: categorias somando 98 vagas e 20% declarados -> arred(0,20 × 98) = 20 vagas.
    if v is None and p is not None and B:
        v = arredonda_in5(p * B)
        origem, rotulo = "percentual", f"calculadas ({p:g} × {B:g})"

    if v is None:
        origem = None

    def resultado(status, motivo):
        return {"status": status, "motivo": motivo, "vagas": v, "vagas_min": v_min, "origem": origem}

    # G0. Mínimo de vagas igual a 0 -> conforme
    #     A base é pequena demais para exigir cota: arred(m × B) = 0, ou seja, B <= 2 para
    #     pessoas negras (0,20 × 2 = 0,4) e B <= 4 para indígenas (0,10 × 4 = 0,4).
    #     Ex.: Natal 2023-07 e 2023-22 (1 e 2 vagas, sem cota) -> conforme.
    if v_min == 0:
        return resultado(STATUS_CONFORME, f"G0: mínimo de vagas 0 (base {B:g}), cota não exigível")

    # G1. Dados inválidos -> indeterminado
    #     vagas reservadas negativas, fracionárias ou acima da base; percentual fora de [0, 1]
    if v is not None and (v < 0 or v % 1 != 0 or (B and v > B)):
        detalhe = f"{v:g} de {B:g}" if B else f"{v:g}"
        return resultado(STATUS_INDETERMINADO, f"G1: vagas reservadas inválidas ({detalhe})")
    if p is not None and not (0 <= p <= 1):
        return resultado(STATUS_INDETERMINADO, f"G1: percentual inválido ({p:g})")

    # G2 e G3. Vagas (de qualquer origem) e base conhecidas: o número de vagas decide
    if v is not None and v_min is not None:
        if v < v_min:
            # G2. abaixo do mínimo -> nao_conforme (mesmo que declare 20%/10%)
            return resultado(STATUS_NAO_CONFORME, f"G2: {v:g} vagas {rotulo} < mínimo {v_min}")
        # G3. atinge o mínimo -> conforme
        return resultado(STATUS_CONFORME, f"G3: {v:g} vagas {rotulo} >= mínimo {v_min}")

    # G4 e G5. Percentual declarado, sem base para calcular vagas
    if p is not None:
        if p + settings.COTA_TOL < m:
            # G4. percentual abaixo do mínimo -> nao_conforme
            return resultado(STATUS_NAO_CONFORME, f"G4: percentual {p:g} < {m:g}")
        # G5. percentual atinge o mínimo -> conforme
        return resultado(STATUS_CONFORME, f"G5: percentual {p:g}")

    # G6. Vagas reservadas, sem base e sem percentual -> indeterminado
    if v is not None:
        return resultado(STATUS_INDETERMINADO, f"G6: {v:g} vagas {rotulo}, total de vagas e percentual desconhecidos")

    # G7. Nem percentual nem vagas reservadas -> nao_conforme
    return resultado(STATUS_NAO_CONFORME, "G7: nenhuma cota identificada")


def avalia_edital(r: pd.Series) -> dict:
    """Status do edital: regra E e, se não se aplicar, combinação dos grupos.

    - E: edital específico para negros ou indígenas -> conforme (edital inteiro);
    - algum grupo nao_conforme -> nao_conforme;
    - senão, algum grupo indeterminado -> indeterminado;
    - senão (os dois conformes) -> conforme.

    Retorna um dict com `conformidade_in5`, `motivo_conformidade` (só os grupos que não ficaram
    conformes) e, por grupo, `vagas_cotas_{g}_in5`, `vagas_min_{g}_in5` e `origem_vagas_{g}_in5`.
    """
    resultados = {g: avalia_grupo(r, g) for g in settings.COTA_MIN}
    linha = {}
    for g, res in resultados.items():
        linha[f"vagas_cotas_{g}_in5"] = res["vagas"]
        linha[f"vagas_min_{g}_in5"] = res["vagas_min"]
        linha[f"origem_vagas_{g}_in5"] = res["origem"]

    especifico = edital_especifico(r)
    if especifico:
        return linha | {"conformidade_in5": STATUS_CONFORME,
                        "motivo_conformidade": f"E: edital específico ({especifico})"}

    status = [res["status"] for res in resultados.values()]
    if STATUS_NAO_CONFORME in status:
        geral = STATUS_NAO_CONFORME
    elif STATUS_INDETERMINADO in status:
        geral = STATUS_INDETERMINADO
    else:
        geral = STATUS_CONFORME
    motivo = " | ".join(f"{g}: {res['motivo']}" for g, res in resultados.items() if res["status"] != STATUS_CONFORME)
    return linha | {"conformidade_in5": geral, "motivo_conformidade": motivo}


def aplica_conformidade(df: pd.DataFrame, categorias: pd.DataFrame | None = None) -> pd.DataFrame:
    """Devolve uma cópia de `df` (aba editais) com as colunas de conformidade.

    `categorias` é a aba `categorias` (uma linha por categoria, com `id`). Se for passada,
    as vagas explícitas por categoria são somadas por edital e usadas como origem prioritária
    das vagas reservadas e da base. Sem ela, valem só as colunas da aba editais.

    Colunas criadas: conformidade_in5, motivo_conformidade e, para g em {negras, indigenas},
    vagas_cotas_{g}_in5, vagas_min_{g}_in5, origem_vagas_{g}_in5; com `categorias`, também
    vagas_categorias_total e vagas_categorias_{g}; e ajuste_manual_in5 (edital com ajuste pontual).
    """
    # !!! Ajustes manuais pontuais na aba editais (decisão de negócio). Não é regra geral.
    #     Ver settings.COTA_AJUSTES_MANUAIS_EDITAIS.
    out, ajustados = aplica_ajustes_manuais_editais(df)
    out["ajuste_manual_in5"] = ajustados
    if categorias is not None:
        # !!! Ajustes manuais pontuais (decisão de negócio), aplicados antes da agregação.
        #     Ver settings.COTA_AJUSTES_MANUAIS_CATEGORIAS. Não é regra geral.
        categorias, ids_ajustados = aplica_ajustes_manuais(categorias)
        out["ajuste_manual_in5"] |= out["id"].isin(ids_ajustados)
        out = out.join(agrega_categorias(categorias), on="id")

        # !!! Ajuste manual pontual (decisão de negócio): editais em que a aba categorias é
        #     ignorada. Os agregados ficam vazios, e a base e as vagas vêm da aba editais.
        #     Ver settings.COTA_AJUSTES_MANUAIS_IGNORA_CATEGORIAS. Não é regra geral.
        for aj in settings.COTA_AJUSTES_MANUAIS_IGNORA_CATEGORIAS:
            alvo = _alvo_edital(out, aj)
            cols_cat = [c for c in out.columns if c.startswith(("vagas_categorias_", "categorias_sem_"))]
            out.loc[alvo, cols_cat] = None
            out.loc[alvo, "ajuste_manual_in5"] = True
    novas = pd.DataFrame(list(out.apply(avalia_edital, axis=1)), index=out.index)
    out[novas.columns] = novas

    # !!! Ajuste manual pontual (decisão de negócio): resultado final definido à mão, por cima
    #     das regras. Ver settings.COTA_AJUSTES_MANUAIS_STATUS. Não é regra geral.
    for aj in settings.COTA_AJUSTES_MANUAIS_STATUS:
        alvo = _alvo_edital(out, aj)
        out.loc[alvo, "conformidade_in5"] = aj["status"]
        out.loc[alvo, "motivo_conformidade"] = f"AJUSTE MANUAL: {aj['justificativa']}"
        out.loc[alvo, "ajuste_manual_in5"] = True
    return out
