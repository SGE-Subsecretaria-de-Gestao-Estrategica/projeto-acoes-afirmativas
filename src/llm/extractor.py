"""Extração com Claude: contagem de tokens, piloto síncrono e Message Batches API."""
from datetime import datetime
from pathlib import Path
import base64
import csv
import json
import os

import anthropic
import pandas as pd
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from dotenv import load_dotenv
from pydantic import ValidationError

from config import settings
from llm import budget
from llm.prompt import SYSTEM_PROMPT, mensagem_usuario
from llm.schema import Edital

load_dotenv(settings.ROOT / ".env")
load_dotenv(settings.ROOT / "src" / ".env")
_client = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        # Chaves de usuário (sk-ant-usr-...) não são ligadas a um workspace: exigem o ID dele no header
        workspace = os.getenv("ANTHROPIC_WORKSPACE_ID")
        headers = {"anthropic-workspace-id": workspace} if workspace else None
        _client = anthropic.Anthropic(max_retries=5, default_headers=headers)
    return _client


# ---------------------------------------------------------------- requisição
def _conteudo(row: pd.Series) -> list[dict]:
    if row["modo"] == "pdf":
        dados = base64.standard_b64encode(Path(row["entrada_path"]).read_bytes()).decode("utf-8")
        edital = {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": dados}}
    else:
        edital = {"type": "text", "text": Path(row["entrada_path"]).read_text(encoding="utf-8")}
    return [edital, {"type": "text", "text": mensagem_usuario(row["ente"], row["arquivo"])}]


def _sem_entrada(row: pd.Series) -> dict:
    """Parâmetros comuns, sem max_tokens (count_tokens não aceita)."""
    return {
        "model": settings.MODEL_ID,
        "system": [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": _conteudo(row)}],
        "output_config": {
            "effort": settings.EFFORT,
            "format": {"type": "json_schema", "schema": Edital.model_json_schema()},
        },
    }


def params(row: pd.Series) -> dict:
    return _sem_entrada(row) | {"max_tokens": settings.MAX_TOKENS}


# ---------------------------------------------------------------- manifesto
def carrega_manifesto() -> pd.DataFrame:
    if not settings.LPG_MANIFESTO.exists():
        raise FileNotFoundError("Rode a etapa 'converter' primeiro.")
    df = pd.read_csv(settings.LPG_MANIFESTO, sep=";", dtype={"id": str})
    return df[df["status"] == "ok"].reset_index(drop=True)


def conta_tokens(refazer: bool = False) -> pd.DataFrame:
    """Conta os tokens de entrada exatos de cada edital (endpoint gratuito) e grava no manifesto."""
    todos = pd.read_csv(settings.LPG_MANIFESTO, sep=";", dtype={"id": str})
    if "tokens_entrada" not in todos.columns:
        todos["tokens_entrada"] = pd.NA
    pendentes = todos[(todos["status"] == "ok") & (refazer | todos["tokens_entrada"].isna())]
    for i, row in pendentes.iterrows():
        p = _sem_entrada(row)
        todos.loc[i, "tokens_entrada"] = client().messages.count_tokens(**p).input_tokens
        print(f"🔢 {row['ente']}/{row['arquivo']}: {int(todos.loc[i, 'tokens_entrada']):,} tokens")
        todos.to_csv(settings.LPG_MANIFESTO, sep=";", index=False)  # salva a cada edital (retomada)
    return todos


def resumo_custo(manifesto: pd.DataFrame, saida_media: int = 6000) -> None:
    tok = manifesto["tokens_entrada"].dropna().astype(int)
    p = settings.PRECOS_USD_POR_MTOK[settings.MODEL_ID]
    entrada = tok.sum() * p["input"] / 1e6 * settings.DESCONTO_BATCH
    saida = len(tok) * saida_media * p["output"] / 1e6 * settings.DESCONTO_BATCH
    print(
        f"Editais com contagem: {len(tok)} | tokens de entrada: {tok.sum():,} "
        f"(mediana {int(tok.median()):,}, máx {tok.max():,})\n"
        f"Estimativa no Batch: entrada US$ {entrada:.2f} + saída (~{saida_media} tok/edital) US$ {saida:.2f} "
        f"= US$ {entrada + saida:.2f}\n"
        f"Pior caso no Batch: US$ {budget.pior_caso(tok.tolist(), batch=True):.2f}"
    )


# ---------------------------------------------------------------- respostas
def _raw_path(edital_id: str) -> Path:
    return settings.LPG_LLM_RAW / settings.PROMPT_VERSION / f"{edital_id}.json"


def ja_extraido(edital_id: str) -> bool:
    p = _raw_path(edital_id)
    return p.exists() and json.loads(p.read_text(encoding="utf-8"))["status"] == "ok"


def salva_resposta(edital_id: str, message, etapa: str) -> str:
    """Valida a resposta contra o schema e grava o JSON bruto. Retorna o status."""
    dados, erro = None, ""
    if message.stop_reason == "refusal":
        status = "recusa"
        erro = str(getattr(message, "stop_details", "") or "")
    elif message.stop_reason == "max_tokens":
        status = "truncado"
    else:
        texto = next((b.text for b in message.content if b.type == "text"), "")
        try:
            dados = Edital.model_validate_json(texto).model_dump()
            status = "ok"
        except ValidationError as e:
            status, erro = "invalido", str(e)[:2000]

    p = _raw_path(edital_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "id": edital_id, "status": status, "erro": erro, "etapa": etapa,
        "modelo": message.model, "prompt_version": settings.PROMPT_VERSION,
        "stop_reason": message.stop_reason, "quando": datetime.now().isoformat(timespec="seconds"),
        "usage": {"input": message.usage.input_tokens, "output": message.usage.output_tokens},
        "dados": dados,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return status


def _selecao(ids: list[str] | None, refazer: bool) -> pd.DataFrame:
    df = carrega_manifesto()
    if ids is not None:
        df = df[df["id"].isin(ids)]
    if not refazer:
        df = df[~df["id"].apply(ja_extraido)]
    if "tokens_entrada" not in df or df["tokens_entrada"].isna().any():
        raise RuntimeError("Há editais sem contagem de tokens. Rode a etapa 'contar' antes de enviar.")
    return df


# ---------------------------------------------------------------- síncrono (piloto)
def extrai_sincrono(ids: list[str], etapa: str = "piloto", refazer: bool = False) -> None:
    df = _selecao(ids, refazer)
    if df.empty:
        print("Nada a fazer: todos já extraídos.")
        return
    budget.garante_orcamento(budget.pior_caso(df["tokens_entrada"].astype(int).tolist(), batch=False), etapa)
    for _, row in df.iterrows():
        msg = client().messages.create(**params(row))
        usd = budget.registra_gasto(row["id"], etapa, msg.usage, batch=False)
        status = salva_resposta(row["id"], msg, etapa)
        print(f"{'✅' if status == 'ok' else '⚠️'} {row['ente']}/{row['arquivo']}: {status} (US$ {usd:.3f})")


# ---------------------------------------------------------------- batch
def envia_batch(ids: list[str] | None = None, etapa: str = "batch", refazer: bool = False) -> str | None:
    df = _selecao(ids, refazer)
    if df.empty:
        print("Nada a enviar: todos já extraídos.")
        return None
    custo_max = budget.pior_caso(df["tokens_entrada"].astype(int).tolist(), batch=True)
    budget.garante_orcamento(custo_max, etapa)

    requests = [
        Request(custom_id=row["id"], params=MessageCreateParamsNonStreaming(**params(row)))
        for _, row in df.iterrows()
    ]
    lote = client().messages.batches.create(requests=requests)

    novo = not settings.LPG_BATCHES.exists()
    with open(settings.LPG_BATCHES, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if novo:
            w.writerow(["batch_id", "etapa", "quando", "n", "pior_caso_usd", "coletado"])
        w.writerow([lote.id, etapa, datetime.now().isoformat(timespec="seconds"), len(df), round(custo_max, 4), 0])
    print(f"📦 Batch {lote.id} enviado com {len(df)} editais.")
    return lote.id


def coleta_batches() -> None:
    """Coleta todos os batches enviados e ainda não coletados (pode rodar várias vezes)."""
    if not settings.LPG_BATCHES.exists():
        print("Nenhum batch enviado.")
        return
    lotes = pd.read_csv(settings.LPG_BATCHES, sep=";")
    for i, lote in lotes[lotes["coletado"] == 0].iterrows():
        info = client().messages.batches.retrieve(lote["batch_id"])
        if info.processing_status != "ended":
            c = info.request_counts
            print(f"⏳ {lote['batch_id']}: {info.processing_status} (processando {c.processing}, ok {c.succeeded})")
            continue
        contagem: dict[str, int] = {}
        for r in client().messages.batches.results(lote["batch_id"]):
            if r.result.type == "succeeded":
                budget.registra_gasto(r.custom_id, lote["etapa"], r.result.message.usage, batch=True)
                status = salva_resposta(r.custom_id, r.result.message, lote["etapa"])
            else:
                status = r.result.type  # errored / canceled / expired: não cobrados, ficam p/ reenvio
            contagem[status] = contagem.get(status, 0) + 1
        lotes.loc[i, "coletado"] = 1
        lotes.to_csv(settings.LPG_BATCHES, sep=";", index=False)
        print(f"✅ {lote['batch_id']} coletado: {contagem} | gasto total até agora US$ {budget.gasto_acumulado():.2f}")
