"""Controle de gasto: o pipeline nunca envia uma etapa cujo pior caso estoure o orçamento."""
from datetime import datetime
import csv

import pandas as pd

from config import settings


class OrcamentoExcedido(RuntimeError):
    pass


def _precos(modelo: str = settings.MODEL_ID) -> dict:
    return settings.PRECOS_USD_POR_MTOK[modelo]


def custo_usage(usage, batch: bool, modelo: str = settings.MODEL_ID) -> float:
    """Custo em US$ de uma resposta a partir de `message.usage`."""
    p = _precos(modelo)
    entrada = (
        (usage.input_tokens or 0)
        + (getattr(usage, "cache_creation_input_tokens", 0) or 0) * settings.MULT_CACHE["escrita"]
        + (getattr(usage, "cache_read_input_tokens", 0) or 0) * settings.MULT_CACHE["leitura"]
    )
    usd = (entrada * p["input"] + (usage.output_tokens or 0) * p["output"]) / 1e6
    return usd * (settings.DESCONTO_BATCH if batch else 1.0)


def pior_caso(tokens_entrada: list[int], batch: bool, modelo: str = settings.MODEL_ID) -> float:
    """Custo máximo possível: entrada medida (com folga p/ escrita de cache) + max_tokens de saída por edital."""
    p = _precos(modelo)
    entrada = sum(tokens_entrada) * settings.MULT_CACHE["escrita"]
    saida = len(tokens_entrada) * settings.MAX_TOKENS
    usd = (entrada * p["input"] + saida * p["output"]) / 1e6
    return usd * (settings.DESCONTO_BATCH if batch else 1.0)


def gasto_acumulado() -> float:
    if not settings.LPG_GASTOS.exists():
        return 0.0
    return float(pd.read_csv(settings.LPG_GASTOS, sep=";")["usd"].sum())


def reservado_em_batches_abertos() -> float:
    """Pior caso dos batches enviados e ainda não coletados (o gasto deles ainda não está em gastos.csv)."""
    if not settings.LPG_BATCHES.exists():
        return 0.0
    df = pd.read_csv(settings.LPG_BATCHES, sep=";")
    return float(df.loc[df["coletado"] == 0, "pior_caso_usd"].sum())


def garante_orcamento(custo_max_etapa: float, etapa: str) -> None:
    gasto = gasto_acumulado()
    reservado = reservado_em_batches_abertos()
    total = gasto + reservado + custo_max_etapa
    print(
        f"💰 {etapa}: gasto até agora US$ {gasto:.2f} | reservado em batches abertos US$ {reservado:.2f} | "
        f"pior caso desta etapa US$ {custo_max_etapa:.2f} | total US$ {total:.2f} de US$ {settings.ORCAMENTO_USD:.2f}"
    )
    if total > settings.ORCAMENTO_USD:
        raise OrcamentoExcedido(
            f"Etapa '{etapa}' cancelada: o pior caso levaria o gasto a US$ {total:.2f}, "
            f"acima do teto de US$ {settings.ORCAMENTO_USD:.2f}. Nada foi enviado."
        )


def registra_gasto(edital_id: str, etapa: str, usage, batch: bool) -> float:
    usd = custo_usage(usage, batch)
    novo = not settings.LPG_GASTOS.exists()
    settings.LPG_GASTOS.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.LPG_GASTOS, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if novo:
            w.writerow(["quando", "etapa", "id", "input", "cache_escrita", "cache_leitura", "output", "batch", "usd"])
        w.writerow([
            datetime.now().isoformat(timespec="seconds"), etapa, edital_id,
            usage.input_tokens, getattr(usage, "cache_creation_input_tokens", 0) or 0,
            getattr(usage, "cache_read_input_tokens", 0) or 0, usage.output_tokens, int(batch), round(usd, 6),
        ])
    return usd
