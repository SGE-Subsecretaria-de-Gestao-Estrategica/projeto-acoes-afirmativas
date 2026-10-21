"""Pipeline LPG: verificação de cotas da IN MinC nº 5/2023 nos editais de estados e capitais.

Etapas (rodar a partir da pasta src/):
    python main.py converter            # PDF -> Markdown / PDF comprimido + manifesto (local, sem custo)
    python main.py contar               # conta tokens exatos de cada edital (gratuito) e estima o custo
    python main.py piloto 10            # extração síncrona de N editais variados (preço cheio)
    python main.py amostra 77           # sorteia a amostra do gabarito, estratificada por ente
    python main.py batch [amostra]      # envia o batch (todos os pendentes, ou só a amostra)
    python main.py coletar              # coleta os batches terminados (pode repetir)
    python main.py consolidar           # aplica as regras da IN e gera data/final/lpg_editais.xlsx
    python main.py gasto                # mostra o gasto acumulado
    python main.py painel               # abre o painel de conformidade em http://127.0.0.1:8050
    python main.py relatorio            # gera relatorios/relatorio_exploratorio_lpg.html
    python main.py revisao              # gera a planilha do gabarito manual (amostra)
    python main.py f1                   # calcula o F1 a partir da planilha revisada

Todas as etapas que chamam a API passam pela trava de orçamento (settings.ORCAMENTO_USD).
"""
import sys

import pandas as pd

import avaliacao
from config import settings
from extract.pdf_to_md import converter_editais
from llm import budget, extractor
from transform.consolida_lpg import consolidar, salva_excel

AMOSTRA = settings.LPG_INTERIM / "amostra_gabarito.csv"


def escolhe_piloto(n: int) -> list[str]:
    """Editais variados: escaneados, os maiores, os menores e o resto espalhado entre entes."""
    df = extractor.carrega_manifesto().sort_values("tokens_entrada")
    escolhidos = list(df[df["modo"] == "pdf"].drop_duplicates("ente").head(2)["id"])
    texto = df[df["modo"] == "texto"]
    escolhidos += list(texto.tail(2)["id"]) + list(texto.head(1)["id"])
    resto = texto[~texto["id"].isin(escolhidos)].drop_duplicates("ente").sample(frac=1, random_state=42)
    escolhidos += list(resto["id"])
    return escolhidos[:n]


def sorteia_amostra(n: int) -> None:
    df = extractor.carrega_manifesto()
    frac = n / len(df)
    amostra = pd.concat(
        g.sample(max(1, round(len(g) * frac)), random_state=42) for _, g in df.groupby("ente")
    )
    amostra = amostra.sample(min(n, len(amostra)), random_state=42)
    amostra[["id", "tipo_ente", "ente", "arquivo", "pdf_path"]].to_csv(AMOSTRA, sep=";", index=False)
    print(f"Amostra de {len(amostra)} editais em {AMOSTRA}")


def main(args: list[str]) -> None:
    etapa = args[0] if args else ""
    if etapa == "converter":
        converter_editais()
    elif etapa == "contar":
        extractor.resumo_custo(extractor.conta_tokens())
    elif etapa == "piloto":
        extractor.extrai_sincrono(escolhe_piloto(int(args[1]) if len(args) > 1 else 10))
    elif etapa == "amostra":
        sorteia_amostra(int(args[1]) if len(args) > 1 else 77)
    elif etapa == "batch":
        ids = list(pd.read_csv(AMOSTRA, sep=";", dtype=str)["id"]) if args[1:] == ["amostra"] else None
        extractor.envia_batch(ids, etapa="gabarito" if ids else "batch")
    elif etapa == "coletar":
        extractor.coleta_batches()
    elif etapa == "consolidar":
        salva_excel(consolidar(extractor.carrega_manifesto()))
    elif etapa == "gasto":
        print(f"Gasto acumulado: US$ {budget.gasto_acumulado():.2f} de US$ {settings.ORCAMENTO_USD:.2f} "
              f"(reservado em batches abertos: US$ {budget.reservado_em_batches_abertos():.2f})")
    elif etapa == "revisao":
        avaliacao.gera_planilha_revisao()
    elif etapa == "f1":
        avaliacao.calcula_f1()
    elif etapa == "relatorio":
        from relatorio_exploratorio import gera
        print(f"Relatório gerado em {gera()}")
    elif etapa == "painel":
        from dashboard.app import app
        app.run(debug=False)
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
