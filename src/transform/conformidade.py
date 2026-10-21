"""Verificação das cotas da IN MinC nº 5/2023, art. 5º, a partir do JSON extraído.

- caput: >= 20% das vagas p/ pessoas negras e >= 10% p/ pessoas indígenas;
- §2º: fração >= 0,5 arredonda para cima, < 0,5 para baixo;
- §3º: editais com categorias devem ter cotas em todas elas;
- §4º: categoria com 1 vaga pode ir à ampla concorrência, se o edital somar 20% / 10%.
"""
import math

from config import settings

GRUPOS = {
    "negras": ("percentual_negras", "vagas_negras", "vagas_negras_total", ("negr", "pret", "pard", "afro")),
    "indigenas": ("percentual_indigenas", "vagas_indigenas", "vagas_indigenas_total", ("indígen", "indigen")),
}
TOL = 1e-9


def arredonda_in5(x: float) -> int:
    """Arredondamento do §2º (meio para cima). np.round arredondaria 2,5 para 2."""
    return math.floor(x + 0.5 + TOL)


def _fracao(p):
    if p is None:
        return None
    return p / 100 if p > 1 else p  # tolera "20" no lugar de 0.2


def _especifico_do_grupo(dados: dict, grupo: str) -> bool:
    alvo = (dados.get("edital_especifico_grupo") or "").lower()
    return any(t in alvo for t in GRUPOS[grupo][3])


def avalia_grupo(dados: dict, grupo: str) -> dict:
    """Retorna status, motivo e vagas reservadas (informadas ou calculadas) para um grupo."""
    col_perc, col_cat, col_total, _ = GRUPOS[grupo]
    minimo = settings.COTA_MIN[grupo]
    perc = _fracao(dados.get(col_perc))
    vagas_totais = dados.get("vagas_totais")
    cats = [c for c in dados.get("categorias") or [] if c.get("vagas")]
    out = {"perc": perc, "vagas_calc": None, "esperado": None}

    if dados.get("edital_especifico_grupo"):
        out["vagas_calc"] = vagas_totais if _especifico_do_grupo(dados, grupo) else 0
        return out | {"status": "especifico", "motivo": f"edital específico: {dados['edital_especifico_grupo']}"}

    total_cat = sum(c["vagas"] for c in cats)
    base = vagas_totais or total_cat or None
    out["esperado"] = arredonda_in5(minimo * base) if base else None

    # 1) reservas informadas por categoria
    if cats and any(c.get(col_cat) is not None for c in cats):
        falhas, sem_info = [], []
        for c in cats:
            res = c.get(col_cat)
            if c["vagas"] == 1:          # §4º: avaliada só no agregado
                continue
            if res is None:
                sem_info.append(c["nome"])
            elif res < arredonda_in5(minimo * c["vagas"]):
                falhas.append(f"{c['nome']} ({res}/{c['vagas']})")
        reservado = sum(c.get(col_cat) or 0 for c in cats)
        out["vagas_calc"] = reservado
        if falhas:
            return out | {"status": "nao_conforme", "motivo": "abaixo do mínimo em: " + "; ".join(falhas)}
        if reservado < arredonda_in5(minimo * total_cat):
            return out | {"status": "nao_conforme", "motivo": f"total reservado {reservado} < {arredonda_in5(minimo * total_cat)} (§4º)"}
        if sem_info:
            return out | {"status": "indeterminado", "motivo": "sem reserva informada em: " + "; ".join(sem_info)}
        return out | {"status": "conforme", "motivo": "reservas por categoria atendem o mínimo"}

    # 2) só percentual
    if perc is not None:
        if cats:
            out["vagas_calc"] = sum(arredonda_in5(perc * c["vagas"]) for c in cats)
        elif base:
            out["vagas_calc"] = arredonda_in5(perc * base)
        if perc + TOL < minimo:
            return out | {"status": "nao_conforme", "motivo": f"percentual {perc:g} < mínimo {minimo:g}"}
        if dados.get("possui_categorias") and dados.get("cotas_por_categoria") == "nao":
            return out | {"status": "nao_conforme", "motivo": "cotas não aplicadas em cada categoria (§3º)"}
        if dados.get("possui_categorias") and dados.get("cotas_por_categoria") == "nao_informado":
            return out | {"status": "conforme", "motivo": "percentual ok; aplicação por categoria não explicitada (ressalva §3º)"}
        return out | {"status": "conforme", "motivo": f"percentual {perc:g}"}

    # 3) só número total de vagas reservadas
    total_res = dados.get(col_total)
    if total_res is not None:
        out["vagas_calc"] = total_res
        if out["esperado"] is None:
            return out | {"status": "indeterminado", "motivo": f"{total_res} vagas reservadas, total de vagas desconhecido"}
        ok = total_res >= out["esperado"]
        return out | {
            "status": "conforme" if ok else "nao_conforme",
            "motivo": f"{total_res} vagas reservadas de {base} (mínimo {out['esperado']})",
        }

    return out | {"status": "nao_conforme", "motivo": "nenhuma cota identificada para o grupo"}


def avalia_edital(dados: dict) -> dict:
    if dados.get("tipo_documento") != "edital":
        return {"status_in5": "nao_aplicavel", "motivo_in5": f"documento do tipo {dados.get('tipo_documento')}"}

    linha, statuses = {}, []
    for g in GRUPOS:
        r = avalia_grupo(dados, g)
        statuses.append(r["status"])
        linha |= {
            f"perc_cotas_{g}": r["perc"], f"vagas_cotas_{g}": r["vagas_calc"],
            f"vagas_min_{g}": r["esperado"], f"status_{g}": r["status"], f"motivo_{g}": r["motivo"],
        }

    if "especifico" in statuses:
        geral = "especifico"
    elif "nao_conforme" in statuses:
        geral = "nao_conforme"
    elif "indeterminado" in statuses:
        geral = "indeterminado"
    else:
        geral = "conforme"
    motivos = list(dict.fromkeys(linha[f"motivo_{g}"] for g in GRUPOS if linha[f"status_{g}"] != "conforme"))
    return linha | {"status_in5": geral, "motivo_in5": " | ".join(motivos)}
