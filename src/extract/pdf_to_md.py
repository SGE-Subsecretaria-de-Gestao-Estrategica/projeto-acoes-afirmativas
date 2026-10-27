# pdf_to_md.py
"""Converte os editais da LPG para Markdown (PyMuPDF) e monta o manifesto.

PDFs com texto viram Markdown com marcadores <!-- página N -->.
PDFs escaneados (sem camada de texto) são recomprimidos como JPEG para
serem enviados ao modelo como documento PDF.
"""
from pathlib import Path
import hashlib
import re
import unicodedata

import pandas as pd
import pymupdf
import pymupdf4llm

from config import settings

pymupdf4llm.use_layout(False)  # o modo layout é ~8x mais lento e não melhora as tabelas aqui


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _id(rel: str) -> str:
    return hashlib.sha1(rel.encode("utf-8")).hexdigest()[:16]


def _slug(nome: str) -> str:
    return re.sub(r"[^A-Z]", "", unicodedata.normalize("NFD", nome).encode("ascii", "ignore").decode().upper())


def lista_novos(base: pd.DataFrame, novos_root: Path = settings.LPG_NOVOS_ROOT) -> pd.DataFrame:
    """PDFs avulsos em data/NOVOS/<qualquer pasta>/*.pdf. O ente sai do nome do arquivo
    (ex.: 2023-02_EST-BAHIA_LPG.pdf) e é casado com as pastas de entes da base."""
    if not novos_root.exists():
        return pd.DataFrame()
    entes = {(t, _slug(e)): e for t, e in base[["tipo_ente", "ente"]].drop_duplicates().itertuples(index=False)}
    for tipo_dir in settings.LPG_PDF_ROOT.iterdir():  # inclui entes com pasta vazia (ex.: Roraima)
        if tipo_dir.is_dir():
            t = "CAPITAL" if tipo_dir.name.lower().startswith("capita") else "ESTADO"
            entes |= {(t, _slug(d.name)): _nfc(d.name) for d in tipo_dir.iterdir() if d.is_dir()}
    linhas = []
    for pdf in sorted(novos_root.rglob("*")):
        if not (pdf.is_file() and pdf.suffix.lower() == ".pdf"):
            continue
        m = re.search(r"_(EST|CAP)-([A-Za-z]+)_", pdf.name)
        if not m:
            raise ValueError(f"Não consegui identificar o ente pelo nome do arquivo: {pdf}")
        tipo = "ESTADO" if m.group(1) == "EST" else "CAPITAL"
        ente = entes.get((tipo, _slug(m.group(2))))
        if ente is None:
            raise ValueError(f"Ente '{m.group(2)}' ({tipo}) não encontrado nas pastas da base: {pdf}")
        rel = "NOVOS/" + _nfc(pdf.relative_to(novos_root).as_posix())
        linhas.append({"id": _id(rel), "tipo_ente": tipo, "ente": ente, "arquivo": _nfc(pdf.name),
                       "pdf_path": str(pdf), "origem": "novos"})
    return pd.DataFrame(linhas)


def lista_editais(pdf_root: Path = settings.LPG_PDF_ROOT) -> pd.DataFrame:
    """PDFs da raiz de cada ente (<pdf_root>/<Capitais|Estados>/<ente>/*.pdf) + os de data/NOVOS."""
    linhas = []
    for tipo_dir in sorted(pdf_root.iterdir()):
        if not tipo_dir.is_dir():
            continue
        tipo_ente = "CAPITAL" if tipo_dir.name.lower().startswith("capita") else "ESTADO"
        for ente_dir in sorted(tipo_dir.iterdir()):
            if not ente_dir.is_dir():
                continue
            for pdf in sorted(ente_dir.iterdir()):  # sem rglob: ignora 'outros editais' e 'PlanilhasPC'
                if pdf.is_file() and pdf.suffix.lower() == ".pdf":
                    rel = _nfc(pdf.relative_to(pdf_root).as_posix())
                    linhas.append({
                        "id": _id(rel),
                        "tipo_ente": tipo_ente,
                        "ente": _nfc(ente_dir.name),
                        "arquivo": _nfc(pdf.name),
                        "pdf_path": str(pdf),
                        "origem": "base",
                    })
    base = pd.DataFrame(linhas)
    return pd.concat([base, lista_novos(base)], ignore_index=True)


def eh_escaneado(doc: pymupdf.Document) -> bool:
    chars = sum(len(pg.get_text()) for pg in doc)
    return chars / max(doc.page_count, 1) < settings.MIN_CHARS_POR_PAGINA


def pdf_para_markdown(pdf_path: str) -> str:
    paginas = pymupdf4llm.to_markdown(pdf_path, page_chunks=True, show_progress=False)
    return "\n\n".join(
        f"<!-- página {i} -->\n{p['text'].strip()}" for i, p in enumerate(paginas, start=1)
    )


def comprime_escaneado(pdf_path: str, destino: Path, dpi: int = 110, qualidade: int = 70) -> Path:
    """Re-renderiza cada página como JPEG e monta um PDF leve (limite da API: 32 MB por requisição)."""
    src = pymupdf.open(pdf_path)
    out = pymupdf.open()
    for pg in src:
        pix = pg.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
        nova = out.new_page(width=pg.rect.width, height=pg.rect.height)
        nova.insert_image(nova.rect, stream=pix.tobytes("jpeg", jpg_quality=qualidade))
    destino.parent.mkdir(parents=True, exist_ok=True)
    out.save(destino, garbage=4, deflate=True)
    return destino


def converter_editais(refazer: bool = False) -> pd.DataFrame:
    """Converte todos os editais e grava o manifesto. Retoma de onde parou."""
    df = lista_editais()
    anterior = (
        pd.read_csv(settings.LPG_MANIFESTO, sep=";", dtype=str).set_index("id")
        if settings.LPG_MANIFESTO.exists() and not refazer else pd.DataFrame()
    )
    print(f"Encontrados {len(df)} PDFs")

    linhas = []
    for _, row in df.iterrows():
        if row["id"] in anterior.index and anterior.loc[row["id"], "status"] == "ok":
            ja = anterior.loc[row["id"]].to_dict()
            linhas.append(row.to_dict() | {k: v for k, v in ja.items() if k not in row.index})
            continue

        reg = row.to_dict()
        try:
            doc = pymupdf.open(row["pdf_path"])
            reg["paginas"] = doc.page_count
            if eh_escaneado(doc):
                destino = settings.LPG_PDF_COMPRIMIDO / f"{row['id']}.pdf"
                comprime_escaneado(row["pdf_path"], destino)
                reg |= {"modo": "pdf", "entrada_path": str(destino)}
            else:
                destino = settings.LPG_MD_ROOT / f"{row['id']}.md"
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_text(pdf_para_markdown(row["pdf_path"]), encoding="utf-8")
                reg |= {"modo": "texto", "entrada_path": str(destino)}
            reg |= {"status": "ok", "mensagem": ""}
            print(f"✅ {row['ente']}/{row['arquivo']} ({reg['modo']})")
        except Exception as e:
            reg |= {"status": "erro", "mensagem": str(e)}
            print(f"❌ {row['ente']}/{row['arquivo']}: {e}")
        linhas.append(reg)

    manifesto = pd.DataFrame(linhas)
    settings.LPG_MANIFESTO.parent.mkdir(parents=True, exist_ok=True)
    manifesto.to_csv(settings.LPG_MANIFESTO, sep=";", index=False)
    print(f"\n📊 Manifesto: {settings.LPG_MANIFESTO}")
    return manifesto
