"""Junta os JSON extraídos, aplica as regras da IN 5 e gera a planilha final."""
import json
import re
from pathlib import Path

import pandas as pd

from config import settings
from dicionario_cotas import TERMOS_GRUPO, mencoes_reserva, menciona
from transform.conformidade import GRUPOS, avalia_edital
from transform.sanitize import normalizar_texto

_ILEGAIS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
GRUPOS_OUTRAS_COTAS = ("pcd", "lgbtqia", "quilombolas")  # viram colunas próprias na aba 'editais'


def cod_ibge(ente: str, tipo_ente: str):
    nome = normalizar_texto(ente)
    if tipo_ente == "CAPITAL":
        if nome in ("SAO PAULO", "RIO DE JANEIRO"):
            nome = f"{nome} (CAPITAL)"
        return settings.MAP_CAPITAIS_IBGE.get(nome)
    return settings.MAP_ESTADOS_IBGE.get(nome) or ("53" if nome == "DISTRITO FEDERAL" else None)


def _carrega_json(manifesto: pd.DataFrame) -> list[dict]:
    pasta = settings.LPG_LLM_RAW / settings.PROMPT_VERSION
    registros = []
    for _, row in manifesto.iterrows():
        p = pasta / f"{row['id']}.json"
        raw = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"status": "nao_extraido", "dados": None}
        registros.append({"meta": row.to_dict(), "raw": raw})
    return registros


def alertas_revisao(meta: dict, d: dict, linha: dict) -> dict:
    """Marca para revisão quando o dicionário acha o grupo perto de 'cota/reserva' no texto,
    mas o LLM não registrou cota nem pontuação bônus para ele. Só para editais lidos como texto."""
    if meta.get("modo") != "texto":
        return {}
    texto = Path(meta["entrada_path"]).read_text(encoding="utf-8")
    bonus = " ".join(d["pontuacao_bonus"])
    out, revisar = {}, []
    for g in TERMOS_GRUPO:
        trechos = mencoes_reserva(texto, g)
        if g in ("negras", "indigenas"):
            achou_llm = linha.get(f"vagas_cotas_{g}") is not None or linha.get(f"perc_cotas_{g}") is not None
        else:
            achou_llm = any(o["grupo_padrao"] == g for o in d["outras_cotas"])
        no_bonus = menciona(bonus, g)
        if trechos and not achou_llm and not no_bonus:
            revisar.append(g)
            out[f"trecho_regex_{g}"] = trechos[0]
    out["revisar_grupos"] = ", ".join(revisar)
    return out


def consolidar(manifesto: pd.DataFrame) -> dict[str, pd.DataFrame]:
    editais, categorias, outras, evid = [], [], [], []
    for reg in _carrega_json(manifesto):
        m, raw, d = reg["meta"], reg["raw"], reg["raw"].get("dados")
        base = {
            "id": m["id"], "tipo_ente": m["tipo_ente"], "ente": m["ente"],
            "cod_ibge": cod_ibge(m["ente"], m["tipo_ente"]), "arquivo_pdf": m["arquivo"],
            "modo_leitura": m["modo"], "paginas": m.get("paginas"), "status_extracao": raw["status"],
        }
        if not d:
            editais.append(base | {"erro_extracao": raw.get("erro", "")})
            continue

        linha = base | {k: d[k] for k in (
            "tipo_documento", "objeto", "modalidade", "area_cultural", "valor_total", "vagas_totais",
            "possui_categorias", "cotas_por_categoria", "edital_especifico_grupo", "observacoes",
        )}
        linha["n_categorias"] = len(d["categorias"])
        linha["outras_cotas"] = "; ".join(
            f"{o['grupo']}" + (f" ({o['percentual']:g})" if o["percentual"] is not None else "")
            for o in d["outras_cotas"]
        )
        for g in GRUPOS_OUTRAS_COTAS:
            cotas_g = [o for o in d["outras_cotas"] if o["grupo_padrao"] == g]
            linha[f"tem_cota_{g}"] = bool(cotas_g)
            linha[f"perc_cotas_{g}"] = next((o["percentual"] for o in cotas_g if o["percentual"] is not None), None)
            linha[f"vagas_cotas_{g}"] = next((o["vagas"] for o in cotas_g if o["vagas"] is not None), None)
        linha["pontuacao_bonus"] = "; ".join(d["pontuacao_bonus"])
        linha["outros_editais_no_pdf"] = "; ".join(d.get("outros_editais_no_documento") or [])
        linha |= avalia_edital(d)

        if linha.get("valor_total") and linha.get("vagas_totais"):
            linha["valor_por_vaga"] = linha["valor_total"] / linha["vagas_totais"]
            for g in GRUPOS:
                if linha.get(f"vagas_cotas_{g}") is not None:
                    linha[f"valor_cotas_{g}"] = linha[f"vagas_cotas_{g}"] * linha["valor_por_vaga"]
        linha |= alertas_revisao(m, d, linha)
        editais.append(linha)

        ids = {"id": m["id"], "tipo_ente": m["tipo_ente"], "ente": m["ente"], "arquivo_pdf": m["arquivo"]}
        categorias += [ids | c for c in d["categorias"]]
        outras += [ids | o for o in d["outras_cotas"]]
        evid += [ids | e for e in d["evidencias"]]

    return {
        "editais": pd.DataFrame(editais),
        "categorias": pd.DataFrame(categorias),
        "outras_cotas": pd.DataFrame(outras),
        "evidencias": pd.DataFrame(evid),
    }


def salva_excel(tabelas: dict[str, pd.DataFrame]) -> None:
    settings.LPG_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(settings.LPG_OUTPUT, engine="openpyxl") as xw:
        for nome, df in tabelas.items():
            df.map(lambda v: _ILEGAIS.sub("", v) if isinstance(v, str) else v).to_excel(xw, sheet_name=nome, index=False)
    e = tabelas["editais"]
    print(f"📄 {settings.LPG_OUTPUT}")
    print(e["status_extracao"].value_counts().to_string())
    if "status_in5" in e:
        print(e["status_in5"].value_counts(dropna=False).to_string())
